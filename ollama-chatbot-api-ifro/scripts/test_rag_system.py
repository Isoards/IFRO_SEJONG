"""
RAG 시스템 테스트 스크립트
업로드된 PDF 기반으로 RAG 시스템이 올바르게 작동하는지 테스트합니다.
"""
import argparse
import json
import logging
import requests
import time
from typing import List, Dict, Any
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGSystemTester:
    """RAG 시스템 테스트 클래스"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.test_results = []
    
    def check_server_health(self) -> bool:
        """서버 상태 확인"""
        try:
            response = requests.get(f"{self.server_url}/healthz", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"서버 상태: {data}")
                return data.get("warmed", False)
            else:
                logger.error(f"서버 상태 확인 실패: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"서버 연결 실패: {str(e)}")
            return False
    
    def check_vector_index(self) -> bool:
        """벡터 인덱스 존재 확인"""
        try:
            index_path = Path("vector_store")
            required_files = ["index.faiss", "meta.json", "mapping.json"]
            
            for file_name in required_files:
                file_path = index_path / file_name
                if not file_path.exists():
                    logger.error(f"벡터 인덱스 파일 누락: {file_path}")
                    return False
            
            # 메타데이터 확인
            with open(index_path / "meta.json", 'r', encoding='utf-8') as f:
                meta = json.load(f)
                logger.info(f"벡터 인덱스 메타데이터: {meta}")
            
            # 매핑 파일 확인
            with open(index_path / "mapping.json", 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                logger.info(f"벡터 인덱스 매핑: {len(mapping)}개 청크")
            
            return True
            
        except Exception as e:
            logger.error(f"벡터 인덱스 확인 오류: {str(e)}")
            return False
    
    def check_corpus(self) -> bool:
        """코퍼스 파일 확인"""
        try:
            corpus_path = Path("data/corpus_v1.jsonl")
            if not corpus_path.exists():
                logger.error(f"코퍼스 파일 누락: {corpus_path}")
                return False
            
            # 코퍼스 통계
            chunk_count = 0
            total_chars = 0
            
            with open(corpus_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        chunk_count += 1
                        try:
                            data = json.loads(line)
                            total_chars += len(data.get("text", ""))
                        except json.JSONDecodeError:
                            continue
            
            logger.info(f"코퍼스 통계: {chunk_count}개 청크, {total_chars:,}자")
            return chunk_count > 0
            
        except Exception as e:
            logger.error(f"코퍼스 확인 오류: {str(e)}")
            return False
    
    def test_single_question(self, question: str, expected_keywords: List[str] = None) -> Dict[str, Any]:
        """단일 질문 테스트"""
        try:
            logger.info(f"테스트 질문: {question}")
            
            payload = {
                "question": question,
                "mode": "accuracy"
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.server_url}/api/ask",
                json=payload,
                timeout=30
            )
            end_time = time.time()
            
            result = {
                "question": question,
                "response_time": end_time - start_time,
                "success": False,
                "answer": "",
                "confidence": 0.0,
                "sources_count": 0,
                "sources": [],
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result.update({
                    "success": True,
                    "answer": data.get("answer", ""),
                    "confidence": data.get("confidence", 0.0),
                    "sources_count": len(data.get("sources", [])),
                    "sources": data.get("sources", [])
                })
                
                # 키워드 검증
                if expected_keywords:
                    answer_lower = result["answer"].lower()
                    found_keywords = [kw for kw in expected_keywords if kw.lower() in answer_lower]
                    result["expected_keywords"] = expected_keywords
                    result["found_keywords"] = found_keywords
                    result["keyword_match_rate"] = len(found_keywords) / len(expected_keywords)
                
                logger.info(f"답변 성공 - 신뢰도: {result['confidence']:.2f}, 소스: {result['sources_count']}개")
                if result["answer"]:
                    logger.info(f"답변 미리보기: {result['answer'][:100]}...")
                
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"질문 처리 실패: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"질문 테스트 오류: {str(e)}")
            return {
                "question": question,
                "success": False,
                "error": str(e),
                "response_time": 0.0
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합 테스트 실행"""
        logger.info("=== RAG 시스템 종합 테스트 시작 ===")
        
        test_summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "server_url": self.server_url,
            "system_checks": {},
            "question_tests": [],
            "overall_success": False,
            "performance_metrics": {}
        }
        
        # 1. 시스템 상태 확인
        logger.info("1. 시스템 상태 확인")
        test_summary["system_checks"]["server_health"] = self.check_server_health()
        test_summary["system_checks"]["vector_index"] = self.check_vector_index()
        test_summary["system_checks"]["corpus"] = self.check_corpus()
        
        # 시스템 상태가 정상이 아니면 테스트 중단
        if not all(test_summary["system_checks"].values()):
            logger.error("시스템 상태 확인 실패 - 테스트 중단")
            return test_summary
        
        # 2. 질문 테스트
        logger.info("2. 질문 테스트 시작")
        
        test_questions = [
            {
                "question": "교통사고가 발생했을 때 어떻게 해야 하나요?",
                "expected_keywords": ["교통사고", "신고", "응급", "경찰", "보험"]
            },
            {
                "question": "정수장 운영 방법에 대해 알려주세요.",
                "expected_keywords": ["정수장", "운영", "처리", "수질", "관리"]
            },
            {
                "question": "시스템 사용법을 설명해주세요.",
                "expected_keywords": ["시스템", "사용법", "방법", "절차", "가이드"]
            },
            {
                "question": "안전 관리에 대한 내용을 알려주세요.",
                "expected_keywords": ["안전", "관리", "점검", "예방", "사고"]
            },
            {
                "question": "장비 유지보수 방법은 무엇인가요?",
                "expected_keywords": ["장비", "유지보수", "점검", "수리", "관리"]
            }
        ]
        
        total_response_time = 0
        successful_tests = 0
        
        for i, test_case in enumerate(test_questions, 1):
            logger.info(f"테스트 {i}/{len(test_questions)}")
            result = self.test_single_question(
                test_case["question"], 
                test_case.get("expected_keywords")
            )
            
            test_summary["question_tests"].append(result)
            total_response_time += result.get("response_time", 0)
            
            if result["success"]:
                successful_tests += 1
        
        # 3. 성능 메트릭 계산
        test_summary["performance_metrics"] = {
            "total_tests": len(test_questions),
            "successful_tests": successful_tests,
            "success_rate": successful_tests / len(test_questions),
            "average_response_time": total_response_time / len(test_questions),
            "total_response_time": total_response_time
        }
        
        # 4. 전체 성공 여부 판정
        test_summary["overall_success"] = (
            all(test_summary["system_checks"].values()) and
            test_summary["performance_metrics"]["success_rate"] >= 0.8
        )
        
        logger.info("=== RAG 시스템 종합 테스트 완료 ===")
        logger.info(f"전체 성공: {test_summary['overall_success']}")
        logger.info(f"성공률: {test_summary['performance_metrics']['success_rate']:.1%}")
        logger.info(f"평균 응답시간: {test_summary['performance_metrics']['average_response_time']:.2f}초")
        
        return test_summary
    
    def generate_test_report(self, test_summary: Dict[str, Any], output_file: str = None):
        """테스트 리포트 생성"""
        report = []
        report.append("# RAG 시스템 테스트 리포트")
        report.append(f"**테스트 시간**: {test_summary['timestamp']}")
        report.append(f"**서버 URL**: {test_summary['server_url']}")
        report.append(f"**전체 성공**: {'✅' if test_summary['overall_success'] else '❌'}")
        report.append("")
        
        # 시스템 상태
        report.append("## 시스템 상태")
        for check, status in test_summary["system_checks"].items():
            report.append(f"- **{check}**: {'✅' if status else '❌'}")
        report.append("")
        
        # 성능 메트릭
        metrics = test_summary["performance_metrics"]
        report.append("## 성능 메트릭")
        report.append(f"- **전체 테스트**: {metrics['total_tests']}개")
        report.append(f"- **성공한 테스트**: {metrics['successful_tests']}개")
        report.append(f"- **성공률**: {metrics['success_rate']:.1%}")
        report.append(f"- **평균 응답시간**: {metrics['average_response_time']:.2f}초")
        report.append(f"- **총 응답시간**: {metrics['total_response_time']:.2f}초")
        report.append("")
        
        # 질문별 결과
        report.append("## 질문별 테스트 결과")
        for i, test in enumerate(test_summary["question_tests"], 1):
            report.append(f"### {i}. {test['question']}")
            report.append(f"**성공**: {'✅' if test['success'] else '❌'}")
            
            if test['success']:
                report.append(f"**신뢰도**: {test['confidence']:.2f}")
                report.append(f"**소스 수**: {test['sources_count']}개")
                report.append(f"**응답시간**: {test['response_time']:.2f}초")
                
                if 'keyword_match_rate' in test:
                    report.append(f"**키워드 매칭률**: {test['keyword_match_rate']:.1%}")
                    report.append(f"**발견된 키워드**: {', '.join(test.get('found_keywords', []))}")
                
                report.append(f"**답변**: {test['answer'][:200]}...")
            else:
                report.append(f"**오류**: {test['error']}")
            
            report.append("")
        
        # 리포트 출력
        report_text = "\n".join(report)
        print(report_text)
        
        # 파일 저장
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"테스트 리포트 저장: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="RAG 시스템 테스트")
    parser.add_argument("--server_url", default="http://localhost:8000", help="서버 URL")
    parser.add_argument("--output_report", help="테스트 리포트 파일 경로")
    parser.add_argument("--output_json", help="JSON 결과 파일 경로")
    
    args = parser.parse_args()
    
    # 테스터 초기화
    tester = RAGSystemTester(server_url=args.server_url)
    
    # 종합 테스트 실행
    test_summary = tester.run_comprehensive_test()
    
    # 리포트 생성
    tester.generate_test_report(test_summary, args.output_report)
    
    # JSON 결과 저장
    if args.output_json:
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON 결과 저장: {args.output_json}")
    
    # 종료 코드 설정
    exit_code = 0 if test_summary["overall_success"] else 1
    exit(exit_code)

if __name__ == "__main__":
    main()
