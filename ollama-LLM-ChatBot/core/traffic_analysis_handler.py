"""
교통정보 해석 핸들러

교통정보 해석 요청을 처리하고 분석 결과를 제공하는 모듈
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re
from datetime import datetime, timedelta
from enum import Enum
from .sql_slot_extractor import SQLSlotExtractor, SlotExtractionResult

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """분석 유형"""
    TRAFFIC_VOLUME = "traffic_volume"
    ACCIDENT_PATTERN = "accident_pattern"
    INTERSECTION_ANALYSIS = "intersection_analysis"
    TIME_PATTERN = "time_pattern"
    REGIONAL_COMPARISON = "regional_comparison"
    GENERAL_ANALYSIS = "general_analysis"

@dataclass
class AnalysisRequest:
    """분석 요청 데이터"""
    question: str
    analysis_type: AnalysisType
    target_data: Optional[Dict] = None
    time_range: Optional[Dict] = None
    location: Optional[str] = None
    metrics: Optional[List[str]] = None

@dataclass
class AnalysisResult:
    """분석 결과"""
    summary: str
    details: List[str]
    insights: List[str]
    recommendations: List[str]
    data_points: Optional[Dict] = None

class TrafficAnalysisHandler:
    """
    교통정보 해석 핸들러
    
    교통정보 해석 요청을 처리하고 의미있는 분석 결과를 제공
    """
    
    def __init__(self, sql_generator=None, answer_generator=None):
        """
        초기화
        
        Args:
            sql_generator: SQL 생성기 (데이터 조회용)
            answer_generator: 답변 생성기 (LLM 기반 분석용)
        """
        self.sql_generator = sql_generator
        self.answer_generator = answer_generator
        self.sql_slot_extractor = SQLSlotExtractor()
        
        # 분석 유형별 키워드 매핑
        self.analysis_keywords = {
            AnalysisType.TRAFFIC_VOLUME: [
                '교통량', '통행량', '차량', '교통 흐름', '혼잡도'
            ],
            AnalysisType.ACCIDENT_PATTERN: [
                '사고', '교통사고', '사고 패턴', '위험', '안전'
            ],
            AnalysisType.INTERSECTION_ANALYSIS: [
                '교차로', '신호등', '교차점', '정체'
            ],
            AnalysisType.TIME_PATTERN: [
                '시간', '시간대', '피크', '패턴', '변화'
            ],
            AnalysisType.REGIONAL_COMPARISON: [
                '지역', '구별', '비교', '순위', '상위', '하위'
            ]
        }
        
        logger.info("교통정보 해석 핸들러 초기화 완료")
    
    def analyze_request(self, question: str, context: Optional[Dict] = None) -> AnalysisRequest:
        """
        분석 요청을 파싱하고 구조화
        
        Args:
            question: 사용자 질문
            context: 추가 컨텍스트 정보
            
        Returns:
            구조화된 분석 요청
        """
        question_lower = question.lower()
        
        # 분석 유형 결정
        analysis_type = self._determine_analysis_type(question_lower)
        
        # 시간 범위 추출
        time_range = self._extract_time_range(question)
        
        # 위치 정보 추출
        location = self._extract_location(question)
        
        # 메트릭 추출
        metrics = self._extract_metrics(question)
        
        return AnalysisRequest(
            question=question,
            analysis_type=analysis_type,
            time_range=time_range,
            location=location,
            metrics=metrics
        )
    
    def _determine_analysis_type(self, question: str) -> AnalysisType:
        """분석 유형 결정"""
        for analysis_type, keywords in self.analysis_keywords.items():
            if any(keyword in question for keyword in keywords):
                return analysis_type
        
        return AnalysisType.GENERAL_ANALYSIS
    
    def _extract_time_range(self, question: str) -> Optional[Dict]:
        """시간 범위 추출"""
        # 한국어 시간 표현 패턴
        time_patterns = {
            '오늘': {'start': 'today', 'end': 'today'},
            '어제': {'start': 'yesterday', 'end': 'yesterday'},
            '이번주': {'start': 'this_week', 'end': 'this_week'},
            '지난주': {'start': 'last_week', 'end': 'last_week'},
            '이번달': {'start': 'this_month', 'end': 'this_month'},
            '지난달': {'start': 'last_month', 'end': 'last_month'},
            '올해': {'start': 'this_year', 'end': 'this_year'},
            '작년': {'start': 'last_year', 'end': 'last_year'}
        }
        
        for pattern, time_range in time_patterns.items():
            if pattern in question:
                return self._resolve_time_range(time_range)
        
        return None
    
    def _resolve_time_range(self, time_range: Dict) -> Dict:
        """시간 범위를 실제 날짜로 변환"""
        now = datetime.now()
        
        if time_range['start'] == 'today':
            return {
                'start': now.strftime('%Y-%m-%d'),
                'end': now.strftime('%Y-%m-%d')
            }
        elif time_range['start'] == 'yesterday':
            yesterday = now - timedelta(days=1)
            return {
                'start': yesterday.strftime('%Y-%m-%d'),
                'end': yesterday.strftime('%Y-%m-%d')
            }
        elif time_range['start'] == 'this_week':
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return {
                'start': start_of_week.strftime('%Y-%m-%d'),
                'end': end_of_week.strftime('%Y-%m-%d')
            }
        elif time_range['start'] == 'last_week':
            start_of_last_week = now - timedelta(days=now.weekday() + 7)
            end_of_last_week = start_of_last_week + timedelta(days=6)
            return {
                'start': start_of_last_week.strftime('%Y-%m-%d'),
                'end': end_of_last_week.strftime('%Y-%m-%d')
            }
        elif time_range['start'] == 'this_month':
            start_of_month = now.replace(day=1)
            return {
                'start': start_of_month.strftime('%Y-%m-%d'),
                'end': now.strftime('%Y-%m-%d')
            }
        elif time_range['start'] == 'last_month':
            if now.month == 1:
                last_month = now.replace(year=now.year-1, month=12)
            else:
                last_month = now.replace(month=now.month-1)
            start_of_last_month = last_month.replace(day=1)
            return {
                'start': start_of_last_month.strftime('%Y-%m-%d'),
                'end': last_month.strftime('%Y-%m-%d')
            }
        
        return time_range
    
    def _extract_location(self, question: str) -> Optional[str]:
        """위치 정보 추출"""
        # 세종시 동/읍 패턴
        location_patterns = [
            r'([가-힣]+동)',  # 동 패턴
            r'([가-힣]+읍)',  # 읍 패턴
            r'([가-힣]+면)',  # 면 패턴
            r'세종특별자치시([가-힣]+)',  # 세종특별자치시 패턴
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, question)
            if match:
                location = match.group(1)
                
                # 세종특별자치시 접두사 제거
                if location.startswith('세종특별자치시'):
                    location = location.replace('세종특별자치시', '')
                
                # 교차로 매핑 확인
                if self._is_intersection_name(location):
                    return self._get_region_from_intersection(location)
                
                return location
        
        return None
    
    def _is_intersection_name(self, location: str) -> bool:
        """교차로 이름인지 확인"""
        # 세종특별자치시 형식의 교차로 이름 패턴
        intersection_patterns = [
            r'세종특별자치시[가-힣]+\(\d+\)',  # 세종특별자치시조치원읍(1) 형식
            r'세종특별자치시[가-힣]+',  # 세종특별자치시조치원읍 형식
        ]
        
        for pattern in intersection_patterns:
            if re.match(pattern, location):
                return True
        
        return False
    
    def _get_region_from_intersection(self, intersection_name: str) -> str:
        """교차로명에서 지역명 추출"""
        # 교차로 매핑 테이블 (MovementHandler와 동일)
        intersection_mapping = {
            # 조치원읍 교차로들
            "세종특별자치시조치원읍": "조치원읍",
            "세종특별자치시조치원읍(1)": "조치원읍",
            "세종특별자치시조치원읍(2)": "조치원읍",
            "세종특별자치시조치원읍(3)": "조치원읍",
            "세종특별자치시조치원읍(4)": "조치원읍",
            "세종특별자치시조치원읍(5)": "조치원읍",
            "세종특별자치시조치원읍(6)": "조치원읍",
            "세종특별자치시조치원읍(7)": "조치원읍",
            "세종특별자치시조치원읍(8)": "조치원읍",
            "세종특별자치시조치원읍(9)": "조치원읍",
            "세종특별자치시조치원읍(10)": "조치원읍",
            
            # 연기면 교차로들
            "세종특별자치시연기면": "연기면",
            "세종특별자치시연기면(1)": "연기면",
            "세종특별자치시연기면(2)": "연기면",
            "세종특별자치시연기면(3)": "연기면",
            "세종특별자치시연기면(4)": "연기면",
            "세종특별자치시연기면(5)": "연기면",
            
            # 연동면 교차로들
            "세종특별자치시연동면": "연동면",
            "세종특별자치시연동면(1)": "연동면",
            "세종특별자치시연동면(2)": "연동면",
            "세종특별자치시연동면(3)": "연동면",
            "세종특별자치시연동면(4)": "연동면",
            "세종특별자치시연동면(5)": "연동면",
            "세종특별자치시연동면(6)": "연동면",
            "세종특별자치시연동면(7)": "연동면",
            "세종특별자치시연동면(8)": "연동면",
            "세종특별자치시연동면(9)": "연동면",
            "세종특별자치시연동면(10)": "연동면",
            
            # 부강면 교차로들
            "세종특별자치시부강면": "부강면",
            "세종특별자치시부강면(1)": "부강면",
            "세종특별자치시부강면(2)": "부강면",
            "세종특별자치시부강면(3)": "부강면",
            "세종특별자치시부강면(4)": "부강면",
            "세종특별자치시부강면(5)": "부강면",
            "세종특별자치시부강면(6)": "부강면",
            "세종특별자치시부강면(7)": "부강면",
            "세종특별자치시부강면(8)": "부강면",
            "세종특별자치시부강면(9)": "부강면",
            "세종특별자치시부강면(10)": "부강면",
            
            # 금남면 교차로들
            "세종특별자치시금남면": "금남면",
            "세종특별자치시금남면(1)": "금남면",
            "세종특별자치시금남면(2)": "금남면",
            "세종특별자치시금남면(3)": "금남면",
            "세종특별자치시금남면(4)": "금남면",
            "세종특별자치시금남면(5)": "금남면",
            "세종특별자치시금남면(6)": "금남면",
            "세종특별자치시금남면(7)": "금남면",
            "세종특별자치시금남면(8)": "금남면",
            "세종특별자치시금남면(9)": "금남면",
            "세종특별자치시금남면(10)": "금남면",
            
            # 장군면 교차로들
            "세종특별자치시장군면": "장군면",
            "세종특별자치시장군면(1)": "장군면",
            "세종특별자치시장군면(2)": "장군면",
            "세종특별자치시장군면(3)": "장군면",
            "세종특별자치시장군면(4)": "장군면",
            "세종특별자치시장군면(5)": "장군면",
            "세종특별자치시장군면(6)": "장군면",
            "세종특별자치시장군면(7)": "장군면",
            "세종특별자치시장군면(8)": "장군면",
            "세종특별자치시장군면(9)": "장군면",
            "세종특별자치시장군면(10)": "장군면",
            
            # 연서면 교차로들
            "세종특별자치시연서면": "연서면",
            "세종특별자치시연서면(1)": "연서면",
            "세종특별자치시연서면(2)": "연서면",
            "세종특별자치시연서면(3)": "연서면",
            "세종특별자치시연서면(4)": "연서면",
            "세종특별자치시연서면(5)": "연서면",
            "세종특별자치시연서면(6)": "연서면",
            "세종특별자치시연서면(7)": "연서면",
            "세종특별자치시연서면(8)": "연서면",
            "세종특별자치시연서면(9)": "연서면",
            "세종특별자치시연서면(10)": "연서면",
            
            # 전의면 교차로들
            "세종특별자치시전의면": "전의면",
            "세종특별자치시전의면(1)": "전의면",
            "세종특별자치시전의면(2)": "전의면",
            "세종특별자치시전의면(3)": "전의면",
            "세종특별자치시전의면(4)": "전의면",
            "세종특별자치시전의면(5)": "전의면",
            "세종특별자치시전의면(6)": "전의면",
            "세종특별자치시전의면(7)": "전의면",
            "세종특별자치시전의면(8)": "전의면",
            "세종특별자치시전의면(9)": "전의면",
            "세종특별자치시전의면(10)": "전의면",
            
            # 전동면 교차로들
            "세종특별자치시전동면": "전동면",
            "세종특별자치시전동면(1)": "전동면",
            "세종특별자치시전동면(2)": "전동면",
            "세종특별자치시전동면(3)": "전동면",
            "세종특별자치시전동면(4)": "전동면",
            "세종특별자치시전동면(5)": "전동면",
            "세종특별자치시전동면(6)": "전동면",
            "세종특별자치시전동면(7)": "전동면",
            "세종특별자치시전동면(8)": "전동면",
            "세종특별자치시전동면(9)": "전동면",
            "세종특별자치시전동면(10)": "전동면",
            
            # 소정면 교차로들
            "세종특별자치시소정면": "소정면",
            "세종특별자치시소정면(1)": "소정면",
            "세종특별자치시소정면(2)": "소정면",
            "세종특별자치시소정면(3)": "소정면",
            "세종특별자치시소정면(4)": "소정면",
            "세종특별자치시소정면(5)": "소정면",
            "세종특별자치시소정면(6)": "소정면",
            "세종특별자치시소정면(7)": "소정면",
            "세종특별자치시소정면(8)": "소정면",
            "세종특별자치시소정면(9)": "소정면",
            "세종특별자치시소정면(10)": "소정면",
            
            # 동 지역 교차로들
            "세종특별자치시한솔동": "한솔동",
            "세종특별자치시새롬동": "새롬동",
            "세종특별자치시도담동": "도담동",
            "세종특별자치시아름동": "아름동",
            "세종특별자치시종촌동": "종촌동",
            "세종특별자치시고운동": "고운동",
            "세종특별자치시소담동": "소담동",
            "세종특별자치시보람동": "보람동",
            "세종특별자치시대평동": "대평동",
            "세종특별자치시다정동": "다정동",
            "세종특별자치시어진동": "어진동",
            "세종특별자치시반곡동": "반곡동",
            "세종특별자치시가람동": "가람동",
            "세종특별자치시한별동": "한별동",
            "세종특별자치시새아름동": "새아름동"
        }
        
        return intersection_mapping.get(intersection_name, intersection_name)
    
    def _extract_metrics(self, question: str) -> List[str]:
        """분석 메트릭 추출"""
        metrics = []
        
        metric_keywords = {
            '평균': 'average',
            '총합': 'sum',
            '최대': 'max',
            '최소': 'min',
            '개수': 'count',
            '비율': 'ratio',
            '증감': 'change'
        }
        
        for keyword, metric in metric_keywords.items():
            if keyword in question:
                metrics.append(metric)
        
        return metrics
    
    def process_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        분석 요청 처리
        
        Args:
            request: 분석 요청
            
        Returns:
            분석 결과
        """
        try:
            # 1. 데이터 수집
            data = self._collect_data(request)
            
            # 2. 분석 수행
            analysis = self._perform_analysis(request, data)
            
            # 3. 결과 생성
            result = self._generate_result(request, analysis)
            
            return result
            
        except Exception as e:
            logger.error(f"분석 처리 중 오류: {e}")
            return AnalysisResult(
                summary="분석 중 오류가 발생했습니다.",
                details=[f"오류 내용: {str(e)}"],
                insights=[],
                recommendations=["다시 시도해주세요."]
            )
    
    def _collect_data(self, request: AnalysisRequest) -> Dict:
        """분석에 필요한 데이터 수집"""
        try:
            # SQL 슬롯 추출을 통한 정확한 쿼리 생성
            slot_result = self.sql_slot_extractor.extract_slots(request.question)
            
            if slot_result.slots:
                # 슬롯 기반 SQL 쿼리 생성
                sql_query = self.sql_slot_extractor.generate_sql_from_slots(slot_result.slots)
                
                # SQL 검증
                is_valid, validation_message = self.sql_slot_extractor.validate_sql(sql_query)
                
                if is_valid and self.sql_generator:
                    # 실제 SQL 실행 (실제 구현에서는 DB 연결 필요)
                    # execution_result = self.sql_generator.execute_sql(sql_query)
                    # return execution_result.get('data', {})
                    pass
                
                logger.info(f"생성된 SQL: {sql_query}")
                logger.info(f"슬롯 추출 결과: {slot_result.reasoning}")
            
            # 임시 더미 데이터 반환 (실제 구현에서는 제거)
            return self._get_dummy_data(request)
            
        except Exception as e:
            logger.error(f"데이터 수집 중 오류: {e}")
            return {}
    
    def _generate_base_query(self, request: AnalysisRequest) -> str:
        """기본 데이터 조회 쿼리 생성"""
        query_parts = ["SELECT * FROM traffic_data"]
        conditions = []
        
        if request.time_range:
            conditions.append(
                f"date BETWEEN '{request.time_range['start']}' AND '{request.time_range['end']}'"
            )
        
        if request.location:
            conditions.append(f"location LIKE '%{request.location}%'")
        
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        return " ".join(query_parts)
    
    def _get_dummy_data(self, request: AnalysisRequest) -> Dict:
        """임시 더미 데이터 (실제 구현에서는 제거)"""
        return {
            'traffic_volume': {
                'total': 125000,
                'average': 4167,
                'peak_hour': 8500,
                'off_peak': 2000
            },
            'accidents': {
                'total': 45,
                'severe': 12,
                'minor': 33
            },
            'locations': {
                '강남구': {'volume': 25000, 'accidents': 8},
                '서초구': {'volume': 22000, 'accidents': 6},
                '송파구': {'volume': 20000, 'accidents': 5}
            }
        }
    
    def _perform_analysis(self, request: AnalysisRequest, data: Dict) -> Dict:
        """실제 분석 수행"""
        analysis = {
            'type': request.analysis_type.value,
            'data': data,
            'insights': []
        }
        
        if request.analysis_type == AnalysisType.TRAFFIC_VOLUME:
            analysis['insights'] = self._analyze_traffic_volume(data)
        elif request.analysis_type == AnalysisType.ACCIDENT_PATTERN:
            analysis['insights'] = self._analyze_accident_pattern(data)
        elif request.analysis_type == AnalysisType.INTERSECTION_ANALYSIS:
            analysis['insights'] = self._analyze_intersection(data)
        else:
            analysis['insights'] = self._analyze_general(data)
        
        return analysis
    
    def _analyze_traffic_volume(self, data: Dict) -> List[str]:
        """교통량 분석"""
        insights = []
        
        if 'traffic_volume' in data:
            vol = data['traffic_volume']
            
            # 피크 시간대 분석
            peak_ratio = vol['peak_hour'] / vol['average']
            if peak_ratio > 1.5:
                insights.append(f"피크 시간대 교통량이 평균보다 {peak_ratio:.1f}배 높아 심각한 혼잡이 예상됩니다.")
            
            # 전반적 교통량 수준
            if vol['average'] > 5000:
                insights.append("전반적으로 높은 교통량을 보이고 있습니다.")
            elif vol['average'] < 2000:
                insights.append("교통량이 상대적으로 낮은 편입니다.")
        
        return insights
    
    def _analyze_accident_pattern(self, data: Dict) -> List[str]:
        """사고 패턴 분석"""
        insights = []
        
        if 'accidents' in data:
            acc = data['accidents']
            
            # 심각 사고 비율
            severe_ratio = acc['severe'] / acc['total'] if acc['total'] > 0 else 0
            if severe_ratio > 0.3:
                insights.append(f"심각 사고 비율이 {severe_ratio:.1%}로 높아 안전 관리가 필요합니다.")
            
            # 전반적 사고 수준
            if acc['total'] > 50:
                insights.append("전반적으로 높은 사고 발생률을 보이고 있습니다.")
        
        return insights
    
    def _analyze_intersection(self, data: Dict) -> List[str]:
        """교차로 분석"""
        insights = []
        
        if 'locations' in data:
            locations = data['locations']
            
            # 교통량 대비 사고율 계산
            for location, info in locations.items():
                if info['volume'] > 0:
                    accident_rate = info['accidents'] / (info['volume'] / 1000)  # 1000대당 사고율
                    if accident_rate > 0.5:
                        insights.append(f"{location}는 교통량 대비 높은 사고율을 보입니다.")
        
        return insights
    
    def _analyze_general(self, data: Dict) -> List[str]:
        """일반 분석"""
        insights = []
        
        if data:
            insights.append("전반적인 교통 상황을 분석한 결과입니다.")
            
            if 'traffic_volume' in data:
                insights.append(f"총 교통량: {data['traffic_volume']['total']:,}대")
            
            if 'accidents' in data:
                insights.append(f"총 사고 건수: {data['accidents']['total']}건")
        
        return insights
    
    def _generate_result(self, request: AnalysisRequest, analysis: Dict) -> AnalysisResult:
        """최종 결과 생성"""
        # 요약 생성
        summary = self._generate_summary(request, analysis)
        
        # 상세 내용
        details = self._generate_details(analysis)
        
        # 인사이트
        insights = analysis.get('insights', [])
        
        # 권장사항
        recommendations = self._generate_recommendations(request, analysis)
        
        return AnalysisResult(
            summary=summary,
            details=details,
            insights=insights,
            recommendations=recommendations,
            data_points=analysis.get('data', {})
        )
    
    def _generate_summary(self, request: AnalysisRequest, analysis: Dict) -> str:
        """요약 생성"""
        analysis_type = request.analysis_type.value
        
        if analysis_type == 'traffic_volume':
            return "교통량 분석 결과를 제공합니다."
        elif analysis_type == 'accident_pattern':
            return "교통사고 패턴 분석 결과를 제공합니다."
        elif analysis_type == 'intersection_analysis':
            return "교차로별 분석 결과를 제공합니다."
        else:
            return "교통정보 종합 분석 결과를 제공합니다."
    
    def _generate_details(self, analysis: Dict) -> List[str]:
        """상세 내용 생성"""
        details = []
        data = analysis.get('data', {})
        
        if 'traffic_volume' in data:
            vol = data['traffic_volume']
            details.append(f"• 총 교통량: {vol['total']:,}대")
            details.append(f"• 평균 교통량: {vol['average']:,}대/일")
            details.append(f"• 피크 시간대: {vol['peak_hour']:,}대")
        
        if 'accidents' in data:
            acc = data['accidents']
            details.append(f"• 총 사고 건수: {acc['total']}건")
            details.append(f"• 심각 사고: {acc['severe']}건")
            details.append(f"• 경미 사고: {acc['minor']}건")
        
        return details
    
    def _generate_recommendations(self, request: AnalysisRequest, analysis: Dict) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        data = analysis.get('data', {})
        
        if 'traffic_volume' in data:
            vol = data['traffic_volume']
            if vol['peak_hour'] / vol['average'] > 1.5:
                recommendations.append("피크 시간대 교통량 분산을 위한 정책 검토가 필요합니다.")
        
        if 'accidents' in data:
            acc = data['accidents']
            if acc['severe'] / acc['total'] > 0.3:
                recommendations.append("안전 시설 개선 및 교통 안전 교육 강화가 필요합니다.")
        
        if not recommendations:
            recommendations.append("현재 교통 상황을 지속적으로 모니터링하시기 바랍니다.")
        
        return recommendations
