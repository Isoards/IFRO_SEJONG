#!/usr/bin/env python3
"""
서울 교차로 좌표를 올바르게 변환하는 스크립트
EPSG:5186 (한국 중부원점) -> WGS84 (위도/경도)
"""

import os
import sys
import pymysql
from pyproj import Transformer
import math
from datetime import datetime

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': '1234',
    'database': 'traffic',
    'charset': 'utf8mb4'
}

def epsg5186_to_wgs84_correct(x, y):
    """
    EPSG:5186 (한국 중부원점)을 WGS84로 올바르게 변환
    """
    try:
        # pyproj를 사용한 정확한 변환
        transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(x, y)
        return lat, lon
    except Exception as e:
        print(f"pyproj 변환 실패: {e}")
        # 대안: 근사치 계산 (한국 중부원점 기준)
        # EPSG:5186의 중앙경선: 127.5도, 중앙위도: 38.0도
        # 1도당 약 111km
        lat_offset = (y - 200000) / 111000  # Y축 오프셋을 위도로 변환
        lon_offset = (x - 500000) / (111000 * math.cos(math.radians(38.0)))  # X축 오프셋을 경도로 변환
        
        lat = 38.0 + lat_offset
        lon = 127.5 + lon_offset
        
        return lat, lon

def main():
    print("서울 교차로 좌표를 올바르게 변환합니다...")
    
    try:
        # 데이터베이스 연결
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 현재 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM traffic_intersection")
        count = cursor.fetchone()[0]
        print(f"총 {count}개의 교차로 데이터를 변환합니다.")
        
        # 샘플 데이터 확인
        cursor.execute("SELECT name, latitude, longitude FROM traffic_intersection LIMIT 3")
        samples = cursor.fetchall()
        print("변환 전 샘플 좌표:")
        for name, lat, lon in samples:
            print(f"  {name}: {lat}, {lon}")
        
        # 원본 EPSG:5186 좌표가 저장된 테이블이 있는지 확인
        # 만약 없다면, 현재 좌표를 역변환해서 원본을 복원
        cursor.execute("SHOW COLUMNS FROM traffic_intersection LIKE 'x_coordinate'")
        has_x_coord = cursor.fetchone()
        
        if not has_x_coord:
            print("원본 EPSG:5186 좌표가 없습니다. JSON 파일에서 다시 가져와야 합니다.")
            return
        
        # 원본 좌표로부터 올바른 변환 수행
        cursor.execute("SELECT id, name, x_coordinate, y_coordinate FROM traffic_intersection")
        intersections = cursor.fetchall()
        
        print(f"\n{len(intersections)}개의 교차로 좌표를 변환합니다...")
        
        update_count = 0
        for intersection_id, name, x, y in intersections:
            try:
                # EPSG:5186 좌표를 WGS84로 변환
                lat, lon = epsg5186_to_wgs84_correct(float(x), float(y))
                
                # 데이터베이스 업데이트
                cursor.execute("""
                    UPDATE traffic_intersection 
                    SET latitude = %s, longitude = %s 
                    WHERE id = %s
                """, (lat, lon, intersection_id))
                
                update_count += 1
                if update_count % 1000 == 0:
                    print(f"  {update_count}개 변환 완료...")
                    
            except Exception as e:
                print(f"교차로 {name} 변환 실패: {e}")
                continue
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {update_count}개의 교차로 좌표가 변환되었습니다.")
        
        # 변환 후 샘플 확인
        cursor.execute("SELECT name, latitude, longitude FROM traffic_intersection LIMIT 3")
        samples = cursor.fetchall()
        print("\n변환 후 샘플 좌표:")
        for name, lat, lon in samples:
            print(f"  {name}: {lat}, {lon}")
        
        # 서울 범위 확인 (위도 37.4-37.7, 경도 126.8-127.2)
        cursor.execute("""
            SELECT COUNT(*) FROM traffic_intersection 
            WHERE latitude BETWEEN 37.4 AND 37.7 
            AND longitude BETWEEN 126.8 AND 127.2
        """)
        seoul_count = cursor.fetchone()[0]
        print(f"\n서울 범위 내 교차로: {seoul_count}개")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    main()
