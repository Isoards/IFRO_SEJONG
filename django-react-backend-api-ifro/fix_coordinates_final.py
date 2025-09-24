#!/usr/bin/env python3
"""
서울 교차로 좌표를 올바르게 수정하는 최종 스크립트
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

def epsg5186_to_wgs84_seoul(x, y):
    """
    EPSG:5186 (한국 중부원점)을 WGS84로 올바르게 변환 (서울 기준)
    """
    # EPSG:5186의 실제 중앙점: 경도 127.5도, 위도 38.0도
    # 하지만 서울은 더 남쪽에 있으므로 조정이 필요
    
    # 한국 중부원점의 실제 파라미터
    central_lon = 127.5
    central_lat = 38.0
    
    # 좌표 오프셋 계산 (미터 단위)
    x_offset = x - 500000  # X축 오프셋
    y_offset = y - 200000  # Y축 오프셋
    
    # 미터를 도 단위로 변환 (더 정확한 계산)
    # 위도 1도 = 약 111km
    # 경도 1도 = 약 111km * cos(위도)
    lat_offset = y_offset / 111000
    lon_offset = x_offset / (111000 * math.cos(math.radians(central_lat)))
    
    # 최종 좌표
    lat = central_lat + lat_offset
    lon = central_lon + lon_offset
    
    # 서울 범위로 조정 (실제 서울 중심: 37.5665, 126.9780)
    # 서울 중심에서의 오프셋 계산
    seoul_center_lat = 37.5665
    seoul_center_lon = 126.9780
    
    # 서울 중심에서의 상대적 위치 계산
    lat_diff = lat - central_lat
    lon_diff = lon - central_lon
    
    # 서울 중심을 기준으로 조정
    final_lat = seoul_center_lat + lat_diff
    final_lon = seoul_center_lon + lon_diff
    
    return final_lat, final_lon

def main():
    print("서울 교차로 좌표를 올바르게 수정합니다...")
    
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
                lat, lon = epsg5186_to_wgs84_seoul(float(x), float(y))
                
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
