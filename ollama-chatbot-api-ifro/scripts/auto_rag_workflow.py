"""
자동화된 RAG 워크플로우 스크립트
PDF 업로드부터 벡터 인덱스 구축, RAG 시스템 테스트까지 전체 과정을 자동화합니다.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
import subprocess

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoRAGWorkflow:
    """자동화된 RAG 워크플로우 클래스"""
    
    def __init__(self, 
                 server_url: str = "http://localhost:8000",
                 pdf_dir: str = "data/pdfs",
                 use_parallel: bool = True,
                 max_workers: int = None):
        """
        Args:
            server_url: 챗봇 서버 URL
            pdf_dir: PDF 저장 디렉토리
            use_parallel: 병렬 처리 사용 여부
            max_workers: 최대 워커 수
        """
        self.server_url = server_url
        self.pdf_dir = Path(pdf_dir)
        self.use_parallel = use_parallel
        self.max_workers = max_workers
        
        # 디렉토리 생성
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"RAG 워크플로우 초기화: {server_url}, 병렬처리: {use_parallel}")
    
    def check_server_status(self) -> bool:
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.server_url}/healthz", timeout=5)
            if response.status_code == 200:
                logger.info("서버 상태 정상")
                return True
            else:
                logger.error(f"서버 상태 이상: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"서버 연결 실패: {str(e)}")
            return False
    
    def upload_pdf_file(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 파일 업로드"""
        try:
            logger.info(f"PDF 업로드 시작: {pdf_path}")
            
            with open(pdf_path, 'rb') as f:
                files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
                response = requests.post(
                    f"{self.server_url}/api/upload-pdf",
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"PDF 업로드 성공: {result['filename']}")
                return result
            else:
                logger.error(f"PDF 업로드 실패: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"PDF 업로드 오류: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def list_uploaded_pdfs(self) -> List[Dict[str, Any]]:
        """업로드된 PDF 목록 조회"""
        try:
            response = requests.get(f"{self.server_url}/api/pdfs", timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result.get("pdfs", [])
            else:
                logger.error(f"PDF 목록 조회 실패: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"PDF 목록 조회 오류: {str(e)}")
            return []
    
    def rebuild_vector_index(self) -> bool:
        """벡터 인덱스 재구축"""
        try:
            logger.info("벡터 인덱스 재구축 시작")
            
            response = requests.post(
                f"{self.server_url}/api/rebuild-index",
                timeout=300  # 5분 타임아웃
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"벡터 인덱스 재구축 요청 성공: {result['message']}")
                return True
            else:
                logger.error(f"벡터 인덱스 재구축 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"벡터 인덱스 재구축 오류: {str(e)}")
            return False
    
    def test_rag_system(self, test_questions: List[str]) -> List[Dict[str, Any]]:
        """RAG 시스템 테스트"""
        results = []
        
        for question in test_questions:
            try:
                logger.info(f"RAG 테스트 질문: {question}")
                
                payload = {
                    "question": question,
                    "mode": "accuracy"
                }
                
                response = requests.post(
                    f"{self.server_url}/api/ask",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append({
                        "question": question,
                        "answer": result.get("answer", ""),
                        "confidence": result.get("confidence", 0.0),
                        "sources_count": len(result.get("sources", [])),
                        "success": True
                    })
                    logger.info(f"RAG 테스트 성공 - 신뢰도: {result.get('confidence', 0.0):.2f}")
                else:
                    results.append({
                        "question": question,
                        "error": f"HTTP {response.status_code}",
                        "success": False
                    })
                    logger.error(f"RAG 테스트 실패: {response.status_code}")
                    
            except Exception as e:
                results.append({
                    "question": question,
                    "error": str(e),
                    "success": False
                })
                logger.error(f"RAG 테스트 오류: {str(e)}")
        
        return results
    
    def run_parallel_embedding(self) -> bool:
        """병렬 임베딩 실행"""
        try:
            logger.info("병렬 임베딩 실행 시작")
            
            # 병렬 임베딩 스크립트 실행
            cmd = [
                sys.executable, 
                "scripts/parallel_embedding.py",
                "--pdf_dir", str(self.pdf_dir),
                "--output_corpus", "data/corpus_v1.jsonl",
                "--output_index", "vector_store",
                "--backend", "faiss"
            ]
            
            if self.max_workers:
                cmd.extend(["--max_workers", str(self.max_workers)])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30분 타임아웃
            )
            
            if result.returncode == 0:
                logger.info("병렬 임베딩 실행 성공")
                logger.info(f"출력: {result.stdout}")
                return True
            else:
                logger.error(f"병렬 임베딩 실행 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("병렬 임베딩 실행 시간 초과")
            return False
        except Exception as e:
            logger.error(f"병렬 임베딩 실행 오류: {str(e)}")
            return False
    
    def run_standard_embedding(self) -> bool:
        """표준 임베딩 실행"""
        try:
            logger.info("표준 임베딩 실행 시작")
            
            # 코퍼스 구축
            corpus_cmd = [
                sys.executable,
                "scripts/build_corpus_from_pdfs.py",
                "--pdf_dir", str(self.pdf_dir),
                "--out", "data/corpus_v1.jsonl",
                "--chunking", "window",
                "--chunk-size", "500",
                "--chunk-overlap", "100"
            ]
            
            result = subprocess.run(
                corpus_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10분 타임아웃
            )
            
            if result.returncode != 0:
                logger.error(f"코퍼스 구축 실패: {result.stderr}")
                return False
            
            # 벡터 인덱스 구축
            index_cmd = [
                sys.executable,
                "scripts/build_vector_index.py",
                "--corpus", "data/corpus_v1.jsonl",
                "--backend", "faiss",
                "--outdir", "vector_store"
            ]
            
            result = subprocess.run(
                index_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10분 타임아웃
            )
            
            if result.returncode == 0:
                logger.info("표준 임베딩 실행 성공")
                return True
            else:
                logger.error(f"벡터 인덱스 구축 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("표준 임베딩 실행 시간 초과")
            return False
        except Exception as e:
            logger.error(f"표준 임베딩 실행 오류: {str(e)}")
            return False
    
    def run_full_workflow(self, 
                         pdf_files: List[str] = None,
                         test_questions: List[str] = None) -> Dict[str, Any]:
        """전체 워크플로우 실행"""
        workflow_result = {
            "success": False,
            "steps": {},
            "test_results": [],
            "errors": []
        }
        
        try:
            # 1. 서버 상태 확인
            logger.info("=== 1단계: 서버 상태 확인 ===")
            if not self.check_server_status():
                workflow_result["errors"].append("서버 연결 실패")
                return workflow_result
            workflow_result["steps"]["server_check"] = True
            
            # 2. PDF 파일 업로드 (제공된 경우)
            if pdf_files:
                logger.info("=== 2단계: PDF 파일 업로드 ===")
                upload_results = []
                for pdf_file in pdf_files:
                    if Path(pdf_file).exists():
                        result = self.upload_pdf_file(pdf_file)
                        upload_results.append(result)
                    else:
                        logger.warning(f"PDF 파일을 찾을 수 없습니다: {pdf_file}")
                        upload_results.append({"success": False, "error": "파일 없음"})
                
                workflow_result["steps"]["pdf_upload"] = upload_results
                
                # 업로드 완료 대기
                logger.info("PDF 업로드 완료 대기 중...")
                time.sleep(5)
            
            # 3. 임베딩 처리
            logger.info("=== 3단계: 임베딩 처리 ===")
            if self.use_parallel:
                embedding_success = self.run_parallel_embedding()
            else:
                embedding_success = self.run_standard_embedding()
            
            workflow_result["steps"]["embedding"] = embedding_success
            
            if not embedding_success:
                workflow_result["errors"].append("임베딩 처리 실패")
                return workflow_result
            
            # 4. 서버 재시작 (벡터 인덱스 로드)
            logger.info("=== 4단계: 서버 재시작 ===")
            logger.info("벡터 인덱스가 업데이트되었습니다. 서버를 재시작해주세요.")
            workflow_result["steps"]["server_restart"] = "manual_required"
            
            # 5. RAG 시스템 테스트
            if test_questions:
                logger.info("=== 5단계: RAG 시스템 테스트 ===")
                test_results = self.test_rag_system(test_questions)
                workflow_result["test_results"] = test_results
                workflow_result["steps"]["rag_test"] = len([r for r in test_results if r["success"]])
            
            workflow_result["success"] = True
            logger.info("=== RAG 워크플로우 완료 ===")
            
        except Exception as e:
            logger.error(f"워크플로우 실행 오류: {str(e)}")
            workflow_result["errors"].append(str(e))
        
        return workflow_result

def main():
    parser = argparse.ArgumentParser(description="자동화된 RAG 워크플로우")
    parser.add_argument("--server_url", default="http://localhost:8000", help="서버 URL")
    parser.add_argument("--pdf_dir", default="data/pdfs", help="PDF 디렉토리")
    parser.add_argument("--pdf_files", nargs="*", help="업로드할 PDF 파일 목록")
    parser.add_argument("--use_parallel", action="store_true", help="병렬 임베딩 사용")
    parser.add_argument("--max_workers", type=int, help="최대 워커 수")
    parser.add_argument("--test_questions", nargs="*", help="테스트 질문 목록")
    parser.add_argument("--output_report", help="결과 리포트 파일 경로")
    
    args = parser.parse_args()
    
    # 기본 테스트 질문
    default_test_questions = [
        "교통사고가 발생했을 때 어떻게 해야 하나요?",
        "정수장 운영 방법에 대해 알려주세요.",
        "시스템 사용법을 설명해주세요."
    ]
    
    test_questions = args.test_questions or default_test_questions
    
    # 워크플로우 실행
    workflow = AutoRAGWorkflow(
        server_url=args.server_url,
        pdf_dir=args.pdf_dir,
        use_parallel=args.use_parallel,
        max_workers=args.max_workers
    )
    
    result = workflow.run_full_workflow(
        pdf_files=args.pdf_files,
        test_questions=test_questions
    )
    
    # 결과 출력
    print("\n" + "="*50)
    print("RAG 워크플로우 실행 결과")
    print("="*50)
    print(f"성공: {result['success']}")
    print(f"단계별 결과: {result['steps']}")
    
    if result['test_results']:
        print("\n테스트 결과:")
        for i, test in enumerate(result['test_results'], 1):
            print(f"{i}. 질문: {test['question']}")
            if test['success']:
                print(f"   답변: {test['answer'][:100]}...")
                print(f"   신뢰도: {test['confidence']:.2f}")
                print(f"   소스 수: {test['sources_count']}")
            else:
                print(f"   오류: {test['error']}")
            print()
    
    if result['errors']:
        print("오류:")
        for error in result['errors']:
            print(f"  - {error}")
    
    # 리포트 파일 저장
    if args.output_report:
        with open(args.output_report, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n결과 리포트 저장: {args.output_report}")

if __name__ == "__main__":
    main()
