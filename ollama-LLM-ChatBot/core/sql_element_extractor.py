"""
SQL 요소 추출기 - 규칙 기반/NER/슬롯 채우기 방식

SBERT는 라우팅용으로만 사용하고, SQL 요소 추출은 빠르고 정확한 규칙 기반 방식 사용
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """쿼리 타입"""
    SELECT = "SELECT"
    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MAX = "MAX"
    MIN = "MIN"
    GROUP_BY = "GROUP_BY"
    ORDER_BY = "ORDER_BY"

class ComparisonOperator(Enum):
    """비교 연산자"""
    EQUAL = "="
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    NOT_EQUAL = "!="
    LIKE = "LIKE"
    IN = "IN"
    BETWEEN = "BETWEEN"

@dataclass
class SQLSlot:
    """SQL 슬롯 (요소)"""
    slot_type: str  # table, column, value, condition 등
    value: str
    confidence: float = 1.0
    original_text: str = ""

@dataclass
class ExtractedSQLElements:
    """추출된 SQL 요소들"""
    query_type: QueryType
    table_name: str
    columns: List[str] = None
    conditions: List[Dict[str, Any]] = None
    group_by: List[str] = None
    order_by: List[str] = None
    limit: Optional[int] = None
    slots: List[SQLSlot] = None
    confidence: float = 0.0

class SQLElementExtractor:
    """
    SQL 요소 추출기 - 규칙 기반 방식
    
    기능:
    1. 한국어 질문에서 SQL 요소 추출
    2. 테이블/컬럼 매핑
    3. 조건절 추출
    4. 집계 함수 식별
    """
    
    def __init__(self):
        """SQL 요소 추출기 초기화"""
        
        # 교통 도메인 스키마 정의
        self.schema = {
            "traffic_intersection": {
                "columns": {
                    "id": ["ID", "식별자", "번호"],
                    "name": ["이름", "명칭", "교차로명"],
                    "location": ["위치", "장소", "지역", "곳"],
                    "traffic_volume": ["교통량", "통행량", "차량수", "대수"],
                    "accident_count": ["사고수", "사고건수", "사고", "접촉사고"],
                    "signal_type": ["신호", "신호등", "신호기"],
                    "coordinates": ["좌표", "위경도"],
                    "district": ["구", "지역", "행정구역"],
                    "road_type": ["도로", "도로유형", "차로"]
                },
                "aliases": ["교차로", "교차점", "신호등", "신호", "사거리", "삼거리"]
            },
            "traffic_incident": {
                "columns": {
                    "id": ["ID", "식별자", "번호"],
                    "incident_type": ["사고유형", "사고종류", "유형"],
                    "location": ["위치", "장소", "발생지"],
                    "timestamp": ["시간", "일시", "발생시간", "날짜"],
                    "severity": ["심각도", "등급", "피해"],
                    "description": ["설명", "내용", "상세"]
                },
                "aliases": ["사고", "접촉사고", "교통사고", "사건"]
            },
            "traffic_volume": {
                "columns": {
                    "id": ["ID", "식별자"],
                    "intersection_id": ["교차로ID", "교차로"],
                    "volume": ["교통량", "통행량", "차량수"],
                    "timestamp": ["시간", "일시", "측정시간"],
                    "direction": ["방향", "진행방향"],
                    "vehicle_type": ["차종", "차량유형"]
                },
                "aliases": ["교통량", "통행량", "차량수", "볼륨"]
            }
        }
        
        # 쿼리 유형 패턴
        self.query_patterns = {
            QueryType.COUNT: [
                r'몇\s*개', r'몇\s*곳', r'몇\s*건', r'개수', r'수량', r'건수',
                r'갯수', r'총\s*\w+', r'전체\s*\w+'
            ],
            QueryType.SUM: [
                r'총\s*교통량', r'전체\s*교통량', r'합계', r'총합', r'누적'
            ],
            QueryType.AVG: [
                r'평균', r'평균적', r'보통', r'일반적'
            ],
            QueryType.MAX: [
                r'최대', r'최고', r'가장\s*많', r'제일\s*많', r'최다'
            ],
            QueryType.MIN: [
                r'최소', r'최저', r'가장\s*적', r'제일\s*적', r'최소한'
            ],
            QueryType.SELECT: [
                r'보여', r'알려', r'찾아', r'검색', r'조회', r'확인'
            ]
        }
        
        # 조건 패턴
        self.condition_patterns = {
            ComparisonOperator.GREATER: [
                r'(\w+)이?\s*(\d+)\s*이상', r'(\w+)이?\s*(\d+)\s*초과',
                r'(\d+)\s*이상의?\s*(\w+)', r'(\d+)\s*초과의?\s*(\w+)'
            ],
            ComparisonOperator.LESS: [
                r'(\w+)이?\s*(\d+)\s*이하', r'(\w+)이?\s*(\d+)\s*미만',
                r'(\d+)\s*이하의?\s*(\w+)', r'(\d+)\s*미만의?\s*(\w+)'
            ],
            ComparisonOperator.EQUAL: [
                r'(\w+)이?\s*(\d+)', r'(\w+)이?\s*["\']([^"\']+)["\']',
                r'(\w+)이?\s*(\w+)', r'(\w+)\s*=\s*(\w+)'
            ],
            ComparisonOperator.LIKE: [
                r'(\w+)이?\s*포함', r'(\w+)이?\s*들어간', r'(\w+)이?\s*있는'
            ]
        }
        
        # 시간 패턴
        self.time_patterns = [
            r'(\d{4})년', r'(\d{1,2})월', r'(\d{1,2})일',
            r'오늘', r'어제', r'이번\s*주', r'지난\s*주', r'이번\s*달', r'지난\s*달'
        ]
        
        # 장소 패턴
        self.location_patterns = [
            r'(\w+구)', r'(\w+동)', r'(\w+로)', r'(\w+대로)', r'(\w+역)',
            r'강남', r'서초', r'송파', r'강동', r'마포', r'용산', r'중구'
        ]
        
        logger.info("SQL 요소 추출기 초기화 완료")
    
    def extract_elements(self, question: str) -> ExtractedSQLElements:
        """
        질문에서 SQL 요소 추출
        
        Args:
            question: 사용자 질문
            
        Returns:
            추출된 SQL 요소들
        """
        question = question.strip()
        logger.debug(f"SQL 요소 추출 시작: {question}")
        
        # 1. 쿼리 타입 결정
        query_type = self._detect_query_type(question)
        
        # 2. 테이블 식별
        table_name = self._identify_table(question)
        
        # 3. 컬럼 추출
        columns = self._extract_columns(question, table_name)
        
        # 4. 조건절 추출
        conditions = self._extract_conditions(question, table_name)
        
        # 5. GROUP BY 추출
        group_by = self._extract_group_by(question)
        
        # 6. ORDER BY 추출
        order_by = self._extract_order_by(question)
        
        # 7. LIMIT 추출
        limit = self._extract_limit(question)
        
        # 8. 슬롯 정보 생성
        slots = self._create_slots(question, table_name, columns, conditions)
        
        # 9. 신뢰도 계산
        confidence = self._calculate_confidence(question, query_type, table_name, columns)
        
        result = ExtractedSQLElements(
            query_type=query_type,
            table_name=table_name,
            columns=columns,
            conditions=conditions,
            group_by=group_by,
            order_by=order_by,
            limit=limit,
            slots=slots,
            confidence=confidence
        )
        
        logger.debug(f"SQL 요소 추출 완료: {result}")
        return result
    
    def _detect_query_type(self, question: str) -> QueryType:
        """쿼리 타입 감지"""
        question_lower = question.lower()
        
        # 패턴 매칭으로 쿼리 타입 결정
        for query_type, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    logger.debug(f"쿼리 타입 감지: {query_type}, 패턴: {pattern}")
                    return query_type
        
        # 기본값은 SELECT
        return QueryType.SELECT
    
    def _identify_table(self, question: str) -> str:
        """테이블 식별"""
        question_lower = question.lower()
        
        # 각 테이블의 별칭을 확인
        for table_name, schema_info in self.schema.items():
            aliases = schema_info.get("aliases", [])
            
            # 테이블 별칭 매칭
            for alias in aliases:
                if alias in question_lower:
                    logger.debug(f"테이블 식별: {table_name}, 별칭: {alias}")
                    return table_name
        
        # 기본 테이블
        return "traffic_intersection"
    
    def _extract_columns(self, question: str, table_name: str) -> List[str]:
        """컬럼 추출"""
        question_lower = question.lower()
        columns = []
        
        if table_name not in self.schema:
            return ["*"]
        
        table_schema = self.schema[table_name]["columns"]
        
        # 각 컬럼의 별칭을 확인
        for column_name, aliases in table_schema.items():
            for alias in aliases:
                if alias in question_lower:
                    if column_name not in columns:
                        columns.append(column_name)
                        logger.debug(f"컬럼 추출: {column_name}, 별칭: {alias}")
        
        # 컬럼이 없으면 전체 선택
        return columns if columns else ["*"]
    
    def _extract_conditions(self, question: str, table_name: str) -> List[Dict[str, Any]]:
        """조건절 추출"""
        conditions = []
        
        # 숫자 조건 추출
        for operator, patterns in self.condition_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, question)
                for match in matches:
                    condition = {
                        "column": self._map_to_column(match.group(1), table_name),
                        "operator": operator.value,
                        "value": match.group(2),
                        "original_text": match.group(0)
                    }
                    conditions.append(condition)
                    logger.debug(f"조건 추출: {condition}")
        
        # 시간 조건 추출
        time_conditions = self._extract_time_conditions(question)
        conditions.extend(time_conditions)
        
        # 장소 조건 추출
        location_conditions = self._extract_location_conditions(question)
        conditions.extend(location_conditions)
        
        return conditions
    
    def _extract_time_conditions(self, question: str) -> List[Dict[str, Any]]:
        """시간 조건 추출"""
        conditions = []
        
        for pattern in self.time_patterns:
            matches = re.finditer(pattern, question)
            for match in matches:
                condition = {
                    "column": "timestamp",
                    "operator": "LIKE",
                    "value": f"%{match.group(1)}%",
                    "original_text": match.group(0)
                }
                conditions.append(condition)
                logger.debug(f"시간 조건 추출: {condition}")
        
        return conditions
    
    def _extract_location_conditions(self, question: str) -> List[Dict[str, Any]]:
        """장소 조건 추출"""
        conditions = []
        
        for pattern in self.location_patterns:
            matches = re.finditer(pattern, question)
            for match in matches:
                condition = {
                    "column": "location",
                    "operator": "LIKE",
                    "value": f"%{match.group(1)}%",
                    "original_text": match.group(0)
                }
                conditions.append(condition)
                logger.debug(f"장소 조건 추출: {condition}")
        
        return conditions
    
    def _extract_group_by(self, question: str) -> List[str]:
        """GROUP BY 추출"""
        group_patterns = [r'별로', r'각', r'구별', r'분류']
        
        for pattern in group_patterns:
            if re.search(pattern, question):
                # 간단한 그룹핑 로직
                if "구별" in question or "지역별" in question:
                    return ["district"]
                elif "시간별" in question:
                    return ["DATE(timestamp)"]
        
        return []
    
    def _extract_order_by(self, question: str) -> List[str]:
        """ORDER BY 추출"""
        if "많은순" in question or "높은순" in question:
            return ["traffic_volume DESC"]
        elif "적은순" in question or "낮은순" in question:
            return ["traffic_volume ASC"]
        
        return []
    
    def _extract_limit(self, question: str) -> Optional[int]:
        """LIMIT 추출"""
        # 숫자 패턴 찾기
        limit_patterns = [
            r'상위\s*(\d+)', r'(\d+)개', r'(\d+)곳',
            r'처음\s*(\d+)', r'첫\s*(\d+)'
        ]
        
        for pattern in limit_patterns:
            match = re.search(pattern, question)
            if match:
                return int(match.group(1))
        
        return None
    
    def _map_to_column(self, text: str, table_name: str) -> str:
        """텍스트를 실제 컬럼명으로 매핑"""
        if table_name not in self.schema:
            return text
        
        table_schema = self.schema[table_name]["columns"]
        
        for column_name, aliases in table_schema.items():
            if text in aliases:
                return column_name
        
        return text
    
    def _create_slots(self, question: str, table_name: str, columns: List[str], conditions: List[Dict]) -> List[SQLSlot]:
        """슬롯 정보 생성"""
        slots = []
        
        # 테이블 슬롯
        slots.append(SQLSlot(
            slot_type="table",
            value=table_name,
            confidence=1.0,
            original_text=question
        ))
        
        # 컬럼 슬롯들
        for column in columns:
            slots.append(SQLSlot(
                slot_type="column",
                value=column,
                confidence=0.9,
                original_text=question
            ))
        
        # 조건 슬롯들
        for condition in conditions:
            slots.append(SQLSlot(
                slot_type="condition",
                value=f"{condition['column']} {condition['operator']} {condition['value']}",
                confidence=0.8,
                original_text=condition.get('original_text', '')
            ))
        
        return slots
    
    def _calculate_confidence(self, question: str, query_type: QueryType, 
                            table_name: str, columns: List[str]) -> float:
        """신뢰도 계산"""
        confidence = 0.0
        
        # 쿼리 타입 신뢰도 (30%)
        if query_type != QueryType.SELECT:  # 특정 타입이 감지됨
            confidence += 0.3
        else:
            confidence += 0.1
        
        # 테이블 신뢰도 (30%)
        if table_name in self.schema:
            confidence += 0.3
        
        # 컬럼 신뢰도 (40%)
        if columns and columns != ["*"]:
            confidence += 0.4
        elif columns == ["*"]:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def generate_sql(self, elements: ExtractedSQLElements) -> str:
        """추출된 요소들로부터 SQL 생성"""
        
        # SELECT 절
        if elements.query_type == QueryType.COUNT:
            select_clause = "SELECT COUNT(*)"
        elif elements.query_type == QueryType.SUM:
            col = "traffic_volume" if "traffic_volume" in elements.columns else elements.columns[0]
            select_clause = f"SELECT SUM({col})"
        elif elements.query_type == QueryType.AVG:
            col = "traffic_volume" if "traffic_volume" in elements.columns else elements.columns[0]
            select_clause = f"SELECT AVG({col})"
        elif elements.query_type == QueryType.MAX:
            col = "traffic_volume" if "traffic_volume" in elements.columns else elements.columns[0]
            select_clause = f"SELECT MAX({col})"
        elif elements.query_type == QueryType.MIN:
            col = "traffic_volume" if "traffic_volume" in elements.columns else elements.columns[0]
            select_clause = f"SELECT MIN({col})"
        else:
            columns_str = ", ".join(elements.columns) if elements.columns else "*"
            select_clause = f"SELECT {columns_str}"
        
        # FROM 절
        from_clause = f"FROM {elements.table_name}"
        
        # WHERE 절
        where_clause = ""
        if elements.conditions:
            where_conditions = []
            for condition in elements.conditions:
                where_conditions.append(f"{condition['column']} {condition['operator']} '{condition['value']}'")
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
        
        # GROUP BY 절
        group_by_clause = ""
        if elements.group_by:
            group_by_clause = f"GROUP BY {', '.join(elements.group_by)}"
        
        # ORDER BY 절
        order_by_clause = ""
        if elements.order_by:
            order_by_clause = f"ORDER BY {', '.join(elements.order_by)}"
        
        # LIMIT 절
        limit_clause = ""
        if elements.limit:
            limit_clause = f"LIMIT {elements.limit}"
        
        # SQL 조합
        sql_parts = [select_clause, from_clause]
        if where_clause:
            sql_parts.append(where_clause)
        if group_by_clause:
            sql_parts.append(group_by_clause)
        if order_by_clause:
            sql_parts.append(order_by_clause)
        if limit_clause:
            sql_parts.append(limit_clause)
        
        sql = " ".join(sql_parts)
        logger.info(f"생성된 SQL: {sql}")
        return sql

if __name__ == "__main__":
    # 테스트 코드
    extractor = SQLElementExtractor()
    
    test_questions = [
        "강남구 교차로가 몇 개인가요?",
        "교통량이 1000 이상인 교차로를 보여주세요",
        "지난달 교통사고가 가장 많은 곳은?",
        "평균 교통량이 높은 상위 5개 지역",
        "서초구 신호등 개수"
    ]
    
    for question in test_questions:
        print(f"\n질문: {question}")
        elements = extractor.extract_elements(question)
        sql = extractor.generate_sql(elements)
        print(f"생성된 SQL: {sql}")
        print(f"신뢰도: {elements.confidence:.2f}")
