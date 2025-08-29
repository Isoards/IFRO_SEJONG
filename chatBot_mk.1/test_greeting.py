#!/usr/bin/env python3
"""
인사말 처리 기능 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.question_analyzer import QuestionAnalyzer
from core.answer_generator import AnswerGenerator, ModelType
from core.pdf_processor import TextChunk

def test_greeting_detection():
    """인사말 감지 테스트"""
    print("=" * 50)
    print("인사말 감지 테스트")
    print("=" * 50)
    
    analyzer = QuestionAnalyzer()
    
    # 테스트할 인사말들
    test_greetings = [
        "안녕하세요",
        "안녕",
        "반갑습니다",
        "반가워요",
        "하이",
        "hi",
        "hello",
        "좋은 아침입니다",
        "좋은 하루 되세요",
        "만나서 반가워",
        "오랜만이네요",
        "잘 지내세요?",
        "어떻게 지내세요?",
        "하이하이",
        "헬로우"
    ]
    
    # 테스트할 일반 질문들
    test_questions = [
        "교통량이 어떻게 되나요?",
        "사고 정보를 알려주세요",
        "이 문서의 내용은 무엇인가요?",
        "분석 결과를 보여주세요"
    ]
    
    print("\n인사말 테스트:")
    for greeting in test_greetings:
        analyzed = analyzer.analyze_question(greeting)
        is_greeting = analyzed.question_type.value == "greeting"
        print(f"'{greeting}' -> {'인사말' if is_greeting else '일반질문'}")
    
    print("\n일반 질문 테스트:")
    for question in test_questions:
        analyzed = analyzer.analyze_question(question)
        is_greeting = analyzed.question_type.value == "greeting"
        print(f"'{question}' -> {'인사말' if is_greeting else '일반질문'}")

def test_greeting_response():
    """인사말 응답 생성 테스트"""
    print("\n" + "=" * 50)
    print("인사말 응답 생성 테스트")
    print("=" * 50)
    
    # 간단한 모의 LLM 클래스
    class MockLLM:
        def __init__(self):
            self.model_name = "mock_model"
        
        def generate(self, prompt):
            # 프롬프트에서 인사말 응답 생성
            if "인사하는 AI 어시스턴트" in prompt:
                responses = [
                    "안녕하세요! 반갑습니다! 😊 무엇을 도와드릴까요?",
                    "하이하이! 만나서 반가워요! ✨ 오늘도 좋은 하루 되세요!",
                    "안녕하세요! 저는 IFRO 챗봇입니다. 도움이 필요하시면 언제든 말씀해 주세요! 🌟",
                    "반갑습니다! 교통 데이터 분석이나 대시보드 사용법에 대해 궁금한 점이 있으시면 언제든 물어보세요! 🚗"
                ]
                import random
                return random.choice(responses)
            else:
                return "일반적인 답변입니다."
    
    # 답변 생성기 초기화
    answer_generator = AnswerGenerator(
        model_type=ModelType.OLLAMA,  # 임시로 OLLAMA 사용
        model_name="mock_model",
        generation_config=None
    )
    answer_generator.llm = MockLLM()
    
    # 테스트할 인사말들
    test_greetings = [
        "안녕하세요",
        "반갑습니다",
        "하이",
        "좋은 아침입니다"
    ]
    
    analyzer = QuestionAnalyzer()
    
    for greeting in test_greetings:
        print(f"\n사용자: {greeting}")
        
        # 질문 분석
        analyzed = analyzer.analyze_question(greeting)
        print(f"분석 결과: {analyzed.question_type.value}")
        
        # 답변 생성
        try:
            answer = answer_generator.generate_answer(
                analyzed_question=analyzed,
                relevant_chunks=[],  # 인사말은 컨텍스트 불필요
                conversation_history=None
            )
            print(f"챗봇: {answer.content}")
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    test_greeting_detection()
    test_greeting_response()
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("=" * 50)
