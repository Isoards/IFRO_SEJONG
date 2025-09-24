"""
증분 임베딩(Incremental Embedding) 시스템
기존 챗봇 서버를 끄지 않고 새로 업로드된 PDF만 추가로 임베딩합니다.
"""
import argparse
import json
import logging
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set
import warnings

# PyTorch 경고 메시지 숨기기
warnings.filterwarnings("ignore", message=".*TypedStorage is deprecated.*")

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from unifiedpdf.config import PipelineConfig
from unifiedpdf.types import Chunk
from unifiedpdf.embedding import get_embedder

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IncrementalEmbeddingProcessor:
    """증분 임베딩 처리 클래스"""
    
    def __init__(self, 
                 corpus_file: str = "data/corpus_v1.jsonl",
                 vector_store_dir: str = "vector_store",
                 processed_files_log: str = "data/processed_files.json"):
        """
        Args:
            corpus_file: 코퍼스 파일 경로
            vector_store_dir: 벡터 스토어 디렉토리
            processed_files_log: 처리된 파일 목록 로그
        """
        self.corpus_file = Path(corpus_file)
        self.vector_store_dir = Path(vector_store_dir)
        self.processed_files_log = Path(processed_files_log)
        
        # 처리된 파일 목록 로드
        self.processed_files = self._load_processed_files()
        
        # 임베더 초기화
        self.embedder = get_embedder(PipelineConfig().embedding_model, use_gpu=False)
        if self.embedder is None:
            raise RuntimeError("임베더를 초기화할 수 없습니다.")
        
        logger.info(f"증분 임베딩 프로세서 초기화 완료")
        logger.info(f"처리된 파일 수: {len(self.processed_files)}")
    
    def _load_processed_files(self) -> Set[str]:
        """처리된 파일 목록 로드"""
        if not self.processed_files_log.exists():
            return set()
        
        try:
            with open(self.processed_files_log, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get("processed_files", []))
        except Exception as e:
            logger.warning(f"처리된 파일 목록 로드 실패: {str(e)}")
            return set()
    
    def _save_processed_files(self):
        """처리된 파일 목록 저장"""
        try:
            self.processed_files_log.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "processed_files": list(self.processed_files),
                "last_updated": datetime.now().isoformat()
            }
            with open(self.processed_files_log, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"처리된 파일 목록 저장 실패: {str(e)}")
    
    def _get_new_pdf_files(self, pdf_dir: str) -> List[Path]:
        """새로 추가된 PDF 파일 목록 반환"""
        pdf_directory = Path(pdf_dir)
        if not pdf_directory.exists():
            return []
        
        all_pdfs = list(pdf_directory.glob("**/*.pdf"))
        new_pdfs = [pdf for pdf in all_pdfs if str(pdf) not in self.processed_files]
        
        logger.info(f"전체 PDF: {len(all_pdfs)}개, 새 PDF: {len(new_pdfs)}개")
        return new_pdfs
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """PDF에서 텍스트 추출"""
        try:
            from scripts.build_corpus_from_pdfs import extract_text_auto
            return extract_text_auto(pdf_path)
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패 {pdf_path}: {str(e)}")
            return ""
    
    def _chunk_text(self, text: str, filename: str, doc_id: str) -> List[Chunk]:
        """텍스트를 청크로 분할"""
        try:
            from unifiedpdf.pdf_processor import PDFProcessor, PDFChunkConfig
            from unifiedpdf.measurements import extract_measurements
            
            cfg = PDFChunkConfig(
                chunk_size=500,
                chunk_overlap=100,
                enable_wastewater_chunking=True,
                wastewater_chunk_size=900,
                wastewater_overlap_ratio=0.25,
            )
            proc = PDFProcessor(cfg)
            chunks = proc.chunk_text(doc_id=doc_id, filename=filename, text=text)
            
            # 측정값 추출
            for chunk in chunks:
                chunk.extra["measurements"] = extract_measurements(chunk.text)
            
            return chunks
            
        except Exception as e:
            logger.error(f"텍스트 청킹 실패: {str(e)}")
            return []
    
    def _load_existing_corpus(self) -> List[Dict[str, Any]]:
        """기존 코퍼스 로드"""
        if not self.corpus_file.exists():
            return []
        
        corpus = []
        try:
            with open(self.corpus_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        corpus.append(json.loads(line))
        except Exception as e:
            logger.error(f"기존 코퍼스 로드 실패: {str(e)}")
        
        return corpus
    
    def _save_corpus(self, corpus: List[Dict[str, Any]]):
        """코퍼스 저장"""
        try:
            # 백업 생성
            if self.corpus_file.exists():
                backup_file = self.corpus_file.with_suffix(self.corpus_file.suffix + ".bak")
                if backup_file.exists():
                    backup_file.unlink()
                self.corpus_file.rename(backup_file)
            
            # 새 코퍼스 저장
            with open(self.corpus_file, 'w', encoding='utf-8') as f:
                for item in corpus:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
            logger.info(f"코퍼스 저장 완료: {len(corpus)}개 청크")
            
        except Exception as e:
            logger.error(f"코퍼스 저장 실패: {str(e)}")
    
    def _load_existing_vectors(self) -> tuple:
        """기존 벡터 인덱스 로드"""
        try:
            import faiss
            import numpy as np
            
            index_path = self.vector_store_dir / "index.faiss"
            meta_path = self.vector_store_dir / "meta.json"
            mapping_path = self.vector_store_dir / "mapping.json"
            
            if not all([index_path.exists(), meta_path.exists(), mapping_path.exists()]):
                logger.info("기존 벡터 인덱스가 없습니다. 새로 생성합니다.")
                return None, None, None
            
            # 메타데이터 로드
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            # 매핑 로드
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            
            # FAISS 인덱스 로드
            index = faiss.read_index(str(index_path))
            
            logger.info(f"기존 벡터 인덱스 로드 완료: {index.ntotal}개 벡터")
            return index, meta, mapping
            
        except Exception as e:
            logger.error(f"기존 벡터 인덱스 로드 실패: {str(e)}")
            return None, None, None
    
    def _save_updated_vectors(self, index, meta: Dict, mapping: List[int]):
        """업데이트된 벡터 인덱스 저장"""
        try:
            import faiss
            
            # 인덱스 저장
            faiss.write_index(index, str(self.vector_store_dir / "index.faiss"))
            
            # 메타데이터 저장
            with open(self.vector_store_dir / "meta.json", 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            
            # 매핑 저장
            with open(self.vector_store_dir / "mapping.json", 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False)
            
            logger.info(f"업데이트된 벡터 인덱스 저장 완료: {index.ntotal}개 벡터")
            
        except Exception as e:
            logger.error(f"벡터 인덱스 저장 실패: {str(e)}")
    
    def process_new_pdfs(self, pdf_dir: str) -> Dict[str, Any]:
        """새로 추가된 PDF 파일들을 처리"""
        logger.info("🔄 증분 임베딩 처리 시작")
        print("🔄 증분 임베딩 처리 시작")
        start_time = time.time()
        
        result = {
            "success": False,
            "processed_files": [],
            "new_chunks": 0,
            "total_chunks": 0,
            "processing_time": 0,
            "errors": []
        }
        
        try:
            # 1. 새 PDF 파일 목록 가져오기
            new_pdfs = self._get_new_pdf_files(pdf_dir)
            if not new_pdfs:
                logger.info("처리할 새 PDF 파일이 없습니다.")
                print("처리할 새 PDF 파일이 없습니다.")
                result["success"] = True
                return result
            
            logger.info(f"📄 새 PDF 파일 {len(new_pdfs)}개 처리 시작")
            print(f"📄 새 PDF 파일 {len(new_pdfs)}개 처리 시작")
            
            # 2. 기존 코퍼스 로드
            existing_corpus = self._load_existing_corpus()
            logger.info(f"기존 코퍼스: {len(existing_corpus)}개 청크")
            
            # 3. 새 PDF 파일들 처리
            new_chunks = []
            for pdf_path in new_pdfs:
                try:
                    logger.info(f"PDF 처리 중: {pdf_path.name}")
                    
                    # 텍스트 추출
                    text = self._extract_text_from_pdf(pdf_path)
                    if not text or len(text.strip()) < 100:
                        logger.warning(f"텍스트 추출 실패 또는 내용 부족: {pdf_path.name}")
                        continue
                    
                    # 청킹
                    chunks = self._chunk_text(text, pdf_path.name, pdf_path.stem)
                    if not chunks:
                        logger.warning(f"청킹 실패: {pdf_path.name}")
                        continue
                    
                    # JSON 형태로 변환
                    for chunk in chunks:
                        new_chunks.append({
                            "doc_id": chunk.doc_id,
                            "filename": chunk.filename,
                            "page": chunk.page,
                            "start": chunk.start_offset,
                            "length": chunk.length,
                            "text": chunk.text,
                            "extra": chunk.extra,
                        })
                    
                    # 처리된 파일 목록에 추가
                    self.processed_files.add(str(pdf_path))
                    result["processed_files"].append(str(pdf_path))
                    
                    logger.info(f"PDF 처리 완료: {pdf_path.name} - {len(chunks)}개 청크")
                    
                except Exception as e:
                    error_msg = f"PDF 처리 오류 {pdf_path}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
            if not new_chunks:
                logger.warning("처리된 새 청크가 없습니다.")
                result["success"] = True
                return result
            
            # 4. 코퍼스 업데이트
            updated_corpus = existing_corpus + new_chunks
            self._save_corpus(updated_corpus)
            result["new_chunks"] = len(new_chunks)
            result["total_chunks"] = len(updated_corpus)
            
            # 5. 벡터 인덱스 업데이트
            self._update_vector_index(new_chunks)
            
            # 6. 처리된 파일 목록 저장
            self._save_processed_files()
            
            end_time = time.time()
            result["processing_time"] = end_time - start_time
            result["success"] = True
            
            logger.info(f"✅ 증분 임베딩 처리 완료: {len(new_chunks)}개 새 청크 추가")
            print(f"✅ 증분 임베딩 처리 완료: {len(new_chunks)}개 새 청크 추가")
            logger.info(f"총 처리 시간: {result['processing_time']:.2f}초")
            print(f"총 처리 시간: {result['processing_time']:.2f}초")
            
        except Exception as e:
            error_msg = f"증분 임베딩 처리 오류: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    def _update_vector_index(self, new_chunks: List[Dict[str, Any]]):
        """벡터 인덱스 업데이트"""
        try:
            import faiss
            import numpy as np
            
            # 기존 벡터 인덱스 로드
            existing_index, meta, mapping = self._load_existing_vectors()
            
            # 새 청크들의 텍스트 추출
            new_texts = [chunk["text"] for chunk in new_chunks]
            
            # 새 벡터 생성
            logger.info(f"새 벡터 생성 중: {len(new_texts)}개 텍스트")
            new_embeddings = self.embedder.embed_texts(new_texts)
            new_embeddings_array = np.array(new_embeddings).astype('float32')
            
            if existing_index is None:
                # 새 인덱스 생성
                logger.info("새 벡터 인덱스 생성")
                index = faiss.index_factory(self.embedder.dim, "Flat")
                meta = {"dim": self.embedder.dim, "space": "l2"}
                mapping = list(range(len(new_chunks)))
            else:
                # 기존 인덱스에 추가
                logger.info(f"기존 벡터 인덱스에 {len(new_chunks)}개 벡터 추가")
                index = existing_index
                # 매핑 업데이트 (기존 매핑 + 새 인덱스)
                new_mapping = list(range(len(mapping), len(mapping) + len(new_chunks)))
                mapping.extend(new_mapping)
            
            # 벡터 추가
            index.add(new_embeddings_array)
            
            # 업데이트된 인덱스 저장
            self._save_updated_vectors(index, meta, mapping)
            
            logger.info(f"벡터 인덱스 업데이트 완료: 총 {index.ntotal}개 벡터")
            
        except Exception as e:
            logger.error(f"벡터 인덱스 업데이트 실패: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description="증분 임베딩 처리")
    parser.add_argument("--pdf_dir", default="data/pdfs", help="PDF 디렉토리")
    parser.add_argument("--corpus_file", default="data/corpus_v1.jsonl", help="코퍼스 파일")
    parser.add_argument("--vector_store_dir", default="vector_store", help="벡터 스토어 디렉토리")
    parser.add_argument("--processed_files_log", default="data/processed_files.json", help="처리된 파일 로그")
    parser.add_argument("--output_report", help="처리 결과 리포트 파일")
    
    args = parser.parse_args()
    
    try:
        # 증분 임베딩 프로세서 초기화
        processor = IncrementalEmbeddingProcessor(
            corpus_file=args.corpus_file,
            vector_store_dir=args.vector_store_dir,
            processed_files_log=args.processed_files_log
        )
        
        # 새 PDF 파일들 처리
        result = processor.process_new_pdfs(args.pdf_dir)
        
        # 결과 출력
        print("\n" + "="*50)
        print("증분 임베딩 처리 결과")
        print("="*50)
        print(f"성공: {result['success']}")
        print(f"처리된 파일: {len(result['processed_files'])}개")
        print(f"새 청크: {result['new_chunks']}개")
        print(f"총 청크: {result['total_chunks']}개")
        print(f"처리 시간: {result['processing_time']:.2f}초")
        
        if result['processed_files']:
            print("\n처리된 파일:")
            for file_path in result['processed_files']:
                print(f"  - {Path(file_path).name}")
        
        if result['errors']:
            print("\n오류:")
            for error in result['errors']:
                print(f"  - {error}")
        
        # 리포트 파일 저장
        if args.output_report:
            with open(args.output_report, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n결과 리포트 저장: {args.output_report}")
        
        # 성공 여부에 따른 종료 코드
        exit_code = 0 if result['success'] else 1
        exit(exit_code)
        
    except Exception as e:
        logger.error(f"증분 임베딩 실행 오류: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
