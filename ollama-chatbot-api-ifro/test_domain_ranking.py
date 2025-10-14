#!/usr/bin/env python3
"""
도메인 특화 키워드 매칭의 효과를 비교하는 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from unifiedpdf import UnifiedPDFPipeline, PipelineConfig
from unifiedpdf.llm import _select_best_contexts, _select_best_contexts_simple
from unifiedpdf.domain_dictionary import get_domain_dictionary, get_question_keywords
import json

def test_domain_ranking_comparison():
    """도메인 특화 키워드 매칭 효과 비교 테스트"""
    
    # 테스트 질문들
    test_questions = [
        "서울시 교통량이 얼마나 되나요?",
        "교통사고 예방 방법은 무엇인가요?",
        "신호등 제어 시스템은 어떻게 작동하나요?",
        "교통정책의 효과는 어떤가요?",
        "도로 설계 기준은 무엇인가요?"
    ]
    
    print("🔍 도메인 특화 키워드 매칭 효과 비교 테스트")
    print("=" * 60)
    
    # 도메인 사전 로드
    domain_dict = {
        "수치_질문": ["교통량", "속도", "거리", "시간", "면적", "용량", "효율", "사고율", "대기시간", "교통밀도", "혼잡도", "지연시간"],
        "정의_질문": ["정의", "무엇", "란", "의미", "개념", "설명", "이해", "특징"],
        "절차_질문": ["방법", "절차", "순서", "어떻게", "과정", "단계", "운영", "관리"],
        "비교_질문": ["비교", "vs", "더", "높", "낮", "차이", "우수", "열등", "장단점", "효과"],
        "문제_질문": ["문제", "고장", "이상", "오류", "장애", "해결", "대책", "원인", "사고"],
        "정책_질문": ["정책", "제도", "법규", "규정", "기준", "가이드라인", "지침", "방침"],
        "안전_질문": ["안전", "사고", "위험", "예방", "대응", "교육", "훈련", "점검"],
        "환경_질문": ["환경", "오염", "대기", "소음", "온실가스", "친환경", "지속가능", "녹색"],
        "keywords": ["교통", "도로", "신호", "안전", "사고", "속도", "혼잡", "정책", "시스템", "플랫폼", "모델", "알고리즘"],
        "high_priority_keywords": ["교통량", "사고율", "속도", "안전", "정책", "시스템"]
    }
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 테스트 질문 {i}: {question}")
        print("-" * 50)
        
        # 질문 유형 분석 (간단한 휴리스틱)
        qtype = "general"
        if any(word in question for word in ["얼마", "몇", "수치", "교통량"]):
            qtype = "수치_질문"
        elif any(word in question for word in ["방법", "어떻게", "절차"]):
            qtype = "절차_질문"
        elif any(word in question for word in ["정의", "무엇", "란", "의미"]):
            qtype = "정의_질문"
        elif any(word in question for word in ["정책", "제도", "법규"]):
            qtype = "정책_질문"
        elif any(word in question for word in ["사고", "안전", "위험"]):
            qtype = "안전_질문"
        
        print(f"분석된 질문 유형: {qtype}")
        
        # 가상의 컨텍스트 데이터 생성 (실제로는 RAG 시스템에서 가져옴)
        mock_contexts = [
            {"text": "서울시 일일 교통량은 평균 1,200만 대이며, 시간당 최대 교통량은 15만 대에 달합니다.", "score": 0.8},
            {"text": "교통사고 예방을 위해서는 안전운전 교육과 교통법규 준수가 중요합니다.", "score": 0.7},
            {"text": "신호등 제어 시스템은 SCOOT, SCATS 등의 알고리즘을 사용하여 실시간으로 신호주기를 조절합니다.", "score": 0.9},
            {"text": "교통정책의 효과는 교통량 감소, 사고율 감소, 대기오염 감소 등으로 측정됩니다.", "score": 0.6},
            {"text": "도로 설계 기준은 설계속도, 설계교통량, 차로폭 등을 고려하여 결정됩니다.", "score": 0.85},
            {"text": "일반적인 도시 계획에 대한 내용입니다.", "score": 0.5},
            {"text": "경제 발전과 관련된 내용입니다.", "score": 0.3}
        ]
        
        # Mock RetrievedSpan 객체 생성
        from unifiedpdf.types import RetrievedSpan, Chunk
        
        contexts = []
        for ctx_data in mock_contexts:
            chunk = Chunk(text=ctx_data["text"], metadata={})
            span = RetrievedSpan(chunk=chunk, score=ctx_data["score"], rank=0)
            contexts.append(span)
        
        # 1. 도메인 특화 키워드 매칭 있음
        print("\n🎯 도메인 특화 키워드 매칭 있음:")
        enhanced_contexts = _select_best_contexts(contexts, question, max_contexts=3, domain_dict=domain_dict, qtype=qtype)
        
        for j, ctx in enumerate(enhanced_contexts, 1):
            print(f"  {j}. 점수: {ctx.score:.3f} | 텍스트: {ctx.chunk.text[:50]}...")
        
        # 2. 도메인 특화 키워드 매칭 없음
        print("\n📊 도메인 특화 키워드 매칭 없음:")
        simple_contexts = _select_best_contexts_simple(contexts, question, max_contexts=3, domain_dict=domain_dict, qtype=qtype)
        
        for j, ctx in enumerate(simple_contexts, 1):
            print(f"  {j}. 점수: {ctx.score:.3f} | 텍스트: {ctx.chunk.text[:50]}...")
        
        # 차이점 분석
        print("\n🔍 차이점 분석:")
        enhanced_texts = [ctx.chunk.text for ctx in enhanced_contexts]
        simple_texts = [ctx.chunk.text for ctx in simple_contexts]
        
        if enhanced_texts != simple_texts:
            print("  ✅ 컨텍스트 선택 순서가 다릅니다!")
            print("  📈 도메인 특화 키워드 매칭이 컨텍스트 선택에 영향을 미쳤습니다.")
        else:
            print("  ⚠️  컨텍스트 선택 순서가 동일합니다.")
            print("  📉 이 질문에서는 도메인 특화 키워드 매칭의 효과가 제한적입니다.")

if __name__ == "__main__":
    test_domain_ranking_comparison()
