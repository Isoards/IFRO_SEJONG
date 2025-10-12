# 교통량 방향 데이터 구조 개선 방안

## 🎯 현재 문제점

### 1. 과도하게 단순한 방향 분류
- 모든 교차로를 NSEW(동서남북) 4방향으로만 분류
- 실제 도로는 T자형, Y자형, 5거리, 6거리 등 다양한 형태
- 일방통행, 회전교차로 등 특수 상황 미반영

### 2. 실제 도로 상황과 불일치
- 광화문 같은 복잡한 교차로도 단순히 4방향으로만 처리
- 실제 교통 흐름과 데이터 구조가 맞지 않음

## 💡 개선 방안

### 방안 1: 유연한 방향 시스템 (권장)

#### 1.1 새로운 데이터 모델
```python
# models.py
class IntersectionDirection(models.Model):
    """교차로별 방향 정의"""
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE)
    direction_id = models.CharField(max_length=10)  # 'N', 'S', 'E', 'W', 'NE', 'SW' 등
    direction_name = models.CharField(max_length=50)  # '북쪽', '남쪽', '동북쪽' 등
    direction_type = models.CharField(max_length=20, choices=[
        ('straight', '직진'),
        ('left', '좌회전'),
        ('right', '우회전'),
        ('u_turn', '유턴'),
    ])
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # 표시 순서

class TrafficVolume(models.Model):
    """교통량 데이터 - 방향을 외래키로 참조"""
    intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE)
    direction = models.ForeignKey(IntersectionDirection, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    volume = models.IntegerField()
    speed = models.FloatField(null=True, blank=True)
    vehicle_type = models.CharField(max_length=20, choices=[
        ('car', '승용차'),
        ('truck', '화물차'),
        ('bus', '버스'),
        ('motorcycle', '오토바이'),
    ], default='car')
    is_simulated = models.BooleanField(default=False)
```

#### 1.2 교차로별 방향 설정
```python
# 교차로별 방향 설정 예시
def setup_intersection_directions():
    # 광화문 교차로 (복잡한 5거리)
    gwanghwamun = Intersection.objects.get(name="광화문")
    
    directions = [
        {'id': 'N1', 'name': '북쪽(세종대로)', 'type': 'straight'},
        {'id': 'N2', 'name': '북쪽(청계천로)', 'type': 'straight'},
        {'id': 'S1', 'name': '남쪽(세종대로)', 'type': 'straight'},
        {'id': 'S2', 'name': '남쪽(청계천로)', 'type': 'straight'},
        {'id': 'E1', 'name': '동쪽(세종대로)', 'type': 'straight'},
        {'id': 'W1', 'name': '서쪽(세종대로)', 'type': 'straight'},
        {'id': 'NE', 'name': '동북쪽(광화문로)', 'type': 'straight'},
        {'id': 'SW', 'name': '서남쪽(광화문로)', 'type': 'straight'},
    ]
    
    for i, direction in enumerate(directions):
        IntersectionDirection.objects.create(
            intersection=gwanghwamun,
            direction_id=direction['id'],
            direction_name=direction['name'],
            direction_type=direction['type'],
            order=i
        )
```

### 방안 2: 기존 시스템 호환성 유지

#### 2.1 하이브리드 접근법
```python
class TrafficVolume(models.Model):
    # 기존 필드 유지 (호환성)
    direction = models.CharField(max_length=1, choices=DIRECTION_CHOICES)
    
    # 새로운 필드 추가
    detailed_direction = models.CharField(max_length=10, null=True, blank=True)
    road_name = models.CharField(max_length=100, null=True, blank=True)
    movement_type = models.CharField(max_length=20, choices=[
        ('straight', '직진'),
        ('left', '좌회전'),
        ('right', '우회전'),
        ('u_turn', '유턴'),
    ], default='straight')
```

#### 2.2 마이그레이션 전략
```python
# 1단계: 기존 데이터 유지하면서 새 필드 추가
# 2단계: 교차로별 상세 방향 설정
# 3단계: 데이터 마이그레이션
# 4단계: 기존 direction 필드 deprecated 처리
```

### 방안 3: 교차로 유형별 분류

#### 3.1 교차로 유형 정의
```python
class IntersectionType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    direction_count = models.IntegerField()
    direction_pattern = models.JSONField()  # 방향 패턴 정의

# 예시
intersection_types = [
    {
        'name': '4거리',
        'direction_count': 4,
        'direction_pattern': ['N', 'S', 'E', 'W']
    },
    {
        'name': 'T자형',
        'direction_count': 3,
        'direction_pattern': ['N', 'S', 'E']  # 서쪽 막다른길
    },
    {
        'name': 'Y자형',
        'direction_count': 3,
        'direction_pattern': ['N', 'NE', 'NW']
    },
    {
        'name': '5거리',
        'direction_count': 5,
        'direction_pattern': ['N', 'S', 'E', 'W', 'NE']
    }
]
```

## 🚀 구현 단계

### 1단계: 데이터 모델 확장 (1-2주)
- 새로운 모델 추가
- 기존 데이터 호환성 유지
- 마이그레이션 스크립트 작성

### 2단계: 교차로별 방향 설정 (1주)
- 주요 교차로별 상세 방향 설정
- 실제 도로 상황 반영
- 관리자 인터페이스 구축

### 3단계: 데이터 수집 시스템 개선 (2-3주)
- 센서 데이터 연동
- 실시간 방향별 교통량 수집
- 데이터 검증 및 품질 관리

### 4단계: 분석 시스템 업데이트 (2-3주)
- AI 분석 프롬프트 개선
- 방향별 상세 분석
- 정책 제안 정확도 향상

## 📊 예상 효과

### 정확도 향상
- 실제 교통 흐름 반영
- 교차로별 특성 고려
- 정책 제안 신뢰성 증대

### 확장성
- 다양한 교차로 유형 지원
- 미래 교통 시스템 대응
- 국제 표준 호환

### 사용자 경험
- 직관적인 방향 표시
- 정확한 교통 정보
- 신뢰할 수 있는 분석 결과

## ⚠️ 주의사항

### 데이터 마이그레이션
- 기존 데이터 보존
- 점진적 전환
- 롤백 계획 수립

### 성능 영향
- 데이터베이스 인덱스 최적화
- 쿼리 성능 모니터링
- 캐싱 전략 수립

### 호환성
- 기존 API 유지
- 프론트엔드 점진적 업데이트
- 문서화 및 가이드 제공

---

*이 개선 방안은 실제 도로 상황을 반영하여 교통 데이터의 정확성과 신뢰성을 크게 향상시킬 것입니다.*
