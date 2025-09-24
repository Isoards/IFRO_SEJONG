#!/usr/bin/env python3
"""
광화문 교차로 가상 시나리오 데이터 생성
2025/09/01 ~ 2025/09/25, 1시간 간격
"""

import os
import sys
import json
import pymysql
import random
from datetime import datetime, timedelta
import math

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'mysql-gpu',
    'port': 3306,
    'user': 'root',
    'password': '1234',
    'database': 'traffic',
    'charset': 'utf8mb4'
}

def get_traffic_pattern(hour, day_of_week, is_holiday=False):
    """
    광화문 교차로의 시간대별 교통 패턴 반영
    """
    # 기본 패턴 (평일 기준)
    if is_holiday:
        # 주말/공휴일 패턴
        if 6 <= hour <= 8:
            return {'volume': 0.3, 'speed': 0.8}  # 새벽/아침
        elif 9 <= hour <= 11:
            return {'volume': 0.4, 'speed': 0.7}   # 오전
        elif 12 <= hour <= 14:
            return {'volume': 0.6, 'speed': 0.6}   # 점심시간
        elif 15 <= hour <= 17:
            return {'volume': 0.7, 'speed': 0.5}   # 오후
        elif 18 <= hour <= 20:
            return {'volume': 0.8, 'speed': 0.4}   # 저녁
        elif 21 <= hour <= 23:
            return {'volume': 0.5, 'speed': 0.6}   # 밤
        else:
            return {'volume': 0.2, 'speed': 0.9}    # 심야
    else:
        # 평일 패턴
        if 6 <= hour <= 8:
            return {'volume': 0.8, 'speed': 0.4}   # 출근시간 (매우 혼잡)
        elif 9 <= hour <= 11:
            return {'volume': 0.6, 'speed': 0.6}   # 오전
        elif 12 <= hour <= 14:
            return {'volume': 0.7, 'speed': 0.5}   # 점심시간
        elif 15 <= hour <= 17:
            return {'volume': 0.8, 'speed': 0.4}   # 오후 (혼잡)
        elif 18 <= hour <= 20:
            return {'volume': 0.9, 'speed': 0.3}   # 퇴근시간 (최고 혼잡)
        elif 21 <= hour <= 23:
            return {'volume': 0.5, 'speed': 0.6}   # 밤
        else:
            return {'volume': 0.3, 'speed': 0.8}   # 심야

def get_weather_impact(day_of_month):
    """
    날씨에 따른 교통 영향 (9월 특성 반영)
    """
    # 9월은 가을철로 날씨 변화가 있음
    if day_of_month in [1, 2, 3, 4, 5]:  # 초순 - 맑음
        return {'volume': 1.0, 'speed': 1.0}
    elif day_of_month in [6, 7, 8, 9, 10]:  # 초순 - 흐림
        return {'volume': 0.9, 'speed': 0.8}
    elif day_of_month in [11, 12, 13, 14, 15]:  # 중순 - 맑음
        return {'volume': 1.0, 'speed': 1.0}
    elif day_of_month in [16, 17, 18, 19, 20]:  # 중순 - 비
        return {'volume': 0.7, 'speed': 0.6}
    else:  # 하순 - 맑음
        return {'volume': 1.0, 'speed': 1.0}

def get_event_impact(date):
    """
    특별 이벤트에 따른 교통 영향
    """
    # 9월 특별 이벤트들
    if date.day == 1:  # 9월 1일 - 개학일
        return {'volume': 1.2, 'speed': 0.7}
    elif date.day == 9:  # 9월 9일 - 추석 연휴
        return {'volume': 0.5, 'speed': 0.9}
    elif date.day == 10:  # 9월 10일 - 추석 연휴
        return {'volume': 0.5, 'speed': 0.9}
    elif date.day == 11:  # 9월 11일 - 추석 연휴
        return {'volume': 0.5, 'speed': 0.9}
    elif date.day == 15:  # 9월 15일 - 추석 연휴
        return {'volume': 0.5, 'speed': 0.9}
    elif date.day == 20:  # 9월 20일 - 주말
        return {'volume': 0.8, 'speed': 0.6}
    elif date.day == 21:  # 9월 21일 - 주말
        return {'volume': 0.8, 'speed': 0.6}
    else:
        return {'volume': 1.0, 'speed': 1.0}

