#!/usr/bin/env python
import os
import sys
import json
import django
from django.db import connection, transaction
from datetime import datetime

# Django 설정
sys.path.append('/app/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

def epsg5186_to_latlon(x, y):
    """
    EPSG:5186 (Korea 2000 / Korea Central Belt 2010) 좌표를 WGS84 위도/경도로 변환
    """
    try:
        from pyproj import Transformer
        
        # EPSG:5186에서 WGS84 (EPSG:4326)로 변환
        transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(x, y)
        
        return lat, lon
        
    except ImportError:
        # pyproj가 없는 경우 근사치 변환 사용
        import math
        
        # EPSG:5186은 한국 중부원점 좌표계
        # 근사치 변환 (정확하지 않으므로 pyproj 사용 권장)
        lat = 37.5 + (y - 200000) / 111000.0
        lon = 127.0 + (x - 500000) / (111000.0 * math.cos(math.radians(37.5)))
        
        return lat, lon

def clear_existing_data():
    """기존 교차로 데이터 삭제"""
    print("기존 교차로 데이터를 삭제하는 중...")
    
    with connection.cursor() as cursor:
        # 외래키 제약조건을 일시적으로 비활성화
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 관련 테이블들 삭제
        tables_to_clear = [
            'traffic_trafficflowanalysisfavorite',
            'traffic_trafficflowanalysisstats', 
            'traffic_trafficinterpretation',
            'traffic_trafficvolume',
            'total_traffic_volume',
            'traffic_incident',
            'S_traffic_volume',
            'S_total_traffic_volume', 
            'S_traffic_interpretation',
            'S_incident',
            'traffic_intersectionstats',
            'traffic_intersectionviewlog',
            'traffic_intersectionfavoritelog',
            'traffic_policyproposal',
            'traffic_proposalattachment',
            'traffic_proposalvote',
            'traffic_proposalviewlog',
            'traffic_proposaltag',
            'traffic_intersection'
        ]
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"✓ {table} 데이터 삭제 완료")
            except Exception as e:
                print(f"⚠ {table} 삭제 중 오류 (테이블이 존재하지 않을 수 있음): {e}")
        
        # 외래키 제약조건 재활성화
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    print("기존 데이터 삭제 완료!")

def import_seoul_intersections():
    """서울 교차로 데이터를 MySQL에 삽입"""
    print("서울 교차로 데이터를 가져오는 중...")
    
    # JSON 파일 경로
    json_path = '/home/aprang2261/IFRO_SEJONG/seoul-intersection-data/서울시 교차로 관련 정보.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    intersections_data = data.get('DATA', [])
    print(f"총 {len(intersections_data)}개의 교차로 데이터를 발견했습니다.")
    
    # 교차로 데이터 변환 및 삽입
    intersections_to_insert = []
    processed_count = 0
    
    for item in intersections_data:
        try:
            # 교차로명칭
            name = item.get('intr_nm', '').strip()
            if not name:
                continue
                
            # X, Y 좌표 (UTM-K)
            x_coord = item.get('xcrd')
            y_coord = item.get('ycrd')
            
            if not x_coord or not y_coord:
                continue
                
            # EPSG:5186을 위도/경도로 변환
            try:
                latitude, longitude = epsg5186_to_latlon(float(x_coord), float(y_coord))
            except (ValueError, TypeError):
                continue
            
            # 교차로 데이터 추가
            intersections_to_insert.append({
                'name': name,
                'latitude': latitude,
                'longitude': longitude,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            
            processed_count += 1
            
            if processed_count % 1000 == 0:
                print(f"처리 중... {processed_count}개 완료")
                
        except Exception as e:
            print(f"데이터 처리 중 오류: {e}")
            continue
    
    print(f"변환 완료: {len(intersections_to_insert)}개의 교차로 데이터")
    
    # MySQL에 일괄 삽입
    if intersections_to_insert:
        print("MySQL 데이터베이스에 삽입하는 중...")
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                # 교차로 데이터 일괄 삽입
                insert_query = """
                INSERT INTO traffic_intersection (name, latitude, longitude, created_at, updated_at)
                VALUES (%(name)s, %(latitude)s, %(longitude)s, %(created_at)s, %(updated_at)s)
                """
                
                cursor.executemany(insert_query, intersections_to_insert)
                
        print(f"✓ {len(intersections_to_insert)}개의 교차로가 성공적으로 삽입되었습니다!")
    
    return len(intersections_to_insert)

def main():
    """메인 실행 함수"""
    print("=== 서울 교차로 데이터 임포트 시작 ===")
    
    try:
        # 1. 기존 데이터 삭제
        clear_existing_data()
        
        # 2. 서울 교차로 데이터 임포트
        inserted_count = import_seoul_intersections()
        
        print(f"\n=== 임포트 완료 ===")
        print(f"총 {inserted_count}개의 서울 교차로가 데이터베이스에 추가되었습니다.")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("서울 교차로 데이터 임포트가 성공적으로 완료되었습니다!")
    else:
        print("서울 교차로 데이터 임포트 중 오류가 발생했습니다.")
