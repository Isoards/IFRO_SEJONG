#!/usr/bin/env python3
"""
서울 교차로 데이터를 올바른 좌표로 다시 가져오는 스크립트
"""

import os
import sys
import json
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
        # 대안: 근사치 계산
        # EPSG:5186의 중앙경선: 127.5도, 중앙위도: 38.0도
        lat_offset = (y - 200000) / 111000
        lon_offset = (x - 500000) / (111000 * math.cos(math.radians(38.0)))
        
        lat = 38.0 + lat_offset
        lon = 127.5 + lon_offset
        
        return lat, lon

def main():
    print("서울 교차로 데이터를 올바른 좌표로 다시 가져옵니다...")
    
    # JSON 파일 경로
    json_path = "/home/aprang2261/IFRO_SEJONG/seoul-intersection-data/서울시 교차로 관련 정보.json"
    
    try:
        # JSON 데이터 로드
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        intersections = data.get('DATA', [])
        print(f"총 {len(intersections)}개의 교차로 데이터를 처리합니다.")
        
        # 데이터베이스 연결
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 기존 데이터 삭제
        print("기존 교차로 데이터를 삭제합니다...")
        cursor.execute("DELETE FROM traffic_intersection")
        cursor.execute("DELETE FROM S_traffic_intersection")
        
        # 새로운 데이터 삽입
        print("새로운 교차로 데이터를 삽입합니다...")
        
        insert_count = 0
        seoul_count = 0
        
        for item in intersections:
            try:
                name = item.get('intr_nm', '').strip()
                x_coord = float(item.get('xcrd', 0))
                y_coord = float(item.get('ycrd', 0))
                
                if not name or x_coord == 0 or y_coord == 0:
                    continue
                
                # EPSG:5186을 WGS84로 변환
                lat, lon = epsg5186_to_wgs84_correct(x_coord, y_coord)
                
                # 서울 범위 확인 (위도 37.4-37.7, 경도 126.8-127.2)
                if 37.4 <= lat <= 37.7 and 126.8 <= lon <= 127.2:
                    seoul_count += 1
                
                # 데이터베이스에 삽입
                cursor.execute("""
                    INSERT INTO traffic_intersection (name, latitude, longitude, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, lat, lon, datetime.now(), datetime.now()))
                
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