def generate_traffic_data():
    """
    광화문 교차로 가상 시나리오 데이터 생성
    """
    print("광화문 교차로 가상 시나리오 데이터를 생성합니다...")
    
    # 광화문 교차로 좌표 (실제 좌표)
    gwanghwamun_lat = 37.5665
    gwanghwamun_lng = 126.9780
    
    # 데이터베이스 연결
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    # 광화문 교차로 찾기 또는 생성
    cursor.execute("SELECT id FROM traffic_intersection WHERE name LIKE '%광화문%' LIMIT 1")
    result = cursor.fetchone()
    
    if result:
        intersection_id = result[0]
        print(f"광화문 교차로 ID: {intersection_id}")
    else:
        # 광화문 교차로가 없으면 생성
        cursor.execute("""
            INSERT INTO traffic_intersection 
            (name, latitude, longitude, intersection_code, intersection_name,
             intersection_management_number, x_coordinate, y_coordinate,
             coordinate_system, gu_code, dong_code, road_type, intersection_type,
             police_station_code, business_office_code, lot_number,
             created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            "광화문교차로", gwanghwamun_lat, gwanghwamun_lng, "GW001", "광화문교차로",
            "GW-001", 0, 0, "WGS84", "110", "110", "001", "001",
            "110", "110", "110", datetime.now(), datetime.now()
        ))
        intersection_id = cursor.lastrowid
        print(f"광화문 교차로 생성 완료, ID: {intersection_id}")
    
    # 기존 데이터 삭제
    cursor.execute("DELETE FROM traffic_trafficvolume WHERE intersection_id = %s", (intersection_id,))
    
    # 2025년 9월 1일부터 25일까지 데이터 생성
    start_date = datetime(2025, 9, 1)
    end_date = datetime(2025, 9, 25)
    
    traffic_data = []
    current_date = start_date
    
    while current_date <= end_date:
        day_of_week = current_date.weekday()  # 0=월요일, 6=일요일
        is_holiday = day_of_week >= 5  # 주말
        
        # 특별 이벤트 확인
        event_impact = get_event_impact(current_date)
        if event_impact['volume'] != 1.0:
            is_holiday = True  # 이벤트일은 주말로 처리
        
        # 날씨 영향
        weather_impact = get_weather_impact(current_date.day)
        
        # 하루 24시간 데이터 생성
        for hour in range(24):
            # 기본 교통 패턴
            pattern = get_traffic_pattern(hour, day_of_week, is_holiday)
            
            # 날씨 영향 적용
            volume_multiplier = pattern['volume'] * weather_impact['volume'] * event_impact['volume']
            speed_multiplier = pattern['speed'] * weather_impact['speed'] * event_impact['speed']
            
            # 광화문 교차로 특성 반영
            base_volume = 1500  # 기본 교통량 (광화문은 매우 혼잡한 교차로)
            base_speed = 25     # 기본 속도 (km/h)
            
            # 실제같은 변동성 추가
            volume_variation = random.uniform(0.8, 1.2)
            speed_variation = random.uniform(0.9, 1.1)
            
            # 최종 값 계산
            total_volume = int(base_volume * volume_multiplier * volume_variation)
            average_speed = max(5, min(50, base_speed * speed_multiplier * speed_variation))
            
            # 데이터 생성 (4방향 교통량)
            traffic_datetime = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            # 4방향 교통량 생성 (동, 서, 남, 북)
            directions = ['E', 'W', 'S', 'N']  # East, West, South, North
            for direction in directions:
                # 방향별 교통량 차이 (광화문은 동서축이 더 혼잡)
                if direction in ['E', 'W']:
                    direction_volume = int(total_volume * 0.6)  # 동서축 60%
                else:
                    direction_volume = int(total_volume * 0.4)  # 남북축 40%
                
                traffic_data.append({
                    'intersection_id': intersection_id,
                    'datetime': traffic_datetime,
                    'direction': direction,
                    'volume': direction_volume,
                    'is_simulated': 1,  # 시뮬레이션 데이터
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
        
        current_date += timedelta(days=1)
    
    # 데이터베이스에 삽입
    print(f"총 {len(traffic_data)}개의 데이터를 삽입합니다...")
    
    for i, data in enumerate(traffic_data):
        cursor.execute("""
            INSERT INTO traffic_trafficvolume 
            (intersection_id, datetime, direction, volume, is_simulated, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['intersection_id'],
            data['datetime'],
            data['direction'],
            data['volume'],
            data['is_simulated'],
            data['created_at'],
            data['updated_at']
        ))
        
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}개 데이터 삽입 완료...")
    
    # 변경사항 저장
    connection.commit()
    print(f"\n총 {len(traffic_data)}개의 광화문 교차로 데이터가 생성되었습니다.")
    
    # 샘플 데이터 출력
    print("\n샘플 데이터:")
    for i in range(0, min(8, len(traffic_data))):
        data = traffic_data[i]
        print(f"  {data['datetime']}: {data['direction']}방향 교통량 {data['volume']}대")
    
    connection.close()

if __name__ == "__main__":
    generate_traffic_data()
