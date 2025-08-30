"""
SQL 전용 모델을 사용한 스키마 기반 SQL 생성 모듈

이 모듈은 질의 유형에 따라 SQL 전용 모델(sqlcoder:7b)을 사용하여
데이터베이스 스키마를 기반으로 정확한 SQL을 생성합니다.
"""

import os
import json
import sqlparse
import time
import pymysql
import asyncio
import concurrent.futures
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

# 로컬 LLM 라이브러리들
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama 라이브러리를 찾을 수 없습니다.")

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python 라이브러리를 찾을 수 없습니다.")

try:
    from .fast_cache import get_sql_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logging.warning("캐시 모듈을 찾을 수 없습니다.")

try:
    from .sql_element_extractor import SQLElementExtractor, ExtractedSQLElements
    ELEMENT_EXTRACTOR_AVAILABLE = True
except ImportError:
    ELEMENT_EXTRACTOR_AVAILABLE = False
    logging.warning("SQL 요소 추출기를 찾을 수 없습니다.")

logger = logging.getLogger(__name__)

class SQLModelType(Enum):
    """SQL 전용 모델 타입"""
    SQLCODER_7B = "sqlcoder:7b"
    SQLCODER_15B = "sqlcoder:15b"
    SQLCODER_34B = "sqlcoder:34b"
    CUSTOM_SQL = "custom_sql"

@dataclass
class DatabaseSchema:
    """데이터베이스 스키마 정보"""
    table_name: str
    columns: List[Dict[str, Any]]  # [{"name": "col1", "type": "TEXT", "description": "설명"}]
    primary_key: Optional[str] = None
    foreign_keys: List[Dict[str, str]] = None  # [{"column": "col1", "references": "table.col"}]
    sample_data: List[Dict[str, Any]] = None  # 샘플 데이터

@dataclass
class SQLQuery:
    """생성된 SQL 쿼리"""
    query: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE
    confidence_score: float
    execution_time: float
    model_name: str
    validation_passed: bool = False
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None
    is_valid: bool = False # 추가된 필드

