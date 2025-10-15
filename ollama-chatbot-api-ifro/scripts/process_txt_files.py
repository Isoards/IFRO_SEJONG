#!/usr/bin/env python3
"""
TXT 파일을 처리하여 corpus를 생성하는 스크립트
"""
import json
import os
from pathlib import Path
from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """텍스트를 청크로 분할"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        
        if start >= len(text):
            break
    
    return chunks

def process_txt_file(file_path: Path) -> List[Dict]:
    """TXT 파일을 처리하여 청크 리스트 반환"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 청크 생성
    chunks = chunk_text(content)
    
    results = []
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 50:  # 너무 짧은 청크 제외
            continue
            
        results.append({
            "text": chunk.strip(),
            "filename": file_path.name,
            "page": i + 1,
            "start_offset": i * (500 - 100),  # 대략적인 오프셋
            "length": len(chunk.strip())
        })
    
    return results

def main():
    """메인 함수"""
    policy_dir = Path("data/policy_documents")
    corpus_file = Path("data/corpus_v1.jsonl")
    
    # corpus 디렉토리 생성
    corpus_file.parent.mkdir(exist_ok=True)
    
    all_chunks = []
    
    # TXT 파일들 처리
    for txt_file in policy_dir.glob("*.txt"):
        print(f"Processing {txt_file.name}...")
        chunks = process_txt_file(txt_file)
        all_chunks.extend(chunks)
        print(f"  Generated {len(chunks)} chunks")
    
    # corpus 파일에 저장
    with open(corpus_file, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Corpus saved to: {corpus_file}")

if __name__ == "__main__":
    main()
