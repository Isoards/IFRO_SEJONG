import os
import sys
import pymysql
from datetime import datetime, timedelta
import random

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'mysql-gpu',
    'port': 3306,
    'user': 'root',
    'password': '1234',
    'database': 'traffic',
    'charset': 'utf8mb4'
}

def generate_total_traffic_volume():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print("광화문 교차로 TotalTrafficVolume 데이터를 생성합니다...")

        # 광화문 교차로 ID 찾기
        cursor.execute("SELECT id FROM traffic_intersection WHERE name = '광화문'")
        result = cursor.fetchone()
        
        if not result:
            print("광화문 교차로를 찾을 수 없습니다.")
            return
            
        intersection_id = result[0]
        print(f"광화문 교차로 ID: {intersection_id}")

        # 기존 TotalTrafficVolume 데이터 삭제
        cursor.execute("DELETE FROM total_traffic_volume WHERE intersection_id = %s", (intersection_id,))
        print("기존 TotalTrafficVolume 데이터 삭제 완료")

        # 2025년 9월 1일부터 25일까지 데이터 생성
        start_date = datetime(2025, 9, 1)
        end_date = datetime(2025, 9, 25)
        
        total_volume_data = []
        current_date = start_date

        while current_date <= end_date:
            for hour in range(24):
                # 요일별 교통량 패턴
                is_weekend = current_date.weekday() >= 5
                
                base_volume = 1000  # 기본 총 교통량
                base_speed = 30     # 기본 평균 속도

                # 시간대별 패턴
                if 7 <= hour < 9 or 17 <= hour < 19:  # 출퇴근 시간
                    volume_multiplier = 1.8
                    speed_multiplier = 0.6
                elif 9 <= hour < 17:  # 주간
                    volume_multiplier = 1.2
                    speed_multiplier = 0.8
                elif 22 <= hour < 24 or 0 <= hour < 6:  # 심야/새벽
                    volume_multiplier = 0.5
                    speed_multiplier = 1.2
                else:
                    volume_multiplier = 1.0
                    speed_multiplier = 1.0
                
                if is_weekend:
                    volume_multiplier *= 0.7
                    speed_multiplier *= 1.2

                # 랜덤 변동성
                volume_variation = random.uniform(0.8, 1.2)
                speed_variation = random.uniform(0.8, 1.2)
                
                # 최종 값 계산
                total_volume = int(base_volume * volume_multiplier * volume_variation)
                average_speed = max(5, min(50, base_speed * speed_multiplier * speed_variation))
                
                traffic_datetime = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                total_volume_data.append({
                    'intersection_id': intersection_id,
                    'datetime': traffic_datetime,
                    'total_volume': total_volume,
                    'average_speed': average_speed
                })
            
            current_date += timedelta(days=1)
        
        # 데이터베이스에 삽입
        print(f"총 {len(total_volume_data)}개의 TotalTrafficVolume 데이터를 삽입합니다...")
        
        for i, data in enumerate(total_volume_data):
            cursor.execute("""
                INSERT INTO total_traffic_volume 
                (intersection_id, datetime, total_volume, average_speed)
                VALUES (%s, %s, %s, %s)
            """, (
                data['intersection_id'],
                data['datetime'],
                data['total_volume'],
                data['average_speed']
            ))
            
            if (i + 1) % 100 == 0:
                print(f"  {i + 1}개 데이터 삽입 완료...")
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {len(total_volume_data)}개의 TotalTrafficVolume 데이터가 생성되었습니다.")
        
        # 샘플 데이터 출력
        print("\n샘플 데이터:")
        for i in range(0, min(5, len(total_volume_data))):
            data = total_volume_data[i]
            print(f"  {data['datetime']}: 총 교통량 {data['total_volume']}대, 평균 속도 {data['average_speed']:.1f}km/h")
        
    except pymysql.Error as e:
        print(f"오류 발생: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    generate_total_traffic_volume()
