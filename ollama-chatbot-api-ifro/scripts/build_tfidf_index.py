#!/usr/bin/env python3
"""
TF-IDF 벡터 인덱스 구축 스크립트
sentence-transformers 없이 기본 라이브러리만 사용
"""

import json
import pickle
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

def load_corpus(corpus_path):
    """코퍼스 파일 로드"""
    documents = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                doc = json.loads(line)
                documents.append(doc)
    return documents

def preprocess_text(text):
    """텍스트 전처리"""
    # 한글, 영문, 숫자만 유지
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text)
    # 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_tfidf_index(corpus_path, output_dir):
    """TF-IDF 인덱스 구축"""
    print("코퍼스 로딩 중...")
    documents = load_corpus(corpus_path)
    print(f"총 {len(documents)}개 문서 로드됨")
    
    # 텍스트 추출 및 전처리
    texts = []
    for doc in documents:
        text = preprocess_text(doc['text'])
        texts.append(text)
    
    print("TF-IDF 벡터화 중...")
    # TF-IDF 벡터화 (한글 처리 최적화)
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
        stop_words=None  # 한글 불용어는 별도 처리 필요시 추가
    )
    
    tfidf_matrix = vectorizer.fit_transform(texts)
    print(f"TF-IDF 매트릭스 크기: {tfidf_matrix.shape}")
    
    # 인덱스 저장
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # TF-IDF 매트릭스 저장
    with open(output_dir / 'tfidf_matrix.pkl', 'wb') as f:
        pickle.dump(tfidf_matrix, f)
    
    # 벡터라이저 저장
    with open(output_dir / 'tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    
    # 문서 메타데이터 저장
    with open(output_dir / 'documents.json', 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"TF-IDF 인덱스가 {output_dir}에 저장되었습니다.")
    return tfidf_matrix, vectorizer, documents

def test_search(tfidf_matrix, vectorizer, documents, query, top_k=5):
    """검색 테스트"""
    print(f"\n검색 쿼리: '{query}'")
    
    # 쿼리 전처리
    processed_query = preprocess_text(query)
    
    # 쿼리 벡터화
    query_vector = vectorizer.transform([processed_query])
    
    # 코사인 유사도 계산
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    # 상위 결과 추출
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    print(f"상위 {top_k}개 결과:")
    for i, idx in enumerate(top_indices):
        score = similarities[idx]
        doc = documents[idx]
        print(f"{i+1}. 점수: {score:.4f}")
        print(f"   파일: {doc['filename']}")
        print(f"   텍스트: {doc['text'][:100]}...")
        print()

if __name__ == "__main__":
    corpus_path = "data/corpus_v1.jsonl"
    output_dir = "data/vector_index"
    
    print("TF-IDF 벡터 인덱스 구축 시작...")
    tfidf_matrix, vectorizer, documents = build_tfidf_index(corpus_path, output_dir)
    
    # 테스트 검색
    test_queries = [
        "교통 정책",
        "도로교통법",
        "대중교통",
        "교통안전",
        "스마트교통"
    ]
    
    for query in test_queries:
        test_search(tfidf_matrix, vectorizer, documents, query)
    
    print("TF-IDF 인덱스 구축 완료!")