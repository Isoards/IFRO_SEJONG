"""
병렬 PDF 임베딩 처리 스크립트
여러 PDF를 동시에 처리하여 임베딩 성능을 향상시킵니다.
"""
import argparse
import asyncio
import json
import logging
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Tuple
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

class ParallelEmbeddingProcessor:
    """병렬 임베딩 처리 클래스"""
    
    def __init__(self, 
                 max_workers: int = None,
                 use_gpu: bool = False,
                 chunk_size: int = 500,
                 chunk_overlap: int = 100):
        """
        Args:
            max_workers: 최대 워커 수 (None이면 CPU 코어 수)
            use_gpu: GPU 사용 여부
            chunk_size: 청크 크기
            chunk_overlap: 청크 오버랩
        """
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.use_gpu = use_gpu
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        logger.info(f"병렬 임베딩 프로세서 초기화: {self.max_workers}개 워커, GPU: {use_gpu}")
    
    def process_single_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """단일 PDF 처리"""
        try:
            from scripts.build_corpus_from_pdfs import extract_text_auto, deduplicate_chunks
            from unifiedpdf.pdf_processor import PDFProcessor, PDFChunkConfig
            from unifiedpdf.measurements import extract_measurements
            
            pdf_file = Path(pdf_path)
            logger.info(f"PDF 처리 시작: {pdf_file.name}")
            
            # 텍스트 추출
            text = extract_text_auto(pdf_file)
            if not text or len(text.strip()) < 100:
                logger.warning(f"텍스트 추출 실패 또는 내용 부족: {pdf_file.name}")
                return []
            
            # 청킹 처리
            cfg = PDFChunkConfig(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                enable_wastewater_chunking=True,
                wastewater_chunk_size=900,
                wastewater_overlap_ratio=0.25,
            )
            proc = PDFProcessor(cfg)
            chunks = proc.chunk_text(doc_id=pdf_file.stem, filename=pdf_file.name, text=text)
            
            # 중복 제거
            unique_chunks = deduplicate_chunks(chunks, threshold=0.9, min_length=50)
            
            # JSON 형태로 변환
            result = []
            for chunk in unique_chunks:
                result.append({
                    "doc_id": chunk.doc_id,
                    "filename": chunk.filename,
                    "page": chunk.page,
                    "start": chunk.start_offset,
                    "length": chunk.length,
                    "text": chunk.text,
                    "extra": chunk.extra,
                })
            
            logger.info(f"PDF 처리 완료: {pdf_file.name} - {len(result)}개 청크")
            return result
            
        except Exception as e:
            logger.error(f"PDF 처리 오류 {pdf_path}: {str(e)}")
            return []
    
    def process_pdfs_parallel(self, pdf_paths: List[str]) -> List[Dict[str, Any]]:
        """여러 PDF를 병렬로 처리"""
        logger.info(f"병렬 PDF 처리 시작: {len(pdf_paths)}개 파일")
        start_time = time.time()
        
        all_chunks = []
        
        # ProcessPoolExecutor를 사용한 병렬 처리
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 각 PDF를 병렬로 처리
            futures = [executor.submit(self.process_single_pdf, pdf_path) for pdf_path in pdf_paths]
            
            # 결과 수집
            for i, future in enumerate(futures):
                try:
                    chunks = future.result(timeout=300)  # 5분 타임아웃
                    all_chunks.extend(chunks)
                    logger.info(f"진행률: {i+1}/{len(pdf_paths)} - {pdf_paths[i]}")
                except Exception as e:
                    logger.error(f"PDF 처리 실패 {pdf_paths[i]}: {str(e)}")
        
        end_time = time.time()
        logger.info(f"병렬 PDF 처리 완료: {len(all_chunks)}개 청크, 소요시간: {end_time - start_time:.2f}초")
        
        return all_chunks
    
    def build_embeddings_parallel(self, chunks: List[Dict[str, Any]]) -> Tuple[List[Chunk], Any]:
        """청크들을 병렬로 임베딩"""
        logger.info(f"병렬 임베딩 시작: {len(chunks)}개 청크")
        start_time = time.time()
        
        # Chunk 객체로 변환
        chunk_objects = []
        for obj in chunks:
            chunk_objects.append(Chunk(
                doc_id=obj.get("doc_id", obj.get("filename", "doc")),
                filename=obj.get("filename", "doc"),
                page=obj.get("page"),
                start_offset=int(obj.get("start", 0)),
                length=int(obj.get("length", len(obj.get("text", "")))),
                text=obj.get("text", ""),
                extra=obj.get("extra", {}),
            ))
        
        # 임베더 초기화
        embedder = get_embedder(PipelineConfig().embedding_model, use_gpu=self.use_gpu)
        if embedder is None:
            raise RuntimeError("임베더를 초기화할 수 없습니다.")
        
        # 텍스트 추출
        texts = [c.text for c in chunk_objects]
        
        # 배치 크기 설정 (메모리 사용량 고려)
        batch_size = min(32, len(texts))
        embeddings = []
        
        # 배치별로 임베딩 처리
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = embedder.embed_texts(batch_texts)
            embeddings.extend(batch_embeddings)
            
            if (i // batch_size + 1) % 10 == 0:
                logger.info(f"임베딩 진행률: {i + len(batch_texts)}/{len(texts)}")
        
        end_time = time.time()
        logger.info(f"병렬 임베딩 완료: {len(embeddings)}개 벡터, 소요시간: {end_time - start_time:.2f}초")
        
        return chunk_objects, embeddings
    
    def save_vector_index(self, chunks: List[Chunk], embeddings: List, output_dir: str, backend: str = "faiss"):
        """벡터 인덱스 저장"""
        logger.info(f"벡터 인덱스 저장 시작: {backend} 백엔드")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if backend == "faiss":
            try:
                import faiss
                import numpy as np
            except ImportError:
                raise RuntimeError("faiss-cpu가 설치되지 않았습니다.")
            
            # FAISS 인덱스 생성
            embedder = get_embedder(PipelineConfig().embedding_model, use_gpu=False)
            index = faiss.index_factory(embedder.dim, "Flat")
            
            # 벡터 추가
            embeddings_array = np.array(embeddings).astype('float32')
            index.add(embeddings_array)
            
            # 인덱스 저장
            faiss.write_index(index, str(output_path / "index.faiss"))
            
            # 메타데이터 저장
            meta = {"dim": embedder.dim, "space": "l2"}
            with (output_path / "meta.json").open("w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            
            # 매핑 저장
            with (output_path / "mapping.json").open("w", encoding="utf-8") as f:
                json.dump(list(range(len(chunks))), f, ensure_ascii=False)
            
            logger.info(f"FAISS 인덱스 저장 완료: {output_path}")
            
        elif backend == "hnsw":
            try:
                import hnswlib
                import numpy as np
            except ImportError:
                raise RuntimeError("hnswlib가 설치되지 않았습니다.")
            
            # HNSW 인덱스 생성
            embedder = get_embedder(PipelineConfig().embedding_model, use_gpu=False)
            p = hnswlib.Index(space="cosine", dim=embedder.dim)
            p.init_index(max_elements=len(chunks), ef_construction=200, M=16)
            
            # 벡터 추가
            embeddings_array = np.array(embeddings).astype('float32')
            labels = np.arange(len(chunks))
            p.add_items(embeddings_array, labels)
            
            # 인덱스 저장
            p.save_index(str(output_path / "index.hnsw"))
            
            # 메타데이터 저장
            meta = {"dim": embedder.dim, "space": "cosine"}
            with (output_path / "meta.json").open("w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            
            # 매핑 저장
            with (output_path / "mapping.json").open("w", encoding="utf-8") as f:
                json.dump(list(range(len(chunks))), f, ensure_ascii=False)
            
            logger.info(f"HNSW 인덱스 저장 완료: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="병렬 PDF 임베딩 처리")
    parser.add_argument("--pdf_dir", default="data/pdfs", help="PDF 디렉토리")
    parser.add_argument("--output_corpus", default="data/corpus_v1.jsonl", help="출력 코퍼스 파일")
    parser.add_argument("--output_index", default="vector_store", help="벡터 인덱스 출력 디렉토리")
    parser.add_argument("--backend", default="faiss", choices=["faiss", "hnsw"], help="벡터 백엔드")
    parser.add_argument("--max_workers", type=int, default=None, help="최대 워커 수")
    parser.add_argument("--use_gpu", action="store_true", help="GPU 사용")
    parser.add_argument("--chunk_size", type=int, default=500, help="청크 크기")
    parser.add_argument("--chunk_overlap", type=int, default=100, help="청크 오버랩")
    parser.add_argument("--dedup_vectors", action="store_true", help="벡터 중복 제거")
    parser.add_argument("--vector_similarity_threshold", type=float, default=0.99, help="벡터 유사도 임계값")
    
    args = parser.parse_args()
    
    # PDF 파일 목록 수집
    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        logger.error(f"PDF 디렉토리가 존재하지 않습니다: {pdf_dir}")
        return
    
    pdf_files = list(pdf_dir.glob("**/*.pdf"))
    if not pdf_files:
        logger.error(f"PDF 파일을 찾을 수 없습니다: {pdf_dir}")
        return
    
    logger.info(f"처리할 PDF 파일: {len(pdf_files)}개")
    for pdf_file in pdf_files:
        logger.info(f"  - {pdf_file.name}")
    
    # 병렬 처리기 초기화
    processor = ParallelEmbeddingProcessor(
        max_workers=args.max_workers,
        use_gpu=args.use_gpu,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    try:
        # 1. PDF 병렬 처리
        all_chunks = processor.process_pdfs_parallel([str(pdf) for pdf in pdf_files])
        
        if not all_chunks:
            logger.error("처리된 청크가 없습니다.")
            return
        
        # 2. 코퍼스 파일 저장
        corpus_path = Path(args.output_corpus)
        corpus_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 기존 파일 백업
        if corpus_path.exists():
            backup_path = corpus_path.with_suffix(corpus_path.suffix + ".bak")
            if backup_path.exists():
                backup_path.unlink()
            corpus_path.rename(backup_path)
            logger.info(f"기존 코퍼스 백업: {backup_path}")
        
        # 새 코퍼스 저장
        with corpus_path.open("w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        
        logger.info(f"코퍼스 저장 완료: {corpus_path} ({len(all_chunks)}개 청크)")
        
        # 3. 벡터 중복 제거 (선택적)
        if args.dedup_vectors:
            logger.info("벡터 중복 제거 시작")
            # 임베더 초기화
            embedder = get_embedder(PipelineConfig().embedding_model, use_gpu=args.use_gpu)
            if embedder is None:
                raise RuntimeError("임베더를 초기화할 수 없습니다.")
            
            # 텍스트 임베딩
            texts = [chunk["text"] for chunk in all_chunks]
            embeddings = embedder.embed_texts(texts)
            
            # 중복 제거
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            unique_indices = []
            seen_vectors = []
            
            for i, emb in enumerate(embeddings):
                is_duplicate = False
                for seen_emb in seen_vectors:
                    similarity = cosine_similarity([emb], [seen_emb])[0][0]
                    if similarity >= args.vector_similarity_threshold:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_indices.append(i)
                    seen_vectors.append(emb)
            
            # 중복 제거된 데이터로 업데이트
            all_chunks = [all_chunks[i] for i in unique_indices]
            embeddings = np.array([embeddings[i] for i in unique_indices])
            
            logger.info(f"벡터 중복 제거 완료: {len(unique_indices)}개 유니크 벡터 유지")
        
        # 4. 임베딩 생성
        chunk_objects, embeddings = processor.build_embeddings_parallel(all_chunks)
        
        # 5. 벡터 인덱스 저장
        processor.save_vector_index(chunk_objects, embeddings, args.output_index, args.backend)
        
        logger.info("병렬 임베딩 처리 완료!")
        logger.info(f"  - 처리된 PDF: {len(pdf_files)}개")
        logger.info(f"  - 생성된 청크: {len(all_chunks)}개")
        logger.info(f"  - 벡터 인덱스: {args.output_index}")
        
    except Exception as e:
        logger.error(f"병렬 임베딩 처리 오류: {str(e)}")
        raise

if __name__ == "__main__":
    main()
