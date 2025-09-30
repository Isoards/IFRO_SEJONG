"""
SQL 데이터베이스 연동 모듈
교통 데이터베이스에서 실시간 데이터를 조회하여 답변에 활용
"""
import mysql.connector
import logging
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class TrafficDataAnalyzer:
    """교통 데이터 분석 클래스"""
    
    def __init__(self, host='db', user='root', password='1234', database='traffic'):
        """데이터베이스 연결 설정"""
        self.connection_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4'
        }
        self.connection = None
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = mysql.connector.connect(**self.connection_config)
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
    
    def get_traffic_incidents_by_district(self, limit=10) -> List[Dict]:
        """구별 교통사고 통계 조회"""
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT district, COUNT(*) as incident_count 
            FROM traffic_incident 
            GROUP BY district 
            ORDER BY incident_count DESC 
            LIMIT %s
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            cursor.close()
            
            return results
        except Exception as e:
            logger.error(f"교통사고 통계 조회 실패: {e}")
            return []
    
    def get_incident_types(self) -> List[Dict]:
        """사고 유형별 통계 조회"""
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT type, COUNT(*) as count 
            FROM traffic_incident 
            GROUP BY type 
            ORDER BY count DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            return results
        except Exception as e:
            logger.error(f"사고 유형 통계 조회 실패: {e}")
            return []
    
    def get_recent_incidents(self, limit=5) -> List[Dict]:
        """최근 교통사고 조회"""
        try:
            if not self.connection:
                if not self.connect():
                    return []
            
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT intersection_name, district, type, status, registered_at 
            FROM traffic_incident 
            ORDER BY registered_at DESC 
            LIMIT %s
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            cursor.close()
            
            return results
        except Exception as e:
            logger.error(f"최근 교통사고 조회 실패: {e}")
            return []
    
    def analyze_traffic_safety(self) -> Dict:
        """교통 안전 분석"""
        try:
            district_stats = self.get_traffic_incidents_by_district(5)
            incident_types = self.get_incident_types()
            recent_incidents = self.get_recent_incidents(3)
            
            analysis = {
                "total_incidents": sum(item['incident_count'] for item in district_stats),
                "high_risk_districts": district_stats[:3],
                "common_incident_types": incident_types[:3],
                "recent_incidents": recent_incidents,
                "safety_recommendations": self._generate_safety_recommendations(district_stats, incident_types)
            }
            
            return analysis
        except Exception as e:
            logger.error(f"교통 안전 분석 실패: {e}")
            return {}
    
    def _generate_safety_recommendations(self, district_stats, incident_types) -> List[str]:
        """안전 개선 권고사항 생성"""
        recommendations = []
        
        if district_stats:
            top_district = district_stats[0]
            recommendations.append(f"{top_district['district']}에서 교통사고가 가장 많이 발생하고 있습니다. 해당 지역의 교통 안전 시설 점검이 필요합니다.")
        
        if incident_types:
            top_type = incident_types[0]
            recommendations.append(f"{top_type['type']} 사고가 가장 빈번합니다. 해당 사고 유형에 대한 예방 교육이 필요합니다.")
        
        recommendations.append("교통사고 다발 구간에 대한 신호등 개선 및 도로 확장을 검토해보세요.")
        recommendations.append("시민 대상 교통 안전 교육 프로그램을 확대하는 것을 권장합니다.")
        
        return recommendations

def create_traffic_analyzer():
    """교통 데이터 분석기 생성"""
    return TrafficDataAnalyzer()
