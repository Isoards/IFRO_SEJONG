#!/usr/bin/env python3
"""
pyproj를 사용해서 서울 교차로 좌표를 정확하게 변환하는 스크립트
"""

import os
import sys
import pymysql
from pyproj import Transformer
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

def epsg5186_to_wgs84_pyproj(x, y):
    """
    pyproj를 사용해서 EPSG:5186을 WGS84로 정확하게 변환
    """
    try:
        # EPSG:5186 (한국 중부원점)에서 WGS84로 변환
        transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(x, y)
        return lat, lon
    except Exception as e:
        print(f"pyproj 변환 실패: {e}")
        return None, None

def main():
    print("pyproj를 사용해서 서울 교차로 좌표를 정확하게 변환합니다...")
    
    try:
        # 데이터베이스 연결
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 현재 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM traffic_intersection")
        count = cursor.fetchone()[0]
        print(f"총 {count}개의 교차로 데이터를 처리합니다.")
        
        # 샘플 데이터 확인
        cursor.execute("SELECT name, latitude, longitude FROM traffic_intersection LIMIT 3")
        samples = cursor.fetchall()
        print("변환 전 샘플 좌표:")
        for name, lat, lon in samples:
            print(f"  {name}: {lat}, {lon}")
        
        # 원본 EPSG:5186 좌표로부터 올바른 변환 수행
        cursor.execute("SELECT id, name, x_coordinate, y_coordinate FROM traffic_intersection WHERE x_coordinate IS NOT NULL AND y_coordinate IS NOT NULL")
        intersections = cursor.fetchall()
        
        print(f"\n{len(intersections)}개의 교차로 좌표를 변환합니다...")
        
        update_count = 0
        seoul_count = 0
        error_count = 0
        
        for intersection_id, name, x, y in intersections:
            try:
                # EPSG:5186 좌표를 WGS84로 변환
                lat, lon = epsg5186_to_wgs84_pyproj(float(x), float(y))
                
                if lat is None or lon is None:
                    error_count += 1
                    continue
                
                # 서울 범위 확인 (위도 37.4-37.7, 경도 126.8-127.2)
                if 37.4 <= lat <= 37.7 and 126.8 <= lon <= 127.2:
                    seoul_count += 1
                
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
                error_count += 1
                continue
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {update_count}개의 교차로 좌표가 변환되었습니다.")
        print(f"서울 범위 내 교차로: {seoul_count}개")
        print(f"변환 실패: {error_count}개")
        
        # 변환 후 샘플 확인
        cursor.execute("SELECT name, latitude, longitude FROM traffic_intersection LIMIT 5")
        samples = cursor.fetchall()
        print("\n변환 후 샘플 좌표:")
        for name, lat, lon in samples:
            print(f"  {name}: {lat:.6f}, {lon:.6f}")
        
        # 서울 범위 내 교차로 개수 확인
        cursor.execute("""
            SELECT COUNT(*) FROM traffic_intersection 
            WHERE latitude BETWEEN 37.4 AND 37.7 
            AND longitude BETWEEN 126.8 AND 127.2
        """)
        seoul_count_final = cursor.fetchone()[0]
        print(f"\n최종 서울 범위 내 교차로: {seoul_count_final}개")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    main()
