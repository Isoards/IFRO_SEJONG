#!/usr/bin/env python3
"""
PDF QA 시스템 메인 실행 파일

이 파일은 PDF QA 시스템의 전체 파이프라인을 실행하고 관리하는
메인 엔트리포인트입니다.
"""

import argparse
import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

# 핵심 모듈들 임포트
from core.pdf_processor import PDFProcessor
from core.vector_store import HybridVectorStore
from core.question_analyzer import QuestionAnalyzer
from core.answer_generator import AnswerGenerator, ModelType, GenerationConfig
from core.evaluator import PDFQAEvaluator
from core.sql_generator import SQLGenerator, DatabaseSchema
from core.dual_pipeline_processor import DualPipelineProcessor
from api.endpoints import run_server
from utils.file_manager import PDFFileManager, setup_pdf_storage

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_qa_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class PDFQASystem:
    """
    PDF QA 시스템 메인 클래스
    
    전체 시스템의 초기화, 설정, 실행을 담당합니다.
    """
    
    def __init__(self, 
                 model_type: str = "ollama",
                 model_name: str = "mistral:latest",
                 embedding_model: str = "jhgan/ko-sroberta-multitask"):
        """
        시스템 초기화
        
        Args:
            model_type: 사용할 LLM 타입 (ollama/huggingface/llama_cpp)
            model_name: 모델 이름
            embedding_model: 임베딩 모델 이름
        """
        self.model_type = ModelType(model_type)
        self.model_name = model_name
        self.embedding_model = embedding_model
        
        # 컴포넌트들
        self.pdf_processor: Optional[PDFProcessor] = None
        self.vector_store: Optional[HybridVectorStore] = None
        self.question_analyzer: Optional[QuestionAnalyzer] = None
        self.answer_generator: Optional[AnswerGenerator] = None
        self.evaluator: Optional[PDFQAEvaluator] = None
        self.sql_generator: Optional[SQLGenerator] = None
        self.dual_pipeline_processor: Optional[DualPipelineProcessor] = None
        self.file_manager: Optional[PDFFileManager] = None
        
        logger.info(f"PDF QA 시스템 초기화: {model_type}/{model_name}")
    
    def initialize_components(self) -> bool:
        """
        시스템 컴포넌트들 초기화
        
        Returns:
            초기화 성공 여부
        """
        try:
            logger.info("컴포넌트 초기화 시작...")
            
            # 1. PDF 프로세서 초기화
            self.pdf_processor = PDFProcessor(
                embedding_model=self.embedding_model
            )
            logger.info("✓ PDF 프로세서 초기화 완료")
            
            # 2. 벡터 저장소 초기화
            self.vector_store = HybridVectorStore(
                embedding_dimension=768,  # 기본 임베딩 차원
                persist_directory="./vector_store"
            )
            
            # 기존 벡터 데이터 로드 시도
            vector_store_path = "./vector_store"
            if os.path.exists(vector_store_path):
                try:
                    self.vector_store.load(vector_store_path)
                    logger.info("✓ 기존 벡터 저장소 데이터 로드 완료")
                except Exception as e:
                    logger.warning(f"벡터 저장소 로드 실패 (새 저장소 생성): {e}")
            
            logger.info("✓ 벡터 저장소 초기화 완료")
            
            # 3. 질문 분석기 초기화
            self.question_analyzer = QuestionAnalyzer(
                embedding_model=self.embedding_model
            )
            logger.info("✓ 질문 분석기 초기화 완료")
            
            # 4. 답변 생성기 초기화
            config = GenerationConfig(
                max_length=512,
                temperature=0.7,
                top_p=0.9
            )
            
            self.answer_generator = AnswerGenerator(
                model_type=self.model_type,
                model_name=self.model_name,
                generation_config=config
            )
            
            # 모델 로드
            if not self.answer_generator.load_model():
                logger.error("답변 생성 모델 로드 실패")
                return False
            
            logger.info("✓ 답변 생성기 초기화 완료")
            
            # 5. 평가기 초기화
            self.evaluator = PDFQAEvaluator(
                embedding_model=self.embedding_model
            )
            logger.info("✓ 평가기 초기화 완료")
            
            # 6. SQL 생성기 초기화
            self.sql_generator = SQLGenerator()
            logger.info("✓ SQL 생성기 초기화 완료")
            
            # 7. Dual Pipeline 처리기 초기화
            # 샘플 데이터베이스 스키마 설정
            sample_schema = DatabaseSchema(
                table_name="users",
                columns=[
                    {"name": "id", "type": "INTEGER", "description": "사용자 ID"},
                    {"name": "name", "type": "TEXT", "description": "사용자 이름"},
                    {"name": "email", "type": "TEXT", "description": "이메일"},
                    {"name": "created_at", "type": "DATETIME", "description": "가입일"},
                    {"name": "status", "type": "TEXT", "description": "상태"}
                ],
                primary_key="id",
                sample_data=[
                    {"id": 1, "name": "김철수", "email": "kim@example.com", "created_at": "2023-01-01", "status": "active"},
                    {"id": 2, "name": "이영희", "email": "lee@example.com", "created_at": "2023-02-15", "status": "active"}
                ]
            )
            
            self.dual_pipeline_processor = DualPipelineProcessor(
                question_analyzer=self.question_analyzer,
                answer_generator=self.answer_generator,
                sql_generator=self.sql_generator,
                vector_store=self.vector_store,
                database_schema=sample_schema
            )
            logger.info("✓ Dual Pipeline 처리기 초기화 완료")
            
            # 8. 파일 매니저 초기화
            self.file_manager = setup_pdf_storage()
            logger.info("✓ 파일 매니저 초기화 완료")
            
            # 9. data 폴더의 PDF 파일들 자동 처리
            self.process_data_folder_pdfs()
            
            logger.info("모든 컴포넌트 초기화 완료!")
            return True
            
        except Exception as e:
            logger.error(f"컴포넌트 초기화 실패: {e}")
            return False
    
    def process_data_folder_pdfs(self):
        """data 폴더의 모든 PDF 파일들을 자동으로 처리"""
        data_folder = "./data"
        if not os.path.exists(data_folder):
            logger.warning("data 폴더가 존재하지 않습니다.")
            return
        
        pdf_files = []
        for file in os.listdir(data_folder):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(data_folder, file))
        
        if not pdf_files:
            logger.info("data 폴더에 PDF 파일이 없습니다.")
            return
        
        logger.info(f"data 폴더에서 {len(pdf_files)}개의 PDF 파일을 발견했습니다.")
        
        for pdf_path in pdf_files:
            try:
                # 이미 처리된 PDF인지 확인
                pdf_id = os.path.basename(pdf_path)
                if self.is_pdf_already_processed(pdf_id):
                    logger.info(f"이미 처리된 PDF 건너뛰기: {pdf_id}")
                    continue
                
                logger.info(f"PDF 처리 중: {pdf_id}")
                result = self.process_pdf(pdf_path)
                logger.info(f"✓ PDF 처리 완료: {result['filename']} ({result['total_chunks']}개 청크)")
                
            except Exception as e:
                logger.error(f"PDF 처리 실패 {pdf_path}: {e}")
    
    def is_pdf_already_processed(self, pdf_id: str) -> bool:
        """PDF가 이미 처리되었는지 확인"""
        try:
            # 벡터 저장소에서 해당 PDF의 청크들이 있는지 확인
            # 간단한 방법으로 파일명 기반 확인
            return False  # 일단 모든 PDF를 다시 처리하도록 설정
        except:
            return False
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """
        PDF 파일 처리
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            처리 결과
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        logger.info(f"PDF 처리 시작: {pdf_path}")
        start_time = time.time()
        
        try:
            # 1. PDF 텍스트 추출 및 임베딩 생성
            chunks, metadata = self.pdf_processor.process_pdf(pdf_path)
            
            # 2. 벡터 저장소에 추가
            self.vector_store.add_chunks(chunks)
            
            # 3. 저장소 저장
            self.vector_store.save()
            
            processing_time = time.time() - start_time
            
            result = {
                "pdf_id": metadata["pdf_id"],
                "filename": os.path.basename(pdf_path),
                "total_chunks": len(chunks),
                "total_pages": metadata.get("pages", 0),
                "processing_time": processing_time,
                "extraction_methods": metadata.get("extraction_method", [])
            }
            
            logger.info(f"PDF 처리 완료: {len(chunks)}개 청크, {processing_time:.2f}초")
            return result
            
        except Exception as e:
            logger.error(f"PDF 처리 실패: {e}")
            raise
    
    def ask_question(self, 
                    question: str, 
                    use_context: bool = True,
                    max_chunks: int = 5) -> Dict:
        """
        질문에 대한 답변 생성
        
        Args:
            question: 사용자 질문
            use_context: 이전 대화 컨텍스트 사용 여부
            max_chunks: 검색할 최대 청크 수
            
        Returns:
            답변 결과
        """
        logger.info(f"질문 처리: {question}")
        start_time = time.time()
        
        try:
            # 1. 질문 분석
            analyzed_question = self.question_analyzer.analyze_question(
                question, use_conversation_context=use_context
            )
            
            # 2. 관련 문서 검색
            relevant_chunks = self.vector_store.search(
                analyzed_question.embedding,
                top_k=max_chunks
            )
            
            if not relevant_chunks:
                return {
                    "answer": "관련된 정보를 찾을 수 없습니다. 다른 질문을 시도해보세요.",
                    "confidence_score": 0.0,
                    "question_type": analyzed_question.question_type.value,
                    "used_chunks": [],
                    "processing_time": time.time() - start_time
                }
            
            # 3. 대화 기록 가져오기
            conversation_history = None
            if use_context:
                conversation_history = self.question_analyzer.get_conversation_context(3)
            
            # 4. 답변 생성
            answer = self.answer_generator.generate_answer(
                analyzed_question,
                relevant_chunks,
                conversation_history
            )
            
            # 5. 대화 기록에 추가
            self.question_analyzer.add_conversation_item(
                question,
                answer.content,
                answer.used_chunks,
                answer.confidence_score
            )
            
            processing_time = time.time() - start_time
            
            result = {
                "answer": answer.content,
                "confidence_score": answer.confidence_score,
                "question_type": analyzed_question.question_type.value,
                "intent": analyzed_question.intent,
                "keywords": analyzed_question.keywords,
                "used_chunks": answer.used_chunks,
                "processing_time": processing_time,
                "model_name": answer.model_name
            }
            
            logger.info(f"답변 생성 완료: {processing_time:.2f}초, 신뢰도: {answer.confidence_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"질문 처리 실패: {e}")
            raise
    
    def interactive_mode(self):
        """대화형 모드 실행"""
        print("\n" + "="*60)
        print("PDF QA 시스템 - 대화형 모드")
        print("="*60)
        print("명령어:")
        print("  - 질문 입력: 자유롭게 질문하세요")
        print("  - '/clear': 대화 기록 초기화")
        print("  - '/status': 시스템 상태 조회")
        print("  - '/pdfs': 저장된 PDF 목록 조회")
        print("  - '/add <파일경로>': PDF 파일 추가")
        print("  - '/categories': 사용 가능한 카테고리 조회")
        print("  - '/exit': 프로그램 종료")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n질문: ").strip()
                
                if not user_input:
                    continue
                
                if user_input == '/exit':
                    print("프로그램을 종료합니다.")
                    break
                elif user_input == '/clear':
                    self.question_analyzer.conversation_history.clear()
                    print("대화 기록이 초기화되었습니다.")
                    continue
                elif user_input == '/status':
                    self.show_system_status()
                    continue
                elif user_input == '/pdfs':
                    self.show_pdf_list()
                    continue
                elif user_input == '/categories':
                    self.show_categories()
                    continue
                elif user_input.startswith('/add '):
                    pdf_path = user_input[5:].strip()
                    self.add_pdf_interactive(pdf_path)
                    continue
                
                # 질문 처리
                result = self.ask_question(user_input)
                
                print(f"\n답변: {result['answer']}")
                print(f"신뢰도: {result['confidence_score']:.2f}")
                print(f"질문 유형: {result['question_type']}")
                print(f"처리 시간: {result['processing_time']:.2f}초")
                
            except KeyboardInterrupt:
                print("\n\n프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"\n오류 발생: {e}")
                logger.error(f"대화형 모드 오류: {e}")
    
    def show_system_status(self):
        """시스템 상태 표시"""
        print("\n시스템 상태:")
        print(f"- 답변 생성 모델: {self.answer_generator.llm.model_name}")
        print(f"- 모델 로드 상태: {'정상' if self.answer_generator.llm.is_loaded else '오류'}")
        print(f"- 대화 기록: {len(self.question_analyzer.conversation_history)}개")
        
        # 메모리 사용량
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"- 메모리 사용량: {memory_mb:.1f}MB")
        except:
            pass
    
    def show_pdf_list(self):
        """저장된 PDF 목록 표시"""
        pdfs = self.file_manager.list_pdfs()
        
        if not pdfs:
            print("\n저장된 PDF 파일이 없습니다.")
            print("PDF 파일을 추가하려면 '/add <파일경로>' 명령어를 사용하세요.")
            return
        
        print(f"\n저장된 PDF 파일 ({len(pdfs)}개):")
        print("-" * 60)
        
        for i, pdf in enumerate(pdfs, 1):
            print(f"{i:2d}. {pdf['filename']}")
            print(f"    카테고리: {pdf['category']}")
            print(f"    크기: {pdf['size_mb']}MB")
            print(f"    수정일: {pdf['modified_at'][:19].replace('T', ' ')}")
            print()
    
    def show_categories(self):
        """사용 가능한 카테고리 표시"""
        categories = self.file_manager.get_categories()
        storage_info = self.file_manager.get_storage_info()
        
        print(f"\n사용 가능한 카테고리:")
        for category in categories:
            category_pdfs = self.file_manager.list_pdfs(category)
            print(f"  - {category}: {len(category_pdfs)}개 파일")
        
        print(f"\n저장소 정보:")
        print(f"  - 전체 파일 수: {storage_info['total_files']}개")
        print(f"  - 전체 크기: {storage_info['total_size_mb']}MB")
        print(f"  - 저장 위치: {storage_info['pdf_directory']}")
    
    def add_pdf_interactive(self, pdf_path: str):
        """대화형 PDF 추가"""
        try:
            if not os.path.exists(pdf_path):
                print(f"파일을 찾을 수 없습니다: {pdf_path}")
                return
            
            # 카테고리 선택
            categories = self.file_manager.get_categories()
            print("\n사용 가능한 카테고리:")
            for i, category in enumerate(categories, 1):
                print(f"  {i}. {category}")
            print(f"  {len(categories) + 1}. 새 카테고리 생성")
            
            try:
                choice = input("카테고리를 선택하세요 (번호 입력, 엔터=misc): ").strip()
                
                if not choice:
                    category = "misc"
                elif choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(categories):
                        category = categories[choice_num - 1]
                    elif choice_num == len(categories) + 1:
                        category = input("새 카테고리 이름: ").strip() or "misc"
                        self.file_manager.create_category(category)
                    else:
                        category = "misc"
                else:
                    category = choice
                
            except:
                category = "misc"
            
            # PDF 저장
            result = self.file_manager.save_pdf(pdf_path, category)
            print(f"\n✓ PDF 파일이 저장되었습니다:")
            print(f"  파일명: {result['filename']}")
            print(f"  카테고리: {result['category']}")
            print(f"  저장 경로: {result['saved_path']}")
            
            # PDF 처리 여부 선택
            process_choice = input("\n이 PDF를 지금 처리하시겠습니까? (y/N): ").strip().lower()
            if process_choice == 'y':
                print("PDF 처리 중...")
                process_result = self.process_pdf(result['saved_path'])
                print(f"✓ PDF 처리 완료: {process_result['total_chunks']}개 청크 생성")
            
        except Exception as e:
            print(f"PDF 추가 중 오류 발생: {e}")
    
    def cleanup(self):
        """시스템 정리"""
        logger.info("시스템 정리 중...")
        
        if self.answer_generator:
            self.answer_generator.unload_model()
        
        if self.vector_store:
            self.vector_store.save()
        
        logger.info("시스템 정리 완료")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="PDF QA 시스템")
    parser.add_argument("--mode", choices=["interactive", "server", "process"], 
                       default="interactive", help="실행 모드")
    parser.add_argument("--pdf", type=str, help="처리할 PDF 파일 경로")
    parser.add_argument("--question", type=str, help="질문 (process 모드)")
    parser.add_argument("--model-type", choices=["ollama", "huggingface", "llama_cpp"],
                       default="ollama", help="사용할 모델 타입")
    parser.add_argument("--model-name", type=str, default="mistral:latest", 
                       help="모델 이름")
    parser.add_argument("--embedding-model", type=str, 
                       default="jhgan/ko-sroberta-multitask",
                       help="임베딩 모델")
    parser.add_argument("--port", type=int, default=8000, help="서버 포트")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="서버 호스트")
    
    args = parser.parse_args()
    
    # 시스템 초기화
    system = PDFQASystem(
        model_type=args.model_type,
        model_name=args.model_name,
        embedding_model=args.embedding_model
    )
    
    try:
        # 컴포넌트 초기화
        if not system.initialize_components():
            logger.error("시스템 초기화 실패")
            sys.exit(1)
        
        # 모드별 실행
        if args.mode == "server":
            logger.info(f"API 서버 시작: http://{args.host}:{args.port}")
            logger.info("Dual Pipeline 기능이 활성화되었습니다.")
            logger.info("- 문서 검색 파이프라인: PDF 내용 기반 질문 답변")
            logger.info("- SQL 질의 파이프라인: 데이터베이스 스키마 기반 SQL 생성")
            logger.info("- 하이브리드 파이프라인: 두 파이프라인 결과 통합")
            run_server(host=args.host, port=args.port)
            
        elif args.mode == "process":
            if not args.pdf or not args.question:
                logger.error("process 모드에서는 --pdf와 --question이 필요합니다.")
                sys.exit(1)
            
            # PDF를 관리 폴더로 복사
            save_result = system.file_manager.save_pdf(args.pdf, "misc")
            print(f"PDF 저장 완료: {save_result['saved_path']}")
            
            # PDF 처리
            pdf_result = system.process_pdf(save_result['saved_path'])
            print(f"PDF 처리 완료: {pdf_result}")
            
            # 질문 처리
            qa_result = system.ask_question(args.question)
            print(f"답변: {qa_result['answer']}")
            
        else:  # interactive 모드
            if args.pdf:
                # PDF를 관리 폴더로 복사 후 처리
                print(f"PDF 파일을 관리 폴더로 복사 중: {args.pdf}")
                save_result = system.file_manager.save_pdf(args.pdf, "misc")
                print(f"저장 완료: {save_result['saved_path']}")
                
                # PDF 처리
                pdf_result = system.process_pdf(save_result['saved_path'])
                print(f"PDF 처리 완료: {pdf_result['filename']} ({pdf_result['total_chunks']}개 청크)")
            
            # 대화형 모드 시작
            system.interactive_mode()
    
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"시스템 실행 중 오류: {e}")
        sys.exit(1)
    finally:
        system.cleanup()

if __name__ == "__main__":
    main()
