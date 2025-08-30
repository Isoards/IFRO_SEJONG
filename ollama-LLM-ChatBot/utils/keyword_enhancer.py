"""
키워드 인식률 향상을 위한 유틸리티 모듈

이 모듈은 질문 분석과 답변 생성에서 키워드 인식률을 높이기 위한
다양한 기능들을 제공합니다.
"""

import re
import json
import pickle
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import Counter, defaultdict
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class ExpressionChain:
    """표현 체인 관리 클래스"""
    
    def __init__(self, base_expression: str, related_expressions: List[str], weight: float = 1.0):
        self.base_expression = base_expression
        self.related_expressions = related_expressions
        self.weight = weight
        self.usage_count = 0
        self.success_count = 0
        self.last_used = None
        
    def update_usage(self, success: bool = True):
        """사용 통계 업데이트"""
        self.usage_count += 1
        if success:
            self.success_count += 1
        self.last_used = datetime.now()
        
    def get_success_rate(self) -> float:
        """성공률 계산"""
        return self.success_count / self.usage_count if self.usage_count > 0 else 0.0

class MultiExpressionIndex:
    """다중 표현 인덱스 관리 클래스"""
    
    def __init__(self):
        self.expression_chains: Dict[str, ExpressionChain] = {}
        self.context_weights: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.user_feedback: List[Dict] = []
        
    def add_expression_chain(self, base_expression: str, related_expressions: List[str], 
                           context: str = "general", weight: float = 1.0):
        """표현 체인 추가"""
        chain = ExpressionChain(base_expression, related_expressions, weight)
        self.expression_chains[base_expression] = chain
        self.context_weights[context][base_expression] = weight
        
    def get_expressions_for_query(self, query: str, context: str = "general") -> List[str]:
        """쿼리에 대한 모든 관련 표현 반환"""
        expressions = []
        for base_expr, chain in self.expression_chains.items():
            if base_expr.lower() in query.lower():
                expressions.extend([base_expr] + chain.related_expressions)
            else:
                for related_expr in chain.related_expressions:
                    if related_expr.lower() in query.lower():
                        expressions.extend([base_expr] + chain.related_expressions)
                        break
        return list(set(expressions))
    
    def update_feedback(self, query: str, expressions_used: List[str], 
                       success: bool, user_rating: Optional[int] = None):
        """사용자 피드백 업데이트"""
        feedback = {
            "query": query,
            "expressions_used": expressions_used,
            "success": success,
            "user_rating": user_rating,
            "timestamp": datetime.now()
        }
        self.user_feedback.append(feedback)
        
        # 표현 체인 성공률 업데이트
        for expr in expressions_used:
            if expr in self.expression_chains:
                self.expression_chains[expr].update_usage(success)
    
    def get_optimal_expressions(self, query: str, context: str = "general", 
                              top_k: int = 5) -> List[Tuple[str, float]]:
        """최적 표현 선택 (성공률과 가중치 기반)"""
        candidates = []
        for base_expr, chain in self.expression_chains.items():
            if base_expr.lower() in query.lower() or any(rel.lower() in query.lower() for rel in chain.related_expressions):
                # 성공률과 가중치를 결합한 점수 계산
                success_rate = chain.get_success_rate()
                context_weight = self.context_weights[context].get(base_expr, 1.0)
                score = (success_rate * 0.7 + context_weight * 0.3) * chain.weight
                candidates.append((base_expr, score))
        
        # 점수순 정렬 후 상위 k개 반환
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]
    
    def save(self, filepath: str):
        """인덱스 저장"""
        data = {
            "expression_chains": self.expression_chains,
            "context_weights": dict(self.context_weights),
            "user_feedback": self.user_feedback
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, filepath: str):
        """인덱스 로드"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        self.expression_chains = data["expression_chains"]
        self.context_weights = defaultdict(dict, data["context_weights"])
        self.user_feedback = data["user_feedback"]

class KeywordEnhancer:
    """
    키워드 인식률 향상 클래스
    
    주요 기능:
    1. 도메인별 전문 용어 사전 관리
    2. 키워드 정규화 및 표준화
    3. 키워드 가중치 계산
    4. 키워드 확장 및 추천
    """
    
    def __init__(self, domain: str = "general"):
        """
        KeywordEnhancer 초기화
        
        Args:
            domain: 도메인 (general, technical, business, academic 등)
        """
        self.domain = domain
        self.domain_keywords = self._load_domain_keywords(domain)
        self.synonym_dict = self._load_synonym_dictionary()
        self.abbreviation_dict = self._load_abbreviation_dictionary()
        
        # 다중 표현 인덱스 초기화
        self.multi_expression_index = MultiExpressionIndex()
        self._initialize_multi_expressions()
        
        logger.info(f"KeywordEnhancer 초기화 완료 (도메인: {domain})")
    
    def _initialize_multi_expressions(self):
        """다중 표현 인덱스 초기화"""
        # 교통 도메인 특화 표현
        traffic_expressions = {
            "교통사고": ["사고", "충돌", "교통사고", "교통사고사고", "교통사고"],
            "교차로": ["사거리", "교차점", "인터섹션", "교차로"],
            "신호등": ["신호", "신호등", "트래픽라이트", "신호등"],
            "교통량": ["트래픽", "교통량", "차량수", "교통량"],
            "교통정체": ["정체", "교통정체", "막힘", "교통정체"],
            "사고발생": ["사고", "발생", "사고발생", "사고발생"],
            "교통상황": ["상황", "교통상황", "교통상황", "교통상황"],
            "교통정보": ["정보", "교통정보", "교통정보", "교통정보"],
            "교통관리": ["관리", "교통관리", "교통관리", "교통관리"],
            "교통안전": ["안전", "교통안전", "교통안전", "교통안전"]
        }
        
        # 데이터베이스 쿼리 관련 표현
        db_expressions = {
            "조회": ["검색", "찾기", "가져오기", "SELECT", "조회"],
            "통계": ["집계", "합계", "평균", "COUNT", "통계"],
            "기간": ["기간", "날짜", "시간", "기간", "기간"],
            "정렬": ["순서", "정렬", "ORDER BY", "정렬"],
            "필터": ["조건", "필터", "WHERE", "필터"],
            "그룹": ["묶음", "그룹", "GROUP BY", "그룹"],
            "최대": ["최대값", "MAX", "최대"],
            "최소": ["최소값", "MIN", "최소"],
            "평균": ["평균값", "AVG", "평균"],
            "합계": ["총합", "SUM", "합계"]
        }
        
        # 일반 표현
        general_expressions = {
            "시스템": ["시스템", "프로그램", "소프트웨어", "시스템"],
            "데이터": ["데이터", "정보", "자료", "데이터"],
            "사용자": ["사용자", "관리자", "고객", "사용자"],
            "기능": ["기능", "특성", "역할", "기능"],
            "설정": ["설정", "구성", "환경", "설정"],
            "문제": ["문제", "오류", "장애", "문제"],
            "해결": ["해결", "수정", "개선", "해결"]
        }
        
        # 표현 체인 추가
        for context, expressions in [("traffic", traffic_expressions), 
                                   ("database", db_expressions), 
                                   ("general", general_expressions)]:
            for base_expr, related_exprs in expressions.items():
                self.multi_expression_index.add_expression_chain(
                    base_expr, related_exprs, context, weight=1.2 if context == "traffic" else 1.0
                )
    
    def _load_domain_keywords(self, domain: str) -> Dict[str, float]:
        """
        도메인별 전문 키워드 로드
        
        Args:
            domain: 도메인 이름
            
        Returns:
            키워드와 가중치 딕셔너리
        """
        domain_keywords = {
            "general": {
                "시스템": 1.0, "프로그램": 1.0, "소프트웨어": 1.0,
                "데이터": 1.0, "정보": 1.0, "자료": 1.0,
                "사용자": 1.0, "관리자": 1.0, "고객": 1.0,
                "기능": 1.0, "특성": 1.0, "역할": 1.0,
                "설정": 1.0, "구성": 1.0, "환경": 1.0,
                "문제": 1.0, "오류": 1.0, "장애": 1.0,
                "해결": 1.0, "수정": 1.0, "개선": 1.0
            },
            "technical": {
                # IT/기술 도메인
                "API": 1.2, "인터페이스": 1.2, "프로토콜": 1.2,
                "데이터베이스": 1.2, "DB": 1.2, "쿼리": 1.2,
                "네트워크": 1.2, "서버": 1.2, "클라이언트": 1.2,
                "보안": 1.2, "인증": 1.2, "암호화": 1.2,
                "성능": 1.2, "최적화": 1.2, "캐싱": 1.2,
                "백업": 1.2, "복구": 1.2, "동기화": 1.2,
                "배포": 1.2, "버전": 1.2, "릴리즈": 1.2
            },
            "business": {
                # 비즈니스 도메인
                "매출": 1.2, "수익": 1.2, "비용": 1.2,
                "고객": 1.2, "서비스": 1.2, "제품": 1.2,
                "마케팅": 1.2, "판매": 1.2, "운영": 1.2,
                "전략": 1.2, "계획": 1.2, "목표": 1.2,
                "성과": 1.2, "지표": 1.2, "분석": 1.2,
                "리스크": 1.2, "규정": 1.2, "정책": 1.2
            },
            "academic": {
                # 학술 도메인
                "연구": 1.2, "분석": 1.2, "조사": 1.2,
                "데이터": 1.2, "샘플": 1.2, "통계": 1.2,
                "결과": 1.2, "결론": 1.2, "가설": 1.2,
                "방법론": 1.2, "이론": 1.2, "모델": 1.2,
                "검증": 1.2, "실험": 1.2, "평가": 1.2
            }
        }
        
        return domain_keywords.get(domain, domain_keywords["general"])
    
    def _load_synonym_dictionary(self) -> Dict[str, List[str]]:
        """
        동의어 사전 로드
        
        Returns:
            동의어 사전
        """
        return {
            # 일반 용어
            "방법": ["방식", "기법", "기술", "수단", "절차"],
            "과정": ["절차", "단계", "순서", "진행", "절차"],
            "결과": ["성과", "효과", "결과물", "산출물", "성과"],
            "문제": ["이슈", "과제", "해결사항", "장애", "오류"],
            "개선": ["향상", "발전", "고도화", "최적화", "개선"],
            "분석": ["검토", "조사", "연구", "평가", "분석"],
            
            # IT 용어
            "시스템": ["플랫폼", "솔루션", "도구", "시스템", "애플리케이션"],
            "데이터": ["정보", "자료", "내용", "데이터", "파일"],
            "관리": ["운영", "유지보수", "관리", "제어"],
            "보안": ["안전", "보호", "안전성", "보안", "인증"],
            "성능": ["효율", "속도", "품질", "성능", "처리속도"],
            
            # 비즈니스 용어
            "비용": ["금액", "가격", "지출", "비용", "경비"],
            "시간": ["기간", "소요시간", "기한", "시간", "기간"],
            "사용자": ["고객", "이용자", "사용자", "사용자"],
            "기능": ["특성", "역할", "작용", "기능", "서비스"],
            "구조": ["체계", "구성", "설계", "구조", "아키텍처"],
            
            # 환경 및 설정
            "환경": ["조건", "상황", "배경", "환경", "설정"],
            "요구사항": ["필요사항", "요구", "필요", "요구사항"],
            "정책": ["규정", "지침", "방침", "정책", "규칙"],
            "절차": ["순서", "과정", "단계", "절차", "방법"]
        }
    
    def _load_abbreviation_dictionary(self) -> Dict[str, str]:
        """
        약어 사전 로드
        
        Returns:
            약어 사전
        """
        return {
            # IT 약어
            "API": "Application Programming Interface",
            "DB": "데이터베이스",
            "UI": "사용자 인터페이스",
            "UX": "사용자 경험",
            "OS": "운영체제",
            "CPU": "중앙처리장치",
            "RAM": "메모리",
            "HDD": "하드디스크",
            "SSD": "솔리드스테이트드라이브",
            "LAN": "근거리통신망",
            "WAN": "광역통신망",
            "VPN": "가상사설망",
            "HTTP": "하이퍼텍스트 전송 프로토콜",
            "HTTPS": "보안 하이퍼텍스트 전송 프로토콜",
            "FTP": "파일 전송 프로토콜",
            "SMTP": "간이 메일 전송 프로토콜",
            "POP3": "메일 수신 프로토콜",
            "IMAP": "인터넷 메시지 접근 프로토콜",
            
            # 비즈니스 약어
            "CEO": "최고경영자",
            "CFO": "최고재무책임자",
            "CTO": "최고기술책임자",
            "HR": "인사",
            "IT": "정보기술",
            "R&D": "연구개발",
            "QA": "품질보증",
            "QC": "품질관리",
            "KPI": "핵심성과지표",
            "ROI": "투자수익률",
            "B2B": "기업간 거래",
            "B2C": "기업과 소비자 간 거래",
            "CRM": "고객관계관리",
            "ERP": "전사적 자원관리",
            "SaaS": "서비스형 소프트웨어",
            "PaaS": "서비스형 플랫폼",
            "IaaS": "서비스형 인프라"
        }
    
    def enhance_keywords(self, keywords: List[str]) -> List[str]:
        """
        키워드 향상 (확장 및 정규화)
        
        Args:
            keywords: 원본 키워드 리스트
            
        Returns:
            향상된 키워드 리스트
        """
        enhanced_keywords = []
        
        for keyword in keywords:
            # 1. 키워드 정규화
            normalized = self._normalize_keyword(keyword)
            enhanced_keywords.append(normalized)
            
            # 2. 동의어 확장
            synonyms = self._get_synonyms(normalized)
            enhanced_keywords.extend(synonyms)
            
            # 3. 약어 확장
            abbreviation = self._expand_abbreviation(normalized)
            if abbreviation:
                enhanced_keywords.append(abbreviation)
        
        # 중복 제거 및 정렬
        unique_keywords = list(set(enhanced_keywords))
        unique_keywords.sort(key=len, reverse=True)
        
        return unique_keywords
    
    def _normalize_keyword(self, keyword: str) -> str:
        """
        키워드 정규화
        
        Args:
            keyword: 원본 키워드
            
        Returns:
            정규화된 키워드
        """
        # 소문자 변환
        normalized = keyword.lower()
        
        # 특수문자 제거
        normalized = re.sub(r'[^\w가-힣]', '', normalized)
        
        # 연속된 공백 제거
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _get_synonyms(self, keyword: str) -> List[str]:
        """
        키워드의 동의어 반환
        
        Args:
            keyword: 키워드
            
        Returns:
            동의어 리스트
        """
        return self.synonym_dict.get(keyword, [])
    
    def _expand_abbreviation(self, keyword: str) -> Optional[str]:
        """
        약어 확장
        
        Args:
            keyword: 키워드
            
        Returns:
            확장된 약어 (없으면 None)
        """
        return self.abbreviation_dict.get(keyword.upper())
    
    def calculate_keyword_weight(self, keyword: str, context: str = "") -> float:
        """
        키워드 가중치 계산
        
        Args:
            keyword: 키워드
            context: 컨텍스트 (선택사항)
            
        Returns:
            가중치 점수
        """
        weight = 1.0
        
        # 1. 도메인 키워드 가중치
        if keyword in self.domain_keywords:
            weight *= self.domain_keywords[keyword]
        
        # 2. 컨텍스트에서의 빈도
        if context:
            frequency = context.lower().count(keyword.lower())
            weight *= (1.0 + frequency * 0.1)
        
        # 3. 키워드 길이 가중치 (긴 키워드가 더 중요)
        weight *= (1.0 + len(keyword) * 0.05)
        
        return weight
    
    def recommend_keywords(self, text: str, max_keywords: int = 10) -> List[Tuple[str, float]]:
        """
        텍스트에서 키워드 추천
        
        Args:
            text: 분석할 텍스트
            max_keywords: 최대 추천 키워드 수
            
        Returns:
            (키워드, 가중치) 튜플 리스트
        """
        # 1. 텍스트에서 단어 추출
        words = re.findall(r'\b\w{2,}\b', text.lower())
        
        # 2. 단어 빈도 계산
        word_freq = Counter(words)
        
        # 3. 키워드 점수 계산
        keyword_scores = []
        for word, freq in word_freq.items():
            # 기본 점수
            score = freq
            
            # 도메인 키워드 가중치 적용
            weight = self.calculate_keyword_weight(word, text)
            score *= weight
            
            keyword_scores.append((word, score))
        
        # 4. 점수로 정렬하고 상위 키워드 반환
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        return keyword_scores[:max_keywords]
    
    def extract_domain_specific_keywords(self, text: str) -> List[str]:
        """
        도메인 특화 키워드 추출
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            도메인 특화 키워드 리스트
        """
        domain_keywords = []
        text_lower = text.lower()
        
        for keyword in self.domain_keywords.keys():
            if keyword in text_lower:
                domain_keywords.append(keyword)
        
        return domain_keywords
    
    def create_keyword_index(self, documents: List[str]) -> Dict[str, List[int]]:
        """
        문서 집합에서 키워드 인덱스 생성
        
        Args:
            documents: 문서 리스트
            
        Returns:
            키워드별 문서 인덱스
        """
        keyword_index = {}
        
        for doc_idx, document in enumerate(documents):
            # 문서에서 키워드 추출
            recommended_keywords = self.recommend_keywords(document, max_keywords=20)
            
            for keyword, _ in recommended_keywords:
                if keyword not in keyword_index:
                    keyword_index[keyword] = []
                keyword_index[keyword].append(doc_idx)
        
        return keyword_index
    
    def find_similar_keywords(self, target_keyword: str, 
                            keyword_candidates: List[str]) -> List[Tuple[str, float]]:
        """
        유사한 키워드 찾기
        
        Args:
            target_keyword: 대상 키워드
            keyword_candidates: 후보 키워드들
            
        Returns:
            (키워드, 유사도) 튜플 리스트
        """
        similarities = []
        target_normalized = self._normalize_keyword(target_keyword)
        
        for candidate in keyword_candidates:
            candidate_normalized = self._normalize_keyword(candidate)
            
            # 1. 정확한 매칭
            if target_normalized == candidate_normalized:
                similarities.append((candidate, 1.0))
                continue
            
            # 2. 부분 문자열 매칭
            if (len(target_normalized) >= 3 and len(candidate_normalized) >= 3 and
                (target_normalized in candidate_normalized or 
                 candidate_normalized in target_normalized)):
                similarity = min(len(target_normalized), len(candidate_normalized)) / \
                           max(len(target_normalized), len(candidate_normalized))
                similarities.append((candidate, similarity))
                continue
            
            # 3. 동의어 매칭
            target_synonyms = self._get_synonyms(target_normalized)
            if candidate_normalized in target_synonyms:
                similarities.append((candidate, 0.8))
                continue
        
        # 유사도로 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities
    
    # 다중 표현 인덱싱 관련 메서드들
    def get_multi_expressions(self, query: str, context: str = "general") -> List[str]:
        """
        쿼리에 대한 다중 표현 반환
        
        Args:
            query: 사용자 쿼리
            context: 컨텍스트 (traffic, database, general 등)
            
        Returns:
            관련된 모든 표현 리스트
        """
        return self.multi_expression_index.get_expressions_for_query(query, context)
    
    def get_optimal_expressions(self, query: str, context: str = "general", 
                              top_k: int = 5) -> List[Tuple[str, float]]:
        """
        최적 표현 선택 (성공률과 가중치 기반)
        
        Args:
            query: 사용자 쿼리
            context: 컨텍스트
            top_k: 반환할 최적 표현 수
            
        Returns:
            (표현, 점수) 튜플 리스트
        """
        return self.multi_expression_index.get_optimal_expressions(query, context, top_k)
    
    def update_expression_feedback(self, query: str, expressions_used: List[str], 
                                 success: bool, user_rating: Optional[int] = None):
        """
        표현 사용 피드백 업데이트
        
        Args:
            query: 원본 쿼리
            expressions_used: 사용된 표현들
            success: 성공 여부
            user_rating: 사용자 평가 (1-5)
        """
        self.multi_expression_index.update_feedback(query, expressions_used, success, user_rating)
    
    def add_custom_expression_chain(self, base_expression: str, related_expressions: List[str], 
                                  context: str = "general", weight: float = 1.0):
        """
        사용자 정의 표현 체인 추가
        
        Args:
            base_expression: 기본 표현
            related_expressions: 관련 표현들
            context: 컨텍스트
            weight: 가중치
        """
        self.multi_expression_index.add_expression_chain(
            base_expression, related_expressions, context, weight
        )
    
    def enhance_query_with_expressions(self, query: str, context: str = "general") -> str:
        """
        표현을 활용한 쿼리 향상
        
        Args:
            query: 원본 쿼리
            context: 컨텍스트
            
        Returns:
            향상된 쿼리
        """
        expressions = self.get_multi_expressions(query, context)
        if not expressions:
            return query
        
        # 쿼리에 표현들을 추가하여 검색 범위 확장
        enhanced_query = query
        for expr in expressions[:3]:  # 상위 3개 표현만 사용
            if expr.lower() not in query.lower():
                enhanced_query += f" {expr}"
        
        return enhanced_query
    
    def get_expression_statistics(self) -> Dict[str, Any]:
        """
        표현 사용 통계 반환
        
        Returns:
            표현 통계 정보
        """
        stats = {
            "total_chains": len(self.multi_expression_index.expression_chains),
            "total_feedback": len(self.multi_expression_index.user_feedback),
            "contexts": list(self.multi_expression_index.context_weights.keys()),
            "top_expressions": []
        }
        
        # 상위 사용 표현들
        usage_stats = []
        for base_expr, chain in self.multi_expression_index.expression_chains.items():
            usage_stats.append({
                "expression": base_expr,
                "usage_count": chain.usage_count,
                "success_rate": chain.get_success_rate(),
                "weight": chain.weight
            })
        
        usage_stats.sort(key=lambda x: x["usage_count"], reverse=True)
        stats["top_expressions"] = usage_stats[:10]
        
        return stats
    
    def save_multi_expression_index(self, filepath: str):
        """다중 표현 인덱스 저장"""
        self.multi_expression_index.save(filepath)
    
    def load_multi_expression_index(self, filepath: str):
        """다중 표현 인덱스 로드"""
        self.multi_expression_index.load(filepath)
    
    def get_context_specific_expressions(self, context: str) -> Dict[str, List[str]]:
        """
        특정 컨텍스트의 표현들 반환
        
        Args:
            context: 컨텍스트 이름
            
        Returns:
            표현 체인 딕셔너리
        """
        context_expressions = {}
        for base_expr, chain in self.multi_expression_index.expression_chains.items():
            if context in self.multi_expression_index.context_weights and \
               base_expr in self.multi_expression_index.context_weights[context]:
                context_expressions[base_expr] = chain.related_expressions
        
        return context_expressions

# 사용 예시
if __name__ == "__main__":
    enhancer = KeywordEnhancer(domain="technical")
    
    # 키워드 향상 테스트
    original_keywords = ["시스템", "API", "데이터"]
    enhanced = enhancer.enhance_keywords(original_keywords)
    print(f"향상된 키워드: {enhanced}")
    
    # 키워드 추천 테스트
    text = "시스템 API를 통해 데이터를 처리하고 성능을 개선합니다."
    recommended = enhancer.recommend_keywords(text)
    print(f"추천 키워드: {recommended}")
