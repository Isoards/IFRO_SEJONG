#!/usr/bin/env python3
"""
서울 교차로 데이터를 올바른 좌표로 최종 가져오는 스크립트
"""

import os
import sys
import json
import pymysql
import math
from datetime import datetime

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'mysql-gpu',
    'port': 3306,
    'user': 'root',
    'password': '1234',
    'database': 'traffic',
    'charset': 'utf8mb4'
}

def epsg5186_to_wgs84_correct(x, y):
    """
    EPSG:5186 (한국 중부원점)을 WGS84로 올바르게 변환
    """
    # EPSG:5186의 중앙점 (127.5, 38.0)
    central_lon = 127.5
    central_lat = 38.0
    
    # 좌표 오프셋 계산 (미터 단위)
    x_offset = x - 500000  # X축 오프셋
    y_offset = y - 200000  # Y축 오프셋
    
    # 미터를 도 단위로 변환
    # 1도당 약 111km
    lat_offset = y_offset / 111000
    lon_offset = x_offset / (111000 * math.cos(math.radians(central_lat)))
    
    # 최종 좌표
    lat = central_lat + lat_offset
    lon = central_lon + lon_offset
    
    return lat, lon

def main():
    print("서울 교차로 데이터를 올바른 좌표로 최종 가져옵니다...")
    
    # JSON 파일 경로
    json_path = "/app/seoul_data.json"
    
    try:
        # JSON 데이터 로드
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        intersections = data.get('DATA', [])
        print(f"총 {len(intersections)}개의 교차로 데이터를 처리합니다.")
        
        # 데이터베이스 연결
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 기존 데이터 삭제 (외래키 제약조건 고려)
        print("기존 교차로 데이터를 삭제합니다...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DELETE FROM traffic_intersection")
        cursor.execute("DELETE FROM S_traffic_intersection")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # 새로운 데이터 삽입
        print("새로운 교차로 데이터를 삽입합니다...")
        
        insert_count = 0
        seoul_count = 0
        
        for item in intersections:
            try:
                name = item.get('intr_nm', '').strip()
                x_coord = item.get('xcrd')
                y_coord = item.get('ycrd')
                
                # null 값 체크
                if not name or x_coord is None or y_coord is None or x_coord == 'null' or y_coord == 'null':
                    continue
                
                x_coord = float(x_coord)
                y_coord = float(y_coord)
                
                if x_coord == 0 or y_coord == 0:
                    continue
                
                # EPSG:5186을 WGS84로 변환
                lat, lon = epsg5186_to_wgs84_correct(x_coord, y_coord)
                
                # 서울 범위 확인 (위도 37.4-37.7, 경도 126.8-127.2)
                if 37.4 <= lat <= 37.7 and 126.8 <= lon <= 127.2:
                    seoul_count += 1
                
                # 필수 필드들 설정
                intersection_code = str(item.get('intr_cd', ''))
                intersection_name = name
                intersection_management_number = str(item.get('intr_mng_no', ''))
                coordinate_system = 'EPSG:5186'
                gu_code = str(item.get('gu_cd', ''))
                dong_code = str(item.get('apt_dong_code', ''))
                road_type = str(item.get('road_se', ''))
                intersection_type = str(item.get('type_cd', ''))
                police_station_code = str(item.get('polstn_new_cd', ''))
                business_office_code = str(item.get('tkcg_bsns_ofc_cd', ''))
                lot_number = str(item.get('lotno', ''))
                
                # 데이터베이스에 삽입
                cursor.execute("""
                    INSERT INTO traffic_intersection (
                        name, latitude, longitude, intersection_code, intersection_name,
                        intersection_management_number, x_coordinate, y_coordinate,
                        coordinate_system, gu_code, dong_code, road_type, intersection_type,
                        police_station_code, business_office_code, lot_number,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, lat, lon, intersection_code, intersection_name,
                    intersection_management_number, x_coord, y_coord,
                    coordinate_system, gu_code, dong_code, road_type, intersection_type,
                    police_station_code, business_office_code, lot_number,
                    datetime.now(), datetime.now()
                ))
                
                insert_count += 1
                if insert_count % 1000 == 0:
                    print(f"  {insert_count}개 삽입 완료...")
                    
            except Exception as e:
                print(f"교차로 {name} 처리 실패: {e}")
                continue
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {insert_count}개의 교차로가 삽입되었습니다.")
        print(f"서울 범위 내 교차로: {seoul_count}개")
        
        # 샘플 데이터 확인
        cursor.execute("SELECT name, latitude, longitude FROM traffic_intersection LIMIT 5")
        samples = cursor.fetchall()
        print("\n샘플 좌표:")
        for name, lat, lon in samples:
            print(f"  {name}: {lat:.6f}, {lon:.6f}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    main()
