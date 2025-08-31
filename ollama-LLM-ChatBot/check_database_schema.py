#!/usr/bin/env python3
"""
데이터베이스 스키마 확인 및 데이터 조회

실제 데이터베이스의 테이블 구조를 확인하고 데이터를 조회하는 기능
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))

from core.real_database_executor import RealDatabaseExecutor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_get_value(result, key, index=0):
    """결과에서 안전하게 값을 추출"""
    if hasattr(result, 'values'):
        return result.get(key)
    elif isinstance(result, (list, tuple)):
        return result[index] if index < len(result) else None
    else:
        return result

def check_database_schema():
    """데이터베이스 스키마 확인"""
    
    print("=" * 60)
    print("데이터베이스 스키마 확인")
    print("=" * 60)
    
    db_executor = RealDatabaseExecutor()
    
    if not db_executor.connect():
        print("✗ 데이터베이스 연결 실패")
        return
    
    try:
        cursor = db_executor.connection.cursor()
        
        # 1. 테이블 목록 확인
        print("\n1. 테이블 목록:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = safe_get_value(table, 'Tables_in_traffic', 0)
            print(f"  - {table_name}")
        
        # 2. 주요 traffic 테이블 구조 확인
        main_tables = ['traffic_intersection', 'traffic_trafficvolume', 'traffic_incident']
        
        print(f"\n2. 주요 Traffic 테이블 구조:")
        for table_name in main_tables:
            print(f"\n  테이블: {table_name}")
            
            # 테이블 구조 확인
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            print("    컬럼:")
            for col in columns:
                field = safe_get_value(col, 'Field', 0)
                field_type = safe_get_value(col, 'Type', 1)
                nullable = safe_get_value(col, 'Null', 2)
                print(f"      - {field}: {field_type} ({nullable})")
            
            # 데이터 개수 확인
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count_result = cursor.fetchone()
            count = safe_get_value(count_result, 'count', 0)
            print(f"    데이터 개수: {count:,}개")
            
            # 샘플 데이터 확인
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            sample_data = cursor.fetchall()
            
            if sample_data:
                print("    샘플 데이터:")
                for i, row in enumerate(sample_data, 1):
                    print(f"      {i}. {row}")
            else:
                print("    샘플 데이터: 없음")
        
        cursor.close()
        
    except Exception as e:
        print(f"✗ 스키마 확인 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_executor.disconnect()

def get_traffic_data_sample():
    """교통 데이터 샘플 조회"""
    
    print("\n" + "=" * 60)
    print("교통 데이터 샘플 조회")
    print("=" * 60)
    
    db_executor = RealDatabaseExecutor()
    
    if not db_executor.connect():
        print("✗ 데이터베이스 연결 실패")
        return
    
    try:
        cursor = db_executor.connection.cursor()
        
        # 1. 세종특별자치시 교차로 목록
        print("\n1. 세종특별자치시 교차로 목록:")
        cursor.execute("""
            SELECT id, name, latitude, longitude
            FROM traffic_intersection
            WHERE name LIKE '%세종%'
            ORDER BY name
            LIMIT 10
        """)
        
        intersections = cursor.fetchall()
        for i, row in enumerate(intersections, 1):
            name = safe_get_value(row, 'name', 1)
            intersection_id = safe_get_value(row, 'id', 0)
            latitude = safe_get_value(row, 'latitude', 2)
            longitude = safe_get_value(row, 'longitude', 3)
            print(f"  {i}. {name} (ID: {intersection_id}) - 좌표: ({latitude}, {longitude})")
        
        # 2. 특정 교차로의 교통량 데이터
        if intersections:
            intersection_id = safe_get_value(intersections[0], 'id', 0)
            print(f"\n2. 교차로 ID {intersection_id}의 교통량 데이터:")
            
            cursor.execute("""
                SELECT datetime, direction, volume, is_simulated
                FROM traffic_trafficvolume
                WHERE intersection_id = %s
                ORDER BY datetime DESC
                LIMIT 10
            """, (intersection_id,))
            
            volumes = cursor.fetchall()
            for i, row in enumerate(volumes, 1):
                datetime_val = safe_get_value(row, 'datetime', 0)
                direction = safe_get_value(row, 'direction', 1)
                volume = safe_get_value(row, 'volume', 2)
                is_simulated = safe_get_value(row, 'is_simulated', 3)
                simulated = "시뮬레이션" if is_simulated else "실제"
                print(f"  {i}. {datetime_val} - 방향: {direction}, 교통량: {volume} ({simulated})")
        
        # 3. 최근 사고 데이터
        print(f"\n3. 최근 사고 데이터:")
        cursor.execute("""
            SELECT incident_id, district, intersection_name, incident_type, status, registered_at
            FROM traffic_incident
            ORDER BY registered_at DESC
            LIMIT 5
        """)
        
        incidents = cursor.fetchall()
        for i, row in enumerate(incidents, 1):
            registered_at = safe_get_value(row, 'registered_at', 5)
            district = safe_get_value(row, 'district', 1)
            intersection_name = safe_get_value(row, 'intersection_name', 2)
            incident_type = safe_get_value(row, 'incident_type', 3)
            status = safe_get_value(row, 'status', 4)
            print(f"  {i}. {registered_at} - {district} {intersection_name}")
            print(f"     유형: {incident_type}, 상태: {status}")
        
        cursor.close()
        
    except Exception as e:
        print(f"✗ 데이터 샘플 조회 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_executor.disconnect()

def get_traffic_data_by_region(region_name="세종"):
    """지역별 교통 데이터 조회"""
    
    print(f"\n" + "=" * 60)
    print(f"{region_name} 지역 교통 데이터 조회")
    print("=" * 60)
    
    db_executor = RealDatabaseExecutor()
    
    if not db_executor.connect():
        print("✗ 데이터베이스 연결 실패")
        return
    
    try:
        cursor = db_executor.connection.cursor()
        
        # 1. 지역별 교차로 목록
        print(f"\n1. {region_name} 지역 교차로 목록:")
        cursor.execute("""
            SELECT id, name, latitude, longitude
            FROM traffic_intersection
            WHERE name LIKE %s
            ORDER BY name
        """, (f'%{region_name}%',))
        
        intersections = cursor.fetchall()
        print(f"총 {len(intersections)}개의 교차로 발견")
        
        for i, row in enumerate(intersections[:10], 1):  # 상위 10개만 표시
            name = safe_get_value(row, 'name', 1)
            intersection_id = safe_get_value(row, 'id', 0)
            latitude = safe_get_value(row, 'latitude', 2)
            longitude = safe_get_value(row, 'longitude', 3)
            print(f"  {i}. {name} (ID: {intersection_id}) - 좌표: ({latitude}, {longitude})")
        
        if len(intersections) > 10:
            print(f"  ... 외 {len(intersections) - 10}개")
        
        # 2. 지역별 교통량 통계
        print(f"\n2. {region_name} 지역 교통량 통계:")
        cursor.execute("""
            SELECT 
                ti.id,
                ti.name,
                COUNT(tv.id) as volume_count,
                AVG(tv.volume) as avg_volume,
                MAX(tv.volume) as max_volume,
                MIN(tv.datetime) as first_record,
                MAX(tv.datetime) as last_record
            FROM traffic_intersection ti
            LEFT JOIN traffic_trafficvolume tv ON ti.id = tv.intersection_id
            WHERE ti.name LIKE %s
            GROUP BY ti.id, ti.name
            ORDER BY volume_count DESC
            LIMIT 10
        """, (f'%{region_name}%',))
        
        traffic_stats = cursor.fetchall()
        for i, row in enumerate(traffic_stats, 1):
            name = safe_get_value(row, 'name', 1)
            intersection_id = safe_get_value(row, 'id', 0)
            volume_count = safe_get_value(row, 'volume_count', 2)
            avg_volume = safe_get_value(row, 'avg_volume', 3)
            max_volume = safe_get_value(row, 'max_volume', 4)
            first_record = safe_get_value(row, 'first_record', 5)
            last_record = safe_get_value(row, 'last_record', 6)
            
            print(f"  {i}. {name} (ID: {intersection_id})")
            print(f"     기록 수: {volume_count}개, 평균 교통량: {avg_volume:.1f}, 최대 교통량: {max_volume}")
            print(f"     기간: {first_record} ~ {last_record}")
        
        # 3. 지역별 사고 통계
        print(f"\n3. {region_name} 지역 사고 통계:")
        cursor.execute("""
            SELECT 
                incident_type,
                COUNT(*) as count,
                COUNT(DISTINCT district) as district_count,
                COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_count,
                COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_count,
                COUNT(CASE WHEN status = 'IN_PROGRESS' THEN 1 END) as in_progress_count
            FROM traffic_incident
            WHERE district LIKE %s OR intersection_name LIKE %s
            GROUP BY incident_type
            ORDER BY count DESC
        """, (f'%{region_name}%', f'%{region_name}%'))
        
        incident_stats = cursor.fetchall()
        for row in incident_stats:
            incident_type = safe_get_value(row, 'incident_type', 0)
            count = safe_get_value(row, 'count', 1)
            district_count = safe_get_value(row, 'district_count', 2)
            open_count = safe_get_value(row, 'open_count', 3)
            closed_count = safe_get_value(row, 'closed_count', 4)
            in_progress_count = safe_get_value(row, 'in_progress_count', 5)
            
            print(f"  - {incident_type}: {count}건 (지역: {district_count}개)")
            print(f"    상태별: 진행중 {in_progress_count}건, 대기중 {open_count}건, 완료 {closed_count}건")
        
        cursor.close()
        
    except Exception as e:
        print(f"✗ 지역별 데이터 조회 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_executor.disconnect()

def get_traffic_volume_by_time(intersection_id=None, start_date=None, end_date=None):
    """시간대별 교통량 데이터 조회"""
    
    print(f"\n" + "=" * 60)
    print("시간대별 교통량 데이터 조회")
    print("=" * 60)
    
    db_executor = RealDatabaseExecutor()
    
    if not db_executor.connect():
        print("✗ 데이터베이스 연결 실패")
        return
    
    try:
        cursor = db_executor.connection.cursor()
        
        # 기본값 설정
        if not intersection_id:
            # 첫 번째 세종 교차로 사용
            cursor.execute("SELECT id FROM traffic_intersection WHERE name LIKE '%세종%' LIMIT 1")
            result = cursor.fetchone()
            intersection_id = safe_get_value(result, 'id', 0)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        
        if not end_date:
            end_date = datetime.now()
        
        # 교차로 정보 조회
        cursor.execute("SELECT name FROM traffic_intersection WHERE id = %s", (intersection_id,))
        result = cursor.fetchone()
        intersection_name = safe_get_value(result, 'name', 0)
        
        print(f"\n교차로: {intersection_name} (ID: {intersection_id})")
        print(f"기간: {start_date} ~ {end_date}")
        
        # 시간대별 교통량 통계
        cursor.execute("""
            SELECT 
                DATE(datetime) as date,
                HOUR(datetime) as hour,
                direction,
                AVG(volume) as avg_volume,
                MAX(volume) as max_volume,
                MIN(volume) as min_volume,
                COUNT(*) as record_count
            FROM traffic_trafficvolume
            WHERE intersection_id = %s 
                AND datetime BETWEEN %s AND %s
            GROUP BY DATE(datetime), HOUR(datetime), direction
            ORDER BY date DESC, hour DESC, direction
            LIMIT 20
        """, (intersection_id, start_date, end_date))
        
        volume_stats = cursor.fetchall()
        
        if volume_stats:
            print(f"\n시간대별 교통량 통계 (최근 20개):")
            for row in volume_stats:
                date = safe_get_value(row, 'date', 0)
                hour = safe_get_value(row, 'hour', 1)
                direction = safe_get_value(row, 'direction', 2)
                avg_volume = safe_get_value(row, 'avg_volume', 3)
                max_volume = safe_get_value(row, 'max_volume', 4)
                min_volume = safe_get_value(row, 'min_volume', 5)
                record_count = safe_get_value(row, 'record_count', 6)
                
                print(f"  {date} {hour:02d}:00 - {direction}방향")
                print(f"    평균: {avg_volume:.1f}, 최대: {max_volume}, 최소: {min_volume} (기록: {record_count}개)")
        else:
            print("해당 기간에 교통량 데이터가 없습니다.")
        
        cursor.close()
        
    except Exception as e:
        print(f"✗ 시간대별 교통량 조회 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_executor.disconnect()

if __name__ == "__main__":
    # 기본 스키마 확인
    check_database_schema()
    
    # 데이터 샘플 조회
    get_traffic_data_sample()
    
    # 지역별 데이터 조회
    get_traffic_data_by_region("세종")
    
    # 시간대별 교통량 조회
    get_traffic_volume_by_time()
