#!/usr/bin/env python
import os
import sys
import pymysql
from pathlib import Path

# === DB 연결 설정 ===
DB_CONFIG = {
    "host": os.getenv('MYSQL_HOST', 'localhost'),
    "user": os.getenv('MYSQL_USER', 'root'),
    "password": os.getenv('MYSQL_PASSWORD', '1234'),
    "database": os.getenv('MYSQL_DATABASE', 'traffic'),
    "charset": "utf8mb4",
    "port": int(os.getenv('MYSQL_PORT', 3307))
}

def epsg5186_to_latlon(x, y):
    """
    EPSG:5186 (Korea 2000 / Korea Central Belt 2010) 좌표를 WGS84 위도/경도로 변환
    근사치 변환 사용
    """
    import math
    
    # EPSG:5186은 한국 중부원점 좌표계
    # 근사치 변환 (정확하지 않으므로 pyproj 사용 권장)
    lat = 37.5 + (y - 200000) / 111000.0
    lon = 127.0 + (x - 500000) / (111000.0 * math.cos(math.radians(37.5)))
    
    return lat, lon

def convert_coordinates():
    """좌표 변환 및 업데이트"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 모든 교차로 데이터 가져오기
        cursor.execute("SELECT id, x_coordinate, y_coordinate FROM traffic_intersection")
        rows = cursor.fetchall()
        print(f"총 {len(rows)}개의 교차로 데이터를 변환합니다.")
        
        updated = 0
        for row in rows:
            id_, x, y = row
            try:
                # EPSG:5186을 위도/경도로 변환
                latitude, longitude = epsg5186_to_latlon(float(x), float(y))
                
                # 데이터베이스 업데이트
                cursor.execute(
                    "UPDATE traffic_intersection SET latitude = %s, longitude = %s WHERE id = %s",
                    (latitude, longitude, id_)
                )
                updated += 1
                
                if updated % 1000 == 0:
                    print(f"변환 중... {updated}개 완료")
                    
            except Exception as e:
                print(f"❌ {id_}번 교차로 변환 실패: {e}")
                continue
        
        conn.commit()
        print(f"✅ {updated}개 교차로 좌표 변환 완료!")
        
    except Exception as e:
        print(f"❌ 변환 실패: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    print("=== 좌표 변환 시작 ===")
    convert_coordinates()
    print("=== 좌표 변환 완료 ===")
