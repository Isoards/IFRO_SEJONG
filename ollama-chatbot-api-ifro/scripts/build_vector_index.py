#!/usr/bin/env python3
"""
기존 corpus 파일을 사용하여 벡터 인덱스를 구축하는 스크립트
"""
import json
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unifiedpdf.config import PipelineConfig
from unifiedpdf.vector_store import make_vector_store
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_corpus(corpus_path: str):
    """corpus 파일을 로드"""
    chunks = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks

def main():
    """메인 함수"""
    corpus_path = "data/corpus_v1.jsonl"
    
    if not os.path.exists(corpus_path):
        logger.error(f"Corpus file not found: {corpus_path}")
        return
    
    # 설정 로드
    cfg = PipelineConfig()
    
    # corpus 로드
    logger.info(f"Loading corpus from {corpus_path}...")
    chunks = load_corpus(corpus_path)
    logger.info(f"Loaded {len(chunks)} chunks")
    
    if not chunks:
        logger.error("No chunks found in corpus")
        return
    
    # 임베딩 모델 로드
    logger.info(f"Loading embedding model: {cfg.embedding_model}")
    embedding_model = SentenceTransformer(cfg.embedding_model)
    
    # 텍스트 추출
    texts = [chunk['text'] for chunk in chunks]
    
    # 임베딩 생성
    logger.info("Generating embeddings...")
    embeddings = embedding_model.encode(texts, show_progress_bar=True)
    
    # 벡터 스토어 생성
    logger.info("Creating vector store...")
    vector_store = make_vector_store(
        embeddings=embeddings,
        texts=texts,
        config=cfg
    )
    
    # 벡터 스토어 저장
    vector_store_dir = Path(cfg.vector_store_dir)
    vector_store_dir.mkdir(exist_ok=True)
    
    logger.info(f"Saving vector store to {vector_store_dir}")
    vector_store.save(str(vector_store_dir))
    
    logger.info("Vector index built successfully!")

if __name__ == "__main__":
    main()