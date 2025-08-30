#!/usr/bin/env python3
"""
데이터셋 분석 스크립트

이 스크립트는 의도 분류 학습 데이터셋을 분석하여 통계 정보를 제공합니다.
"""

import json
import os
from collections import Counter
from typing import Dict, List, Tuple

def analyze_dataset(file_path: str) -> Dict:
    """데이터셋 분석"""
    print("=" * 60)
    print("📊 데이터셋 분석")
    print("=" * 60)
    
    # 데이터셋 로드
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except Exception as e:
        print(f"❌ 데이터셋 로드 실패: {e}")
        return {}
    
    # 기본 통계
    total_intents = len(dataset)
    total_examples = sum(len(examples) for examples in dataset.values())
    
    print(f"\n📈 기본 통계")
    print(f"의도 유형 수: {total_intents}")
    print(f"총 예시 수: {total_examples}")
    print(f"평균 예시 수: {total_examples / total_intents:.1f}")
    
    # 의도별 통계
    print(f"\n📋 의도별 통계")
    intent_stats = []
    for intent, examples in dataset.items():
        count = len(examples)
        percentage = (count / total_examples) * 100
        intent_stats.append((intent, count, percentage))
        
        print(f"{intent}: {count}개 ({percentage:.1f}%)")
    
    # 의도별 예시 수 분포
    print(f"\n📊 의도별 예시 수 분포")
    counts = [count for _, count, _ in intent_stats]
    print(f"최소: {min(counts)}개")
    print(f"최대: {max(counts)}개")
    print(f"중앙값: {sorted(counts)[len(counts)//2]}개")
    
    # 불균형 분석
    print(f"\n⚖️ 데이터 불균형 분석")
    max_count = max(counts)
    min_count = min(counts)
    imbalance_ratio = max_count / min_count if min_count > 0 else float('inf')
    print(f"최대/최소 비율: {imbalance_ratio:.1f}")
    
    if imbalance_ratio > 3:
        print("⚠️ 데이터 불균형이 심각합니다. 일부 의도에 대한 추가 데이터가 필요할 수 있습니다.")
    elif imbalance_ratio > 2:
        print("⚠️ 데이터 불균형이 있습니다. 일부 의도에 대한 추가 데이터를 고려해보세요.")
    else:
        print("✅ 데이터 분포가 비교적 균형잡혀 있습니다.")
    
    # 질문 길이 분석
    print(f"\n📏 질문 길이 분석")
    all_questions = []
    for examples in dataset.values():
        all_questions.extend(examples)
    
    question_lengths = [len(q) for q in all_questions]
    avg_length = sum(question_lengths) / len(question_lengths)
    min_length = min(question_lengths)
    max_length = max(question_lengths)
    
    print(f"평균 길이: {avg_length:.1f}자")
    print(f"최소 길이: {min_length}자")
    print(f"최대 길이: {max_length}자")
    
    # 길이별 분포
    length_ranges = [
        (0, 10, "매우 짧음"),
        (11, 20, "짧음"),
        (21, 40, "보통"),
        (41, 60, "길음"),
        (61, float('inf'), "매우 길음")
    ]
    
    print(f"\n📏 길이별 분포")
    for min_len, max_len, label in length_ranges:
        if max_len == float('inf'):
            count = sum(1 for l in question_lengths if l >= min_len)
        else:
            count = sum(1 for l in question_lengths if min_len <= l <= max_len)
        percentage = (count / len(question_lengths)) * 100
        print(f"{label} ({min_len}-{max_len if max_len != float('inf') else '∞'}자): {count}개 ({percentage:.1f}%)")
    
    # 키워드 분석
    print(f"\n🔍 키워드 분석")
    common_keywords = analyze_keywords(all_questions)
    print("가장 자주 사용되는 키워드 (상위 10개):")
    for keyword, count in common_keywords[:10]:
        print(f"  {keyword}: {count}회")
    
    # 의도별 키워드 분석
    print(f"\n🎯 의도별 키워드 분석")
    for intent, examples in dataset.items():
        intent_keywords = analyze_keywords(examples)
        print(f"\n{intent} (상위 5개):")
        for keyword, count in intent_keywords[:5]:
            print(f"  {keyword}: {count}회")
    
    return {
        "total_intents": total_intents,
        "total_examples": total_examples,
        "intent_stats": intent_stats,
        "imbalance_ratio": imbalance_ratio,
        "avg_question_length": avg_length,
        "common_keywords": common_keywords[:10]
    }

def analyze_keywords(questions: List[str]) -> List[Tuple[str, int]]:
    """키워드 분석"""
    # 한국어 불용어
    stopwords = {
        '은', '는', '이', '가', '을', '를', '의', '에', '에서', '로', '으로',
        '와', '과', '도', '만', '까지', '부터', '께서', '한테', '에게',
        '그', '저', '이', '그것', '저것', '이것', '것', '수', '때',
        '있다', '없다', '하다', '되다', '있다', '없다', '않다', '못하다',
        '어떤', '어떻게', '무엇', '뭐', '어디', '언제', '누가', '왜', '어떤',
        '이런', '저런', '그런', '이러한', '저러한', '그러한'
    }
    
    # 키워드 추출
    keywords = []
    for question in questions:
        # 간단한 토큰화 (공백 기준)
        tokens = question.split()
        for token in tokens:
            # 특수문자 제거
            clean_token = ''.join(c for c in token if c.isalnum() or c in '가-힣')
            if clean_token and len(clean_token) > 1 and clean_token not in stopwords:
                keywords.append(clean_token)
    
    # 빈도 계산
    keyword_counts = Counter(keywords)
    return keyword_counts.most_common()

def suggest_improvements(analysis_result: Dict):
    """개선 제안"""
    print(f"\n💡 개선 제안")
    
    # 데이터 불균형 개선 제안
    if analysis_result.get('imbalance_ratio', 0) > 2:
        print("1. 데이터 불균형 개선:")
        print("   - 예시가 적은 의도에 대한 추가 데이터 수집")
        print("   - 데이터 증강 기법 활용")
        print("   - 가중치 기반 학습 고려")
    
    # 질문 길이 다양성 개선 제안
    avg_length = analysis_result.get('avg_question_length', 0)
    if avg_length < 15:
        print("2. 질문 길이 다양성 개선:")
        print("   - 더 상세한 질문 예시 추가")
        print("   - 복합 질문 예시 포함")
    
    # 키워드 다양성 개선 제안
    common_keywords = analysis_result.get('common_keywords', [])
    if len(common_keywords) < 20:
        print("3. 키워드 다양성 개선:")
        print("   - 동의어, 유사어 활용")
        print("   - 다양한 표현 방식 포함")
    
    print("4. 일반적인 개선 사항:")
    print("   - 실제 사용자 질문 패턴 반영")
    print("   - 도메인 특화 용어 추가")
    print("   - 오타, 축약형 등 실제 사용 패턴 포함")

def main():
    """메인 함수"""
    dataset_path = "data/intent_training_dataset.json"
    
    if not os.path.exists(dataset_path):
        print(f"❌ 데이터셋 파일을 찾을 수 없습니다: {dataset_path}")
        return
    
    # 데이터셋 분석
    analysis_result = analyze_dataset(dataset_path)
    
    if analysis_result:
        # 개선 제안
        suggest_improvements(analysis_result)
        
        print(f"\n" + "=" * 60)
        print("✅ 데이터셋 분석 완료!")
        print("=" * 60)
    else:
        print("❌ 데이터셋 분석 실패")

if __name__ == "__main__":
    main()
