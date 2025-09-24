#!/usr/bin/env python3
"""
서울 교차로 좌표를 수동으로 수정하는 스크립트
"""

import os
import sys
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

def epsg5186_to_wgs84_manual(x, y):
    """
    EPSG:5186을 WGS84로 수동 변환 (서울 중심 기준)
    """
    # 서울 중심 좌표
    seoul_center_lat = 37.5665
    seoul_center_lon = 126.9780
    
    # EPSG:5186의 중앙점
    center_lat = 38.0
    center_lon = 127.5
    
    # 좌표 오프셋 계산
    x_offset = x - 500000  # 동서 오프셋
    y_offset = y - 200000  # 남북 오프셋
    
    # 미터를 도 단위로 변환 (1도 = 111,320m)
    lat_offset = y_offset / 111320
    lon_offset = x_offset / (111320 * math.cos(math.radians(center_lat)))
    
    # 중앙점에서 오프셋 적용
    lat = center_lat + lat_offset
    lon = center_lon + lon_offset
    
    # 서울 중심으로 조정 (중앙점에서 서울 중심까지의 거리)
    lat_diff = seoul_center_lat - center_lat
    lon_diff = seoul_center_lon - center_lon
    
    # 최종 좌표
    final_lat = lat + lat_diff
    final_lon = lon + lon_diff
    
    return final_lat, final_lon

def main():
    print("서울 교차로 좌표를 수동으로 수정합니다...")
    
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
        print("수정 전 샘플 좌표:")
        for name, lat, lon in samples:
            print(f"  {name}: {lat}, {lon}")
        
        # 원본 EPSG:5186 좌표로부터 올바른 변환 수행
        cursor.execute("SELECT id, name, x_coordinate, y_coordinate FROM traffic_intersection WHERE x_coordinate IS NOT NULL AND y_coordinate IS NOT NULL")
        intersections = cursor.fetchall()
        
        print(f"\n{len(intersections)}개의 교차로 좌표를 변환합니다...")
        
        update_count = 0
        seoul_count = 0
        
        for intersection_id, name, x, y in intersections:
            try:
                # EPSG:5186 좌표를 WGS84로 변환
                lat, lon = epsg5186_to_wgs84_manual(float(x), float(y))
                
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
                continue
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {update_count}개의 교차로 좌표가 변환되었습니다.")
        print(f"서울 범위 내 교차로: {seoul_count}개")
        
        # 변환 후 샘플 확인
        cursor.execute("SELECT name, latitude, longitude FROM traffic_intersection LIMIT 5")
        samples = cursor.fetchall()
        print("\n변환 후 샘플 좌표:")
        for name, lat, lon in samples:
            print(f"  {name}: {lat:.6f}, {lon:.6f}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    main()
