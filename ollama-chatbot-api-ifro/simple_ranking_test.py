#!/usr/bin/env python3
"""
도메인 특화 키워드 매칭의 효과를 비교하는 간단한 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 간단한 Mock 클래스들
class MockChunk:
    def __init__(self, text, metadata=None):
        self.text = text
        self.metadata = metadata or {}

class MockRetrievedSpan:
    def __init__(self, chunk, score, rank=0):
        self.chunk = chunk
        self.score = score
        self.rank = rank

def _select_best_contexts_enhanced(contexts, question, max_contexts=4, domain_dict=None, qtype="general"):
    """도메인 특화 키워드 매칭 있음"""
    if len(contexts) <= max_contexts:
        return contexts
    
    # 키워드 추출 (간단한 버전)
    keywords = []
    for word in question.split():
        if len(word) >= 2:
            keywords.append(word.lower())
    
    scored_contexts = []
    for context in contexts:
        text_lower = context.chunk.text.lower()
        keyword_matches = sum(1 for kw in keywords if kw in text_lower)
        
        # 도메인 특화 키워드 매칭
        domain_keyword_matches = 0
        high_priority_matches = 0
        
        if domain_dict:
            # 질문 유형별 키워드 매칭
            if qtype in domain_dict:
                type_keywords = domain_dict[qtype]
                domain_keyword_matches += sum(1 for kw in type_keywords if kw.lower() in text_lower)
            
            # 일반 도메인 키워드 매칭
            general_keywords = domain_dict.get("keywords", [])
            domain_keyword_matches += sum(1 for kw in general_keywords if kw.lower() in text_lower)
            
            # 고우선순위 키워드 매칭
            high_priority_keywords = domain_dict.get("high_priority_keywords", [])
            high_priority_matches = sum(1 for kw in high_priority_keywords if kw.lower() in text_lower)
        
        # 점수 계산
        basic_bonus = keyword_matches * 0.1
        domain_bonus = domain_keyword_matches * 0.2
        priority_bonus = high_priority_matches * 0.3
        total_score = context.score + basic_bonus + domain_bonus + priority_bonus
        
        scored_contexts.append((total_score, context))
    
    scored_contexts.sort(key=lambda x: x[0], reverse=True)
    return [ctx for _, ctx in scored_contexts[:max_contexts]]

def _select_best_contexts_simple(contexts, question, max_contexts=4, domain_dict=None, qtype="general"):
    """도메인 특화 키워드 매칭 없음"""
    if len(contexts) <= max_contexts:
        return contexts
    
    # 단순히 원래 점수만으로 정렬
    scored_contexts = [(context.score, context) for context in contexts]
    scored_contexts.sort(key=lambda x: x[0], reverse=True)
    return [ctx for _, ctx in scored_contexts[:max_contexts]]

def test_ranking_comparison():
    """랭킹 비교 테스트"""
    
    print("🔍 도메인 특화 키워드 매칭 효과 비교 테스트")
    print("=" * 60)
    
    # 도메인 사전
    domain_dict = {
        "수치_질문": ["교통량", "속도", "거리", "시간", "면적", "용량", "효율", "사고율", "대기시간", "교통밀도", "혼잡도", "지연시간"],
        "정의_질문": ["정의", "무엇", "란", "의미", "개념", "설명", "이해", "특징"],
        "절차_질문": ["방법", "절차", "순서", "어떻게", "과정", "단계", "운영", "관리"],
        "정책_질문": ["정책", "제도", "법규", "규정", "기준", "가이드라인", "지침", "방침"],
        "안전_질문": ["안전", "사고", "위험", "예방", "대응", "교육", "훈련", "점검"],
        "keywords": ["교통", "도로", "신호", "안전", "사고", "속도", "혼잡", "정책", "시스템", "플랫폼", "모델", "알고리즘"],
        "high_priority_keywords": ["교통량", "사고율", "속도", "안전", "정책", "시스템"]
    }
    
    # 테스트 질문들
    test_cases = [
        {
            "question": "서울시 교통량이 얼마나 되나요?",
            "qtype": "수치_질문",
            "contexts": [
                {"text": "서울시 일일 교통량은 평균 1,200만 대이며, 시간당 최대 교통량은 15만 대에 달합니다.", "score": 0.8},
                {"text": "교통사고 예방을 위해서는 안전운전 교육과 교통법규 준수가 중요합니다.", "score": 0.7},
                {"text": "신호등 제어 시스템은 SCOOT, SCATS 등의 알고리즘을 사용하여 실시간으로 신호주기를 조절합니다.", "score": 0.9},
                {"text": "일반적인 도시 계획에 대한 내용입니다.", "score": 0.5},
                {"text": "경제 발전과 관련된 내용입니다.", "score": 0.3}
            ]
        },
        {
            "question": "교통사고 예방 방법은 무엇인가요?",
            "qtype": "절차_질문",
            "contexts": [
                {"text": "교통사고 예방을 위해서는 안전운전 교육과 교통법규 준수가 중요합니다.", "score": 0.7},
                {"text": "서울시 일일 교통량은 평균 1,200만 대이며, 시간당 최대 교통량은 15만 대에 달합니다.", "score": 0.8},
                {"text": "신호등 제어 시스템은 SCOOT, SCATS 등의 알고리즘을 사용하여 실시간으로 신호주기를 조절합니다.", "score": 0.9},
                {"text": "일반적인 도시 계획에 대한 내용입니다.", "score": 0.5},
                {"text": "경제 발전과 관련된 내용입니다.", "score": 0.3}
            ]
        },
        {
            "question": "교통정책의 효과는 어떤가요?",
            "qtype": "정책_질문",
            "contexts": [
                {"text": "교통정책의 효과는 교통량 감소, 사고율 감소, 대기오염 감소 등으로 측정됩니다.", "score": 0.6},
                {"text": "서울시 일일 교통량은 평균 1,200만 대이며, 시간당 최대 교통량은 15만 대에 달합니다.", "score": 0.8},
                {"text": "교통사고 예방을 위해서는 안전운전 교육과 교통법규 준수가 중요합니다.", "score": 0.7},
                {"text": "일반적인 도시 계획에 대한 내용입니다.", "score": 0.5},
                {"text": "경제 발전과 관련된 내용입니다.", "score": 0.3}
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case["question"]
        qtype = test_case["qtype"]
        contexts_data = test_case["contexts"]
        
        print(f"\n📝 테스트 케이스 {i}: {question}")
        print(f"질문 유형: {qtype}")
        print("-" * 50)
        
        # Mock RetrievedSpan 객체 생성
        contexts = []
        for ctx_data in contexts_data:
            chunk = MockChunk(text=ctx_data["text"])
            span = MockRetrievedSpan(chunk=chunk, score=ctx_data["score"])
            contexts.append(span)
        
        # 1. 도메인 특화 키워드 매칭 있음
        print("\n🎯 도메인 특화 키워드 매칭 있음:")
        enhanced_contexts = _select_best_contexts_enhanced(contexts, question, max_contexts=3, domain_dict=domain_dict, qtype=qtype)
        
        for j, ctx in enumerate(enhanced_contexts, 1):
            print(f"  {j}. 점수: {ctx.score:.3f} | 텍스트: {ctx.chunk.text[:60]}...")
        
        # 2. 도메인 특화 키워드 매칭 없음
        print("\n📊 도메인 특화 키워드 매칭 없음:")
        simple_contexts = _select_best_contexts_simple(contexts, question, max_contexts=3, domain_dict=domain_dict, qtype=qtype)
        
        for j, ctx in enumerate(simple_contexts, 1):
            print(f"  {j}. 점수: {ctx.score:.3f} | 텍스트: {ctx.chunk.text[:60]}...")
        
        # 차이점 분석
        print("\n🔍 차이점 분석:")
        enhanced_texts = [ctx.chunk.text for ctx in enhanced_contexts]
        simple_texts = [ctx.chunk.text for ctx in simple_contexts]
        
        if enhanced_texts != simple_texts:
            print("  ✅ 컨텍스트 선택 순서가 다릅니다!")
            print("  📈 도메인 특화 키워드 매칭이 컨텍스트 선택에 영향을 미쳤습니다.")
            
            # 구체적인 차이점 표시
            print("  📋 상세 차이점:")
            for j, (enhanced, simple) in enumerate(zip(enhanced_texts, simple_texts), 1):
                if enhanced != simple:
                    print(f"    {j}순위: '{enhanced[:30]}...' vs '{simple[:30]}...'")
        else:
            print("  ⚠️  컨텍스트 선택 순서가 동일합니다.")
            print("  📉 이 질문에서는 도메인 특화 키워드 매칭의 효과가 제한적입니다.")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    test_ranking_comparison()
