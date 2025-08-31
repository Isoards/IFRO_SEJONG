"""
데이터 분석 결과 해석 및 답변 생성 모듈

SQL 쿼리 결과를 분석하여 자연어로 된 인사이트와 답변을 생성
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """분석 결과"""
    total_records: int
    time_period: str
    location: Optional[str]
    metrics: Dict[str, Any]
    insights: List[str]
    trends: List[str]
    summary: str

class DataAnalysisGenerator:
    """데이터 분석 결과 해석 및 답변 생성기"""
    
    def __init__(self):
        """초기화"""
        self.insight_patterns = {
            'high_traffic': {
                'condition': lambda avg: avg > 1000,
                'message': '교통량이 평균적으로 높은 수준입니다.'
            },
            'low_traffic': {
                'condition': lambda avg: avg < 500,
                'message': '교통량이 상대적으로 낮은 수준입니다.'
            },
            'peak_day': {
                'condition': lambda max_val, avg: max_val > avg * 1.5,
                'message': '특정 날짜에 교통량이 급증한 패턴이 보입니다.'
            },
            'consistent_traffic': {
                'condition': lambda std, avg: std < avg * 0.3,
                'message': '교통량이 비교적 일정한 패턴을 보입니다.'
            }
        }
        
        logger.info("데이터 분석 생성기 초기화 완료")
    
    def analyze_sql_results(self, 
                          sql_results: List[Dict], 
                          query_info: Dict,
                          time_range: Dict) -> AnalysisResult:
        """
        SQL 쿼리 결과를 분석
        
        Args:
            sql_results: SQL 쿼리 실행 결과
            query_info: 원본 질문 정보
            time_range: 시간 범위 정보
            
        Returns:
            분석 결과
        """
        logger.info(f"SQL 결과 분석 시작: {len(sql_results)}개 레코드")
        
        if not sql_results:
            return self._create_empty_result(time_range, query_info)
        
        # 1. 기본 통계 계산
        metrics = self._calculate_metrics(sql_results)
        
        # 2. 인사이트 추출
        insights = self._extract_insights(metrics, sql_results)
        
        # 3. 트렌드 분석
        trends = self._analyze_trends(sql_results)
        
        # 4. 요약 생성
        summary = self._generate_summary(metrics, insights, trends, time_range, query_info)
        
        return AnalysisResult(
            total_records=len(sql_results),
            time_period=time_range['description'],
            location=query_info.get('location'),
            metrics=metrics,
            insights=insights,
            trends=trends,
            summary=summary
        )
    
    def _calculate_metrics(self, results: List[Dict]) -> Dict[str, Any]:
        """기본 통계 계산"""
        metrics = {}
        
        # 교통량 관련 지표들
        traffic_columns = ['traffic_volume', 'vehicle_count', 'total_traffic_volume', 'total_vehicle_count']
        accident_columns = ['accident_count', 'incident_count', 'total_accident_count', 'total_incident_count']
        
        # 교통량 통계
        for col in traffic_columns:
            if col in results[0]:
                values = [row[col] for row in results if row[col] is not None]
                if values:
                    metrics[col] = {
                        'total': sum(values),
                        'average': sum(values) / len(values),
                        'maximum': max(values),
                        'minimum': min(values),
                        'count': len(values)
                    }
        
        # 사고 통계
        for col in accident_columns:
            if col in results[0]:
                values = [row[col] for row in results if row[col] is not None]
                if values:
                    metrics[col] = {
                        'total': sum(values),
                        'count': len(values),
                        'average': sum(values) / len(values) if values else 0
                    }
        
        # 날짜별 분석
        if 'date' in results[0]:
            date_values = [row['date'] for row in results if row['date']]
            metrics['date_analysis'] = {
                'start_date': min(date_values) if date_values else None,
                'end_date': max(date_values) if date_values else None,
                'total_days': len(set(date_values)) if date_values else 0
            }
        
        return metrics
    
    def _extract_insights(self, metrics: Dict, results: List[Dict]) -> List[str]:
        """인사이트 추출"""
        insights = []
        
        # 교통량 분석
        for col in ['traffic_volume', 'vehicle_count', 'total_traffic_volume', 'total_vehicle_count']:
            if col in metrics:
                avg = metrics[col]['average']
                max_val = metrics[col]['maximum']
                min_val = metrics[col]['minimum']
                
                # 높은 교통량
                if self.insight_patterns['high_traffic']['condition'](avg):
                    insights.append(f"평균 {col.replace('_', ' ')}: {avg:,.0f}대로 높은 수준")
                
                # 낮은 교통량
                elif self.insight_patterns['low_traffic']['condition'](avg):
                    insights.append(f"평균 {col.replace('_', ' ')}: {avg:,.0f}대로 낮은 수준")
                
                # 피크 패턴
                if self.insight_patterns['peak_day']['condition'](max_val, avg):
                    insights.append(f"최대 {col.replace('_', ' ')}: {max_val:,.0f}대로 평균 대비 {max_val/avg:.1f}배")
        
        # 사고 분석
        for col in ['accident_count', 'incident_count', 'total_accident_count', 'total_incident_count']:
            if col in metrics:
                total = metrics[col]['total']
                if total > 0:
                    insights.append(f"총 {col.replace('_', ' ')}: {total}건")
        
        return insights
    
    def _analyze_trends(self, results: List[Dict]) -> List[str]:
        """트렌드 분석"""
        trends = []
        
        if len(results) < 2:
            return trends
        
        # 날짜별 교통량 트렌드
        if 'date' in results[0]:
            # 날짜별로 정렬
            sorted_results = sorted(results, key=lambda x: x['date'])
            
            # 교통량 컬럼 찾기
            traffic_col = None
            for col in ['traffic_volume', 'vehicle_count', 'total_traffic_volume', 'total_vehicle_count']:
                if col in results[0]:
                    traffic_col = col
                    break
            
            if traffic_col:
                # 첫날과 마지막날 비교
                first_day = sorted_results[0][traffic_col]
                last_day = sorted_results[-1][traffic_col]
                
                if first_day and last_day:
                    change_ratio = (last_day - first_day) / first_day
                    if change_ratio > 0.1:
                        trends.append(f"교통량이 {change_ratio*100:.1f}% 증가하는 추세")
                    elif change_ratio < -0.1:
                        trends.append(f"교통량이 {abs(change_ratio)*100:.1f}% 감소하는 추세")
                    else:
                        trends.append("교통량이 비교적 안정적인 추세")
        
        return trends
    
    def _generate_summary(self, 
                         metrics: Dict, 
                         insights: List[str], 
                         trends: List[str],
                         time_range: Dict,
                         query_info: Dict) -> str:
        """요약 생성"""
        location = query_info.get('location', '전체 지역')
        period = time_range['description']
        
        summary_parts = [f"{location}의 {period} 교통량 정보입니다."]
        
        # 주요 통계 추가
        if 'traffic_volume' in metrics or 'vehicle_count' in metrics:
            for col in ['traffic_volume', 'vehicle_count', 'total_traffic_volume', 'total_vehicle_count']:
                if col in metrics:
                    avg = metrics[col]['average']
                    total = metrics[col]['total']
                    summary_parts.append(f"평균 {col.replace('_', ' ')}: {avg:,.0f}대, 총 {total:,.0f}대")
                    break
        
        # 인사이트 추가
        if insights:
            summary_parts.extend(insights[:3])  # 상위 3개만
        
        # 트렌드 추가
        if trends:
            summary_parts.extend(trends[:2])  # 상위 2개만
        
        return " ".join(summary_parts)
    
    def _create_empty_result(self, time_range: Dict, query_info: Dict) -> AnalysisResult:
        """빈 결과 생성"""
        location = query_info.get('location', '해당 지역')
        period = time_range['description']
        
        return AnalysisResult(
            total_records=0,
            time_period=period,
            location=location,
            metrics={},
            insights=[],
            trends=[],
            summary=f"{location}의 {period} 데이터가 없습니다."
        )
    
    def generate_natural_language_answer(self, 
                                       analysis_result: AnalysisResult,
                                       original_question: str) -> str:
        """
        자연어 답변 생성
        
        Args:
            analysis_result: 분석 결과
            original_question: 원본 질문
            
        Returns:
            자연어 답변
        """
        if analysis_result.total_records == 0:
            return analysis_result.summary
        
        # 기본 답변 구조
        answer_parts = []
        
        # 1. 시간 범위와 위치 정보
        location_info = f"{analysis_result.location}의" if analysis_result.location else "전체 지역의"
        answer_parts.append(f"{location_info} {analysis_result.time_period} 교통량 정보를 분석한 결과입니다.")
        
        # 2. 데이터 개요
        answer_parts.append(f"총 {analysis_result.total_records}개의 데이터를 분석했습니다.")
        
        # 3. 주요 통계
        if analysis_result.metrics:
            traffic_metrics = []
            for col in ['traffic_volume', 'vehicle_count', 'total_traffic_volume', 'total_vehicle_count']:
                if col in analysis_result.metrics:
                    metrics = analysis_result.metrics[col]
                    traffic_metrics.append(f"평균 {col.replace('_', ' ')}: {metrics['average']:,.0f}대")
                    break
            
            if traffic_metrics:
                answer_parts.append(" ".join(traffic_metrics))
        
        # 4. 주요 인사이트
        if analysis_result.insights:
            answer_parts.append("주요 특징:")
            for insight in analysis_result.insights[:3]:  # 상위 3개
                answer_parts.append(f"• {insight}")
        
        # 5. 트렌드 정보
        if analysis_result.trends:
            answer_parts.append("트렌드:")
            for trend in analysis_result.trends[:2]:  # 상위 2개
                answer_parts.append(f"• {trend}")
        
        # 6. 요약
        if analysis_result.summary:
            answer_parts.append(f"\n요약: {analysis_result.summary}")
        
        return "\n".join(answer_parts)
    
    def format_for_display(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        화면 표시용 포맷으로 변환
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            표시용 데이터
        """
        return {
            'summary': analysis_result.summary,
            'total_records': analysis_result.total_records,
            'time_period': analysis_result.time_period,
            'location': analysis_result.location,
            'metrics': analysis_result.metrics,
            'insights': analysis_result.insights,
            'trends': analysis_result.trends,
            'has_data': analysis_result.total_records > 0
        }
