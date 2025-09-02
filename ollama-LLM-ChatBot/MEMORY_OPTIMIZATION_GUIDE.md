# AI 모델 메모리 최적화 가이드

## 개요

이 문서는 AI 모델의 메모리 관리 문제를 해결하기 위한 종합적인 최적화 방안을 설명합니다.

## 주요 문제점

1. **AI 모델들이 메모리에 계속 로드되어 OOM 위험**
2. **메모리 누수 가능성 (특히 PyTorch 모델)**
3. **대용량 PDF 처리 시 메모리 폭증 위험**

## 해결 방안

### 1. 메모리 최적화 시스템

#### 1.1 LRU 캐시 기반 모델 관리
- 사용 빈도가 낮은 모델을 자동으로 언로드
- 우선순위 기반 모델 관리
- 메모리 압박 시 자동 정리

#### 1.2 지연 로딩 (Lazy Loading)
- 필요할 때만 모델 로드
- 메모리 사용량 최소화
- 빠른 응답 시간 보장

#### 1.3 메모리 모니터링
- 실시간 메모리 사용량 추적
- 임계치 기반 자동 정리
- 메모리 프로파일링

### 2. PDF 처리 최적화

#### 2.1 배치 처리
- 메모리 제한을 고려한 배치 크기 조정
- 청크 단위 처리로 메모리 사용량 제어
- 점진적 처리로 메모리 폭증 방지

#### 2.2 메모리 제한 설정
- PDF 처리 시 최대 메모리 사용량 제한
- 자동 메모리 정리
- 오류 발생 시 안전한 복구

### 3. PyTorch 모델 최적화

#### 3.1 float16 사용
- 메모리 사용량 50% 절약
- 성능 저하 최소화
- GPU 메모리 효율성 향상

#### 3.2 GPU 캐시 정리
- 자동 GPU 메모리 정리
- 메모리 누수 방지
- 효율적인 리소스 관리

## 설정 방법

### 환경 변수 설정

```bash
# 메모리 최적화 환경 변수
export MAX_MODEL_MEMORY_GB=8.0
export MEMORY_WARNING_THRESHOLD=75.0
export MEMORY_CRITICAL_THRESHOLD=85.0
export PDF_MAX_MEMORY_GB=2.0
export MEMORY_MONITORING_INTERVAL=30.0
export ENABLE_AUTO_CLEANUP=true
```

### Docker 설정

```yaml
# docker-compose.yml
services:
  chatbot:
    environment:
      - MAX_MODEL_MEMORY_GB=8.0
      - MEMORY_WARNING_THRESHOLD=75.0
      - MEMORY_CRITICAL_THRESHOLD=85.0
      - PDF_MAX_MEMORY_GB=2.0
    deploy:
      resources:
        limits:
          memory: 12G
          cpus: '4.0'
        reservations:
          memory: 8G
          cpus: '2.0'
```

## API 엔드포인트

### 메모리 상태 확인
```bash
GET /memory/status
```

### 메모리 최적화 실행
```bash
POST /memory/optimize
```

### 로드된 모델 목록
```bash
GET /memory/models
```

### 특정 모델 언로드
```bash
DELETE /memory/models/{model_name}
```

## 모니터링 및 로깅

### 메모리 사용량 모니터링
- 30초마다 메모리 상태 확인
- 임계치 초과 시 자동 정리
- 상세한 메모리 프로파일링

### 로그 레벨 설정
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 성능 최적화 팁

### 1. 모델 우선순위 설정
```python
model_priorities = {
    "paust/pko-t5-small": 1,  # 핵심 모델
    "jhgan/ko-sroberta-multitask": 1,  # 핵심 모델
    "defog/sqlcoder-7b-2": 2  # 선택적 모델
}
```

### 2. 배치 크기 조정
```python
# 메모리 제한을 고려한 배치 크기 계산
batch_size = min(16, total_chunks)
```

### 3. 메모리 정리 주기
```python
# 30초마다 메모리 상태 확인
monitoring_interval = 30.0
```

## 문제 해결

### 1. OOM 오류 발생 시
1. 메모리 사용량 확인: `GET /memory/status`
2. 불필요한 모델 언로드: `DELETE /memory/models/{model_name}`
3. 메모리 최적화 실행: `POST /memory/optimize`

### 2. PDF 처리 실패 시
1. PDF 파일 크기 확인
2. 메모리 제한 조정
3. 배치 크기 축소

### 3. 모델 로딩 실패 시
1. 모델 캐시 확인
2. 메모리 여유 공간 확인
3. 다른 모델 언로드 후 재시도

## 모니터링 대시보드

메모리 상태를 실시간으로 모니터링할 수 있는 대시보드 정보:

- 시스템 메모리 사용량
- 모델별 메모리 사용량
- PDF 처리 메모리 사용량
- 메모리 정리 이력
- 성능 지표

## 성능 지표

### 메모리 사용량 목표
- 시스템 메모리: 75% 이하
- 모델 메모리: 8GB 이하
- PDF 처리 메모리: 2GB 이하

### 응답 시간 목표
- 모델 로딩: 30초 이하
- PDF 처리: 5분 이하 (100MB 파일 기준)
- 메모리 정리: 10초 이하

## 결론

이 메모리 최적화 시스템을 통해 다음과 같은 효과를 얻을 수 있습니다:

1. **OOM 위험 대폭 감소**: 자동 메모리 관리로 안정성 향상
2. **성능 향상**: 지연 로딩과 배치 처리로 응답 시간 개선
3. **리소스 효율성**: 메모리 사용량 최적화로 비용 절약
4. **운영 편의성**: 실시간 모니터링과 자동 정리로 관리 부담 감소

## 추가 정보

- [메모리 최적화 유틸리티](../core/utils/memory_optimizer.py)
- [PDF 처리기](../core/document/pdf_processor.py)
- [답변 생성기](../core/llm/answer_generator.py)
- [메모리 설정](../core/config/memory_config.py)
