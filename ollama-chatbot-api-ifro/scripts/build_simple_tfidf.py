#!/usr/bin/env python3
"""
기본 라이브러리만 사용한 TF-IDF 구현
sklearn 없이 numpy와 기본 라이브러리만 사용
"""

import json
import pickle
import math
import re
from pathlib import Path
from collections import Counter, defaultdict

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

def tokenize(text):
    """간단한 토큰화 (공백 기준)"""
    return text.split()

def build_vocabulary(documents):
    """어휘 사전 구축"""
    vocabulary = set()
    for doc in documents:
        text = preprocess_text(doc['text'])
        tokens = tokenize(text)
        vocabulary.update(tokens)
    return sorted(list(vocabulary))

def calculate_tfidf(documents, vocabulary):
    """TF-IDF 계산"""
    # 문서별 단어 빈도 계산
    doc_freqs = []
    for doc in documents:
        text = preprocess_text(doc['text'])
        tokens = tokenize(text)
        doc_freq = Counter(tokens)
        doc_freqs.append(doc_freq)
    
    # 전체 문서 수
    N = len(documents)
    
    # 단어별 문서 빈도 계산
    word_doc_count = defaultdict(int)
    for doc_freq in doc_freqs:
        for word in doc_freq:
            word_doc_count[word] += 1
    
    # TF-IDF 매트릭스 계산
    tfidf_matrix = []
    for i, doc_freq in enumerate(doc_freqs):
        doc_tfidf = []
        for word in vocabulary:
            # TF 계산
            tf = doc_freq.get(word, 0) / len(doc_freq) if len(doc_freq) > 0 else 0
            
            # IDF 계산
            idf = math.log(N / (word_doc_count[word] + 1)) if word_doc_count[word] > 0 else 0
            
            # TF-IDF 계산
            tfidf = tf * idf
            doc_tfidf.append(tfidf)
        
        tfidf_matrix.append(doc_tfidf)
    
    return tfidf_matrix, vocabulary

def cosine_similarity(vec1, vec2):
    """코사인 유사도 계산"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(a * a for a in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0
    
    return dot_product / (norm1 * norm2)

def search_documents(tfidf_matrix, vocabulary, documents, query, top_k=5):
    """문서 검색"""
    # 쿼리 전처리
    processed_query = preprocess_text(query)
    query_tokens = tokenize(processed_query)
    
    # 쿼리 벡터 생성
    query_vector = [0] * len(vocabulary)
    for token in query_tokens:
        if token in vocabulary:
            idx = vocabulary.index(token)
            query_vector[idx] = 1  # 간단한 이진 벡터
    
    # 각 문서와의 유사도 계산
    similarities = []
    for i, doc_vector in enumerate(tfidf_matrix):
        similarity = cosine_similarity(query_vector, doc_vector)
        similarities.append((similarity, i))
    
    # 상위 결과 정렬
    similarities.sort(reverse=True)
    
    return similarities[:top_k]

def build_tfidf_index(corpus_path, output_dir):
    """TF-IDF 인덱스 구축"""
    print("코퍼스 로딩 중...")
    documents = load_corpus(corpus_path)
    print(f"총 {len(documents)}개 문서 로드됨")
    
    print("어휘 사전 구축 중...")
    vocabulary = build_vocabulary(documents)
    print(f"어휘 사전 크기: {len(vocabulary)}")
    
    print("TF-IDF 매트릭스 계산 중...")
    tfidf_matrix, vocabulary = calculate_tfidf(documents, vocabulary)
    print(f"TF-IDF 매트릭스 크기: {len(tfidf_matrix)} x {len(vocabulary)}")
    
    # 인덱스 저장
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # TF-IDF 매트릭스 저장
    with open(output_dir / 'tfidf_matrix.pkl', 'wb') as f:
        pickle.dump(tfidf_matrix, f)
    
    # 어휘 사전 저장
    with open(output_dir / 'vocabulary.pkl', 'wb') as f:
        pickle.dump(vocabulary, f)
    
    # 문서 메타데이터 저장
    with open(output_dir / 'documents.json', 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"TF-IDF 인덱스가 {output_dir}에 저장되었습니다.")
    return tfidf_matrix, vocabulary, documents

def test_search(tfidf_matrix, vocabulary, documents, query, top_k=5):
    """검색 테스트"""
    print(f"\n검색 쿼리: '{query}'")
    
    results = search_documents(tfidf_matrix, vocabulary, documents, query, top_k)
    
    print(f"상위 {top_k}개 결과:")
    for i, (score, idx) in enumerate(results):
        doc = documents[idx]
        print(f"{i+1}. 점수: {score:.4f}")
        print(f"   파일: {doc['filename']}")
        print(f"   텍스트: {doc['text'][:100]}...")
        print()

if __name__ == "__main__":
    corpus_path = "data/corpus_v1.jsonl"
    output_dir = "data/vector_index"
    
    print("TF-IDF 벡터 인덱스 구축 시작...")
    tfidf_matrix, vocabulary, documents = build_tfidf_index(corpus_path, output_dir)
    
    # 테스트 검색
    test_queries = [
        "교통 정책",
        "도로교통법",
        "대중교통",
        "교통안전",
        "스마트교통"
    ]
    
    for query in test_queries:
        test_search(tfidf_matrix, vocabulary, documents, query)
    
    print("TF-IDF 인덱스 구축 완료!")