class SQLGenerator:
    """
    SQL 전용 모델을 사용한 스키마 기반 SQL 생성 클래스
    
    주요 기능:
    1. 스키마 기반 SQL 생성
    2. SQL 구문 검증
    3. Few-shot 예시를 통한 정확도 향상
    4. 오류 발생 시 자동 수정
    """
    
    def __init__(self, 
                 model_type: SQLModelType = SQLModelType.SQLCODER_7B,
                 model_name: str = "sqlcoder:7b",
                 cache_enabled: bool = True):
        """
        SQLGenerator 초기화
        
        Args:
            model_type: SQL 전용 모델 타입
            model_name: 모델 이름
            cache_enabled: 캐싱 활성화 여부
        """
        self.model_type = model_type
        self.model_name = model_name
        self.cache_enabled = cache_enabled and CACHE_AVAILABLE
        self.query_cache = get_sql_cache() if self.cache_enabled else None
        
        # SQL 검증을 위한 설정
        self.max_retries = 3
        self.validation_enabled = True
        
        # 규칙 기반 SQL 요소 추출기 초기화
        self.element_extractor = None
        if ELEMENT_EXTRACTOR_AVAILABLE:
            try:
                self.element_extractor = SQLElementExtractor()
                logger.info("✅ 규칙 기반 SQL 요소 추출기 초기화 완료")
            except Exception as e:
                logger.warning(f"SQL 요소 추출기 초기화 실패: {e}")
                self.element_extractor = None
        
        # 데이터베이스 연결 설정
        self.db_config = {
            'host': os.getenv('MYSQL_HOST', 'db'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', '1234'),
            'database': os.getenv('MYSQL_DATABASE', 'traffic'),
            'charset': 'utf8mb4',
            'port': int(os.getenv('MYSQL_PORT', 3306))
        }
        
        logger.info(f"SQL Generator 초기화: {model_name}")
        logger.info(f"데이터베이스 연결 설정: {self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
    
    def generate_sql_parallel(self,
                             questions: List[str],
                             schema: DatabaseSchema,
                             few_shot_examples: List[Dict[str, str]] = None) -> List[SQLQuery]:
        """
        여러 질문에 대해 병렬로 SQL 생성
        
        Args:
            questions: 자연어 질문들
            schema: 데이터베이스 스키마
            few_shot_examples: Few-shot 예시들
            
        Returns:
            생성된 SQL 쿼리들
        """
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 각 질문에 대해 병렬로 SQL 생성
            future_to_question = {
                executor.submit(self.generate_sql, question, schema, few_shot_examples): question
                for question in questions
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_question):
                question = future_to_question[future]
                try:
                    sql_query = future.result()
                    results.append(sql_query)
                except Exception as e:
                    logger.error(f"SQL 생성 실패 - 질문: {question}, 오류: {e}")
                    # 실패한 경우 기본 오류 쿼리 반환
                    error_query = SQLQuery(
                        query="-- SQL 생성 실패",
                        query_type="ERROR",
                        confidence_score=0.0,
                        execution_time=0.0,
                        model_name=self.model_name,
                        validation_passed=False,
                        error_message=str(e),
                        is_valid=False
                    )
                    results.append(error_query)
        
        total_time = time.time() - start_time
        logger.info(f"병렬 SQL 생성 완료: {len(questions)}개 질문, {total_time:.2f}초")
        return results

    def generate_sql(self, 
                    question: str, 
                    schema: DatabaseSchema,
                    few_shot_examples: List[Dict[str, str]] = None) -> SQLQuery:
        """
        스키마 기반 SQL 생성
        
        Args:
            question: 자연어 질문
            schema: 데이터베이스 스키마
            few_shot_examples: Few-shot 예시들
            
        Returns:
            생성된 SQL 쿼리
        """
        start_time = time.time()
        
        # 캐시 확인 (빠른 SQL 응답)
        if self.cache_enabled and self.query_cache:
            schema_key = f"{schema.table_name}_{len(schema.columns)}"
            cached_sql = self.query_cache.get(question, schema_key)
            if cached_sql:
                logger.info(f"캐시된 SQL 쿼리 사용: {time.time() - start_time:.3f}초")
                return cached_sql
        
        # 규칙 기반 빠른 SQL 생성 (우선 시도)
        if self.element_extractor:
            try:
                elements = self.element_extractor.extract_elements(question)
                if elements.confidence > 0.7:  # 신뢰도가 높은 경우 규칙 기반 사용
                    fast_sql = self.element_extractor.generate_sql(elements)
                    
                    # 빠른 검증
                    validation_result = self._validate_sql(fast_sql)
                    if validation_result['valid']:
                        execution_time = time.time() - start_time
                        
                        sql_query = SQLQuery(
                            query=fast_sql,
                            query_type=elements.query_type.value,
                            confidence_score=elements.confidence,
                            execution_time=execution_time,
                            model_name=f"{self.model_name}_rule_based",
                            validation_passed=True,
                            is_valid=True,
                            metadata={"method": "rule_based", "elements": elements}
                        )
                        
                        # 캐시에 저장
                        if self.cache_enabled and self.query_cache:
                            self.query_cache.put(question, sql_query, schema_key)
                        
                        logger.info(f"🚀 규칙 기반 빠른 SQL 생성: {execution_time:.3f}초, 신뢰도: {elements.confidence:.2f}")
                        return sql_query
                    else:
                        logger.debug(f"규칙 기반 SQL 검증 실패, LLM으로 폴백: {validation_result['error']}")
                else:
                    logger.debug(f"규칙 기반 신뢰도 낮음 ({elements.confidence:.2f}), LLM으로 폴백")
            except Exception as e:
                logger.warning(f"규칙 기반 SQL 생성 실패, LLM으로 폴백: {e}")
        
        # LLM 기반 SQL 생성 (폴백)
        
        # 프롬프트 생성
        prompt = self._create_sql_prompt(question, schema, few_shot_examples)
        
        # SQL 생성
        raw_sql = self._call_sql_model(prompt)
        
        # SQL 정제 및 검증
        cleaned_sql = self._clean_sql(raw_sql)
        validation_result = self._validate_sql(cleaned_sql)
        
        # 오류 발생 시 재시도
        retry_count = 0
        while not validation_result['valid'] and retry_count < self.max_retries:
            logger.warning(f"SQL 검증 실패 (시도 {retry_count + 1}): {validation_result['error']}")
            
            # 수정 요청 프롬프트 생성
            correction_prompt = self._create_correction_prompt(
                question, schema, cleaned_sql, validation_result['error']
            )
            
            # 수정된 SQL 생성
            corrected_sql = self._call_sql_model(correction_prompt)
            cleaned_sql = self._clean_sql(corrected_sql)
            validation_result = self._validate_sql(cleaned_sql)
            retry_count += 1
        
        # 결과 생성
        execution_time = time.time() - start_time
        sql_query = SQLQuery(
            query=cleaned_sql,
            query_type=self._detect_query_type(cleaned_sql),
            confidence_score=validation_result.get('confidence', 0.8),
            execution_time=execution_time,
            model_name=self.model_name,
            validation_passed=validation_result['valid'],
            error_message=validation_result.get('error'),
            is_valid=validation_result['valid']  # 검증 결과에 따라 유효성 설정
        )
        
        # 캐시에 저장 (빠른 후속 SQL 생성을 위해)
        if self.cache_enabled and self.query_cache and sql_query.is_valid:
            schema_key = f"{schema.table_name}_{len(schema.columns)}"
            self.query_cache.put(question, sql_query, schema_key)
        
        logger.info(f"SQL 생성 완료: {sql_query.query_type}, 유효성: {sql_query.is_valid}")
        return sql_query

    def execute_sql(self, sql_query: SQLQuery) -> Dict[str, Any]:
        """
        SQL 쿼리를 실제 데이터베이스에서 실행
        
        Args:
            sql_query: 실행할 SQL 쿼리 객체
            
        Returns:
            실행 결과 딕셔너리
        """
        if not sql_query.is_valid:
            return {
                'success': False,
                'error': 'SQL 쿼리가 유효하지 않습니다.',
                'data': None
            }
        
        start_time = time.time()
        
        try:
            # 데이터베이스 연결
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            logger.info(f"SQL 실행: {sql_query.query}")
            
            # 쿼리 실행
            cursor.execute(sql_query.query)
            
            # 쿼리 타입에 따른 결과 처리
            if sql_query.query_type == 'SELECT':
                # SELECT 쿼리: 결과 반환
                results = cursor.fetchall()
                
                # 결과를 리스트로 변환 (datetime 객체 처리)
                processed_results = []
                for row in results:
                    processed_row = {}
                    for key, value in row.items():
                        if hasattr(value, 'isoformat'):  # datetime 객체
                            processed_row[key] = value.isoformat()
                        else:
                            processed_row[key] = value
                    processed_results.append(processed_row)
                
                execution_time = time.time() - start_time
                
                return {
                    'success': True,
                    'data': processed_results,
                    'row_count': len(processed_results),
                    'execution_time': execution_time,
                    'query_type': 'SELECT'
                }
                
            else:
                # INSERT, UPDATE, DELETE 쿼리: 영향받은 행 수 반환
                affected_rows = cursor.rowcount
                connection.commit()
                
                execution_time = time.time() - start_time
                
                return {
                    'success': True,
                    'data': None,
                    'affected_rows': affected_rows,
                    'execution_time': execution_time,
                    'query_type': sql_query.query_type
                }
                
        except pymysql.Error as e:
            logger.error(f"데이터베이스 오류: {e}")
            return {
                'success': False,
                'error': f'데이터베이스 오류: {str(e)}',
                'data': None,
                'execution_time': time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"SQL 실행 중 예상치 못한 오류: {e}")
            return {
                'success': False,
                'error': f'실행 오류: {str(e)}',
                'data': None,
                'execution_time': time.time() - start_time
            }
            
        finally:
            try:
                if 'cursor' in locals():
                    cursor.close()
                if 'connection' in locals():
                    connection.close()
            except Exception as e:
                logger.warning(f"데이터베이스 연결 종료 중 오류: {e}")

    def test_database_connection(self) -> Dict[str, Any]:
        """
        데이터베이스 연결 테스트
        
        Returns:
            연결 테스트 결과
        """
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()
            
            # 간단한 쿼리 실행
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return {
                'success': True,
                'message': '데이터베이스 연결 성공',
                'test_result': result
            }
            
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_database_schema(self) -> List[Dict[str, Any]]:
        """
        현재 데이터베이스의 테이블 스키마 정보 조회
        
        Returns:
            테이블 스키마 정보 리스트
        """
        try:
            connection = pymysql.connect(**self.db_config)
            cursor = connection.cursor()
            
            # 테이블 목록 조회
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            schema_info = []
            for table in tables:
                table_name = table[0]
                
                # 컬럼 정보 조회
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                # 샘플 데이터 조회 (최대 3행)
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                except:
                    sample_data = []
                
                schema_info.append({
                    'table_name': table_name,
                    'columns': [
                        {
                            'name': col[0],
                            'type': col[1],
                            'null': col[2],
                            'key': col[3],
                            'default': col[4],
                            'extra': col[5]
                        } for col in columns
                    ],
                    'sample_data': sample_data
                })
            
            cursor.close()
            connection.close()
            
            return schema_info
            
        except Exception as e:
            logger.error(f"스키마 정보 조회 실패: {e}")
            return []
    
    def _create_sql_prompt(self, 
                          question: str, 
                          schema: DatabaseSchema,
                          few_shot_examples: List[Dict[str, str]] = None) -> str:
        """SQL 생성 프롬프트 생성"""
        
        # 스키마 정보 포맷팅
        schema_info = f"테이블: {schema.table_name}\n"
        schema_info += "컬럼:\n"
        for col in schema.columns:
            schema_info += f"  - {col['name']} ({col['type']})"
            if 'description' in col:
                schema_info += f": {col['description']}"
            schema_info += "\n"
        
        if schema.primary_key:
            schema_info += f"기본키: {schema.primary_key}\n"
        
        if schema.foreign_keys:
            schema_info += "외래키:\n"
            for fk in schema.foreign_keys:
                schema_info += f"  - {fk['column']} -> {fk['references']}\n"
        
        # 샘플 데이터 추가
        if schema.sample_data:
            schema_info += "샘플 데이터:\n"
            for i, sample in enumerate(schema.sample_data[:3]):  # 최대 3개 샘플
                schema_info += f"  {i+1}: {sample}\n"
        
        # Few-shot 예시 추가
        examples_text = ""
        if few_shot_examples:
            examples_text = "\n예시:\n"
            for example in few_shot_examples:
                examples_text += f"질문: {example['question']}\n"
                examples_text += f"SQL: {example['sql']}\n\n"
        
        # 최종 프롬프트 생성
        prompt = f"""당신은 SQL 전문가입니다. 주어진 스키마를 기반으로 자연어 질문을 SQL로 변환하세요.

{schema_info}

{examples_text}질문: {question}

SQL 쿼리만 출력하세요 (설명 없이):"""
        
        return prompt
    
    def _create_correction_prompt(self,
                                 question: str,
                                 schema: DatabaseSchema,
                                 failed_sql: str,
                                 error_message: str) -> str:
        """SQL 수정 프롬프트 생성"""
        
        schema_info = f"테이블: {schema.table_name}\n"
        schema_info += "컬럼:\n"
        for col in schema.columns:
            schema_info += f"  - {col['name']} ({col['type']})\n"
        
        prompt = f"""SQL 쿼리에 오류가 있습니다. 수정해주세요.

스키마:
{schema_info}

질문: {question}

실패한 SQL: {failed_sql}

오류: {error_message}

수정된 SQL 쿼리만 출력하세요:"""
        
        return prompt
    
    def _call_sql_model(self, prompt: str) -> str:
        """SQL 전용 모델 호출"""
        
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama가 설치되지 않았습니다.")
        
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.1,  # SQL 생성을 위해 낮은 temperature
                    'top_p': 0.9,
                    'max_tokens': 512
                }
            )
            
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"SQL 모델 호출 실패: {e}")
            raise
    
    def _clean_sql(self, raw_sql: str) -> str:
        """SQL 정제"""
        # 불필요한 텍스트 제거
        sql = raw_sql.strip()
        
        # SQL 키워드로 시작하지 않는 경우 처리
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']
        for keyword in sql_keywords:
            if keyword in sql.upper():
                # 해당 키워드부터 시작하도록 자르기
                start_idx = sql.upper().find(keyword)
                sql = sql[start_idx:]
                break
        
        # 세미콜론 제거
        sql = sql.rstrip(';')
        
        return sql
    
    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """SQL 구문 검증"""
        if not self.validation_enabled:
            return {'valid': True}
        
        try:
            # sqlparse를 사용한 구문 검증
            parsed = sqlparse.parse(sql)
            
            # 기본적인 구문 오류 검사
            if not parsed or not parsed[0].tokens:
                return {'valid': False, 'error': '빈 SQL 쿼리'}
            
            # SQL 키워드 확인
            tokens = [token.value.upper() for token in parsed[0].tokens if token.is_keyword]
            if not tokens:
                return {'valid': False, 'error': 'SQL 키워드를 찾을 수 없음'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'구문 오류: {str(e)}'}
    
    def _detect_query_type(self, sql: str) -> str:
        """쿼리 타입 감지"""
        sql_upper = sql.upper().strip()
        
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'UNKNOWN'
    
    def _generate_cache_key(self, question: str, schema: DatabaseSchema) -> str:
        """캐시 키 생성"""
        import hashlib
        
        # 질문과 스키마 정보를 조합하여 해시 생성
        key_data = f"{question}_{schema.table_name}_{str(schema.columns)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def clear_cache(self):
        """캐시 초기화"""
        if self.query_cache:
            self.query_cache.clear()
            logger.info("SQL 쿼리 캐시 초기화")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        if not self.query_cache:
            return {'cache_enabled': False}
        
        return {
            'cache_enabled': True,
            'cache_size': len(self.query_cache),
            'cache_hits': 0,  # TODO: 히트 카운터 구현
            'cache_misses': 0
        }
