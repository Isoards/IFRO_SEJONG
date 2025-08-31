# 시간 기반 질문 처리 구현 문서

## 개요

"1주전 조치원읍 통행량 정보 요약해줘" 같은 시간 기반 질문에 대해 챗봇이 DB에서 지난주 1주일동안의 통행량을 조회하는 SQL문을 생성해서 DB로 보내서 데이터를 조회하고 분석해서 답변을 생성하는 과정을 구현했습니다.

## 구현된 컴포넌트

### 1. TimeBasedQueryHandler (`core/time_based_query_handler.py`)

시간 기반 질문을 분석하고 적절한 SQL 쿼리를 생성하는 핵심 컴포넌트입니다.

#### 주요 기능:
- **시간 표현 인식**: "1주전", "지난주", "이번달", "어제" 등 한국어 시간 표현 파싱
- **위치 정보 추출**: 세종시 지역명 (조치원읍, 한솔동 등) 인식
- **지표 추출**: 교통량, 사고, 통행량 등 요청된 지표 파싱
- **SQL 템플릿 생성**: 분석 유형에 따른 적절한 SQL 쿼리 생성

#### 지원하는 시간 표현:
```python
time_patterns = {
    '오늘': TimeExpression.TODAY,
    '어제': TimeExpression.YESTERDAY,
    '이번주': TimeExpression.THIS_WEEK,
    '지난주': TimeExpression.LAST_WEEK,
    '1주전': TimeExpression.LAST_WEEK,  # 추가된 패턴
    '이번달': TimeExpression.THIS_MONTH,
    '지난달': TimeExpression.LAST_MONTH,
    '올해': TimeExpression.THIS_YEAR,
    '작년': TimeExpression.LAST_YEAR,
    # ... 기타 패턴들
}
```

#### 지원하는 지역:
```python
location_patterns = {
    '읍': ['조치원읍', '연서면', '연동면', '부강면', '금남면', ...],
    '동': ['한솔동', '새롬동', '도담동', '아름동', '종촌동', ...]
}
```

### 2. DataAnalysisGenerator (`core/data_analysis_generator.py`)

SQL 쿼리 결과를 분석하여 자연어 답변을 생성하는 컴포넌트입니다.

#### 주요 기능:
- **통계 계산**: 평균, 최대, 최소, 총합 등 기본 통계
- **인사이트 추출**: 교통량 패턴, 피크 시간, 트렌드 분석
- **자연어 답변 생성**: 분석 결과를 사용자가 이해하기 쉬운 형태로 변환

#### 분석 지표:
- 교통량 (traffic_volume)
- 차량 수 (vehicle_count)
- 사고 건수 (accident_count)
- 인시던트 건수 (incident_count)

### 3. 메인 시스템 통합

`main.py`와 `api/endpoints.py`에 시간 기반 질문 처리 로직을 통합했습니다.

#### 처리 흐름:
1. **질문 분석**: 시간 기반 질문인지 확인
2. **SQL 생성**: 적절한 SQL 쿼리 생성
3. **DB 조회**: 실제 데이터베이스에서 데이터 조회
4. **데이터 분석**: 조회된 데이터 분석
5. **답변 생성**: 자연어 답변 생성

## 사용 예시

### 입력 질문:
```
"1주전 조치원읍 통행량 정보 요약해줘"
```

### 처리 과정:

#### 1. 시간 기반 질문 파싱
```python
time_result = time_handler.analyze_and_generate_sql(question)
# 결과:
# - 시간 범위: 1주전 (2025-08-18 ~ 2025-08-24)
# - 위치: 조치원읍
# - 지표: traffic_volume, vehicle_count
# - 집계 유형: summary
```

#### 2. SQL 쿼리 생성
```sql
SELECT date, 
       SUM(vehicle_count) as total_vehicle_count,
       AVG(vehicle_count) as avg_vehicle_count,
       MAX(vehicle_count) as max_vehicle_count,
       MIN(vehicle_count) as min_vehicle_count,
       SUM(traffic_volume) as total_traffic_volume,
       AVG(traffic_volume) as avg_traffic_volume,
       MAX(traffic_volume) as max_traffic_volume,
       MIN(traffic_volume) as min_traffic_volume
FROM traffic_trafficvolume 
WHERE date BETWEEN '2025-08-18' AND '2025-08-24' 
  AND region = '조치원읍'
GROUP BY date 
ORDER BY date DESC 
LIMIT 10
```

#### 3. 데이터 분석 결과
```python
analysis_result = {
    'total_records': 7,
    'time_period': '1주전 (2025-08-18 ~ 2025-08-24)',
    'location': '조치원읍',
    'metrics': {
        'traffic_volume': {
            'average': 1282,
            'total': 8976,
            'maximum': 1855,
            'minimum': 850
        }
    },
    'insights': [
        '평균 교통량: 1,282대로 높은 수준',
        '최대 교통량: 1,855대로 평균 대비 1.7배'
    ],
    'trends': [
        '교통량이 49.5% 증가하는 추세'
    ]
}
```

#### 4. 최종 답변
```
조치원읍의 1주전 (2025-08-18 ~ 2025-08-24) 교통량 정보를 분석한 결과입니다.
총 7개의 데이터를 분석했습니다.
평균 교통량: 1,282대

주요 특징:
• 평균 교통량: 1,282대로 높은 수준
• 최대 교통량: 1,855대로 평균 대비 1.7배
• 평균 차량 수: 1,287대로 높은 수준

트렌드:
• 교통량이 49.5% 증가하는 추세

요약: 조치원읍의 1주전 교통량 정보입니다. 평균 교통량: 1,282대, 총 8,976대
```

## 테스트 결과

### 테스트 질문들:
1. "1주전 조치원읍 통행량 정보 요약해줘" ✅
2. "지난주 세종시 교통량 분석" ✅
3. "이번달 한솔동 교통사고 통계" ✅
4. "어제 도담동 교통량" ✅
5. "올해 조치원읍 평균 교통량" ✅
6. "지난달 전체 지역 교통량 비교" ✅
7. "금주 아름동 교통량 상세 정보" ✅
8. "작년 소담동 교통사고 분석" ✅

### 성공률: 100% (8/8)

## 파일 구조

```
ollama-LLM-ChatBot/
├── core/
│   ├── time_based_query_handler.py    # 시간 기반 질문 처리기
│   ├── data_analysis_generator.py     # 데이터 분석 생성기
│   ├── sql_generator.py               # SQL 생성기 (기존)
│   └── ...
├── main.py                            # 메인 시스템 (수정됨)
├── api/
│   └── endpoints.py                   # API 엔드포인트 (수정됨)
├── test_time_based_queries.py         # 시간 기반 질문 테스트
├── test_integration.py                # 통합 테스트
└── TIME_BASED_QUERY_IMPLEMENTATION.md # 이 문서
```

## 실행 방법

### 1. 개별 컴포넌트 테스트
```bash
python test_time_based_queries.py
```

### 2. 통합 테스트
```bash
python test_integration.py
```

### 3. 메인 시스템 실행
```bash
python main.py --mode server
```

## 향후 개선 사항

1. **더 많은 시간 표현 지원**: "3일 전", "지난 월요일" 등
2. **복합 조건 지원**: "1주전 조치원읍 오전 교통량"
3. **비교 분석**: "지난주와 이번주 비교"
4. **예측 기능**: "다음주 교통량 예측"
5. **시각화**: 차트, 그래프 생성

## 결론

시간 기반 질문 처리 기능이 성공적으로 구현되어, 사용자가 "1주전 조치원읍 통행량 정보 요약해줘" 같은 자연어 질문을 하면 시스템이:

1. ✅ 시간 표현을 정확히 파싱
2. ✅ 위치 정보를 추출
3. ✅ 적절한 SQL 쿼리 생성
4. ✅ 데이터베이스에서 데이터 조회
5. ✅ 조회된 데이터 분석
6. ✅ 자연어 답변 생성

이 모든 과정을 자동으로 수행하여 사용자에게 의미 있는 답변을 제공할 수 있게 되었습니다.
