import os
import sys
import pymysql
from datetime import datetime as dt, timedelta
import random
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

def get_intersection_characteristics(intersection_name):
    """교차로명을 기반으로 특성 파악"""
    characteristics = {
        'base_volume': 500,  # 기본 교통량
        'base_speed': 30,     # 기본 속도
        'peak_multiplier': 1.5,  # 출퇴근 시간 배수
        'weekend_multiplier': 0.8,  # 주말 배수
        'night_multiplier': 0.3,    # 심야 배수
        'traffic_type': 'normal'  # 교통 유형
    }
    
    name_lower = intersection_name.lower()
    
    # 관광지/명소 특성
    if any(keyword in name_lower for keyword in ['광화문', '명동', '동대문', '남대문', '경복궁', '청계천', '한강', '63빌딩', '롯데월드', '에버랜드']):
        characteristics.update({
            'base_volume': 800,
            'base_speed': 25,
            'peak_multiplier': 2.0,
            'weekend_multiplier': 1.2,  # 주말에 더 활발
            'traffic_type': 'tourist'
        })
    
    # 상업지구 특성
    elif any(keyword in name_lower for keyword in ['강남', '신촌', '홍대', '이태원', '압구정', '청담', '삼성', '잠실', '건대', '성신여대']):
        characteristics.update({
            'base_volume': 700,
            'base_speed': 28,
            'peak_multiplier': 1.8,
            'weekend_multiplier': 1.1,
            'traffic_type': 'commercial'
        })
    
    # 주거지역 특성
    elif any(keyword in name_lower for keyword in ['아파트', '단지', '마을', '동네', '주민센터', '학교', '병원', '시장']):
        characteristics.update({
            'base_volume': 400,
            'base_speed': 32,
            'peak_multiplier': 1.3,
            'weekend_multiplier': 0.9,
            'traffic_type': 'residential'
        })
    
    # 업무지구 특성
    elif any(keyword in name_lower for keyword in ['여의도', '마포', '영등포', '구로', '가산', '판교', '분당', '일산']):
        characteristics.update({
            'base_volume': 600,
            'base_speed': 26,
            'peak_multiplier': 1.7,
            'weekend_multiplier': 0.7,
            'traffic_type': 'business'
        })
    
    # 교육기관 특성
    elif any(keyword in name_lower for keyword in ['대학교', '고등학교', '중학교', '초등학교', '학교', '캠퍼스']):
        characteristics.update({
            'base_volume': 350,
            'base_speed': 35,
            'peak_multiplier': 1.4,
            'weekend_multiplier': 0.6,
            'traffic_type': 'educational'
        })
    
    # 교통요충지 특성
    elif any(keyword in name_lower for keyword in ['역', '지하철', '버스', '터미널', '공항', '고속도로', '터널', '대교']):
        characteristics.update({
            'base_volume': 900,
            'base_speed': 22,
            'peak_multiplier': 2.2,
            'weekend_multiplier': 1.0,
            'traffic_type': 'transportation'
        })
    
    return characteristics

def generate_traffic_pattern(characteristics, hour, is_weekend, date):
    """교차로 특성에 따른 교통 패턴 생성"""
    base_volume = characteristics['base_volume']
    base_speed = characteristics['base_speed']
    peak_multiplier = characteristics['peak_multiplier']
    weekend_multiplier = characteristics['weekend_multiplier']
    night_multiplier = characteristics['night_multiplier']
    traffic_type = characteristics['traffic_type']
    
    # 시간대별 패턴
    if 7 <= hour < 9:  # 출근 시간
        volume_multiplier = peak_multiplier
        speed_multiplier = 0.6
    elif 17 <= hour < 19:  # 퇴근 시간
        volume_multiplier = peak_multiplier
        speed_multiplier = 0.6
    elif 9 <= hour < 17:  # 주간
        volume_multiplier = 1.2
        speed_multiplier = 0.8
    elif 22 <= hour < 24 or 0 <= hour < 6:  # 심야/새벽
        volume_multiplier = night_multiplier
        speed_multiplier = 1.2
    else:  # 저녁
        volume_multiplier = 1.0
        speed_multiplier = 1.0
    
    # 주말 패턴
    if is_weekend:
        volume_multiplier *= weekend_multiplier
        speed_multiplier *= 1.1
    
    # 교통 유형별 특별 패턴
    if traffic_type == 'tourist':
        # 관광지는 주말과 저녁에 더 활발
        if is_weekend or 18 <= hour < 22:
            volume_multiplier *= 1.3
    elif traffic_type == 'business':
        # 업무지는 주말에 매우 한산
        if is_weekend:
            volume_multiplier *= 0.5
    elif traffic_type == 'educational':
        # 교육기관은 방학 중이므로 교통량 감소
        volume_multiplier *= 0.7
    elif traffic_type == 'transportation':
        # 교통요충지는 항상 활발
        volume_multiplier *= 1.1
    
    # 날씨 영향 (9월 특성)
    weather_impact = 1.0
    if 9 <= date.day <= 11:  # 추석 연휴
        if traffic_type == 'tourist':
            weather_impact = 1.5  # 관광지 활발
        else:
            weather_impact = 0.7  # 일반 지역 한산
    elif 12 <= date.day <= 18:  # 중순 (비 오는 날)
        weather_impact = 0.8  # 교통량 감소
    elif 19 <= date.day <= 25:  # 하순 (맑은 날)
        weather_impact = 1.1  # 교통량 증가
    
    # 랜덤 변동성
    volume_variation = random.uniform(0.8, 1.2)
    speed_variation = random.uniform(0.8, 1.2)
    
    # 최종 값 계산
    total_volume = int(base_volume * volume_multiplier * volume_variation * weather_impact)
    average_speed = max(5, min(60, base_speed * speed_multiplier * speed_variation))
    
    return total_volume, average_speed

def generate_all_intersections_data():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print("서울시 모든 교차로 교통 데이터를 생성합니다...")

        # 모든 교차로 가져오기
        cursor.execute("SELECT id, name FROM traffic_intersection")
        intersections = cursor.fetchall()
        print(f"총 {len(intersections)}개의 교차로 데이터 생성")

        # 기존 데이터 삭제
        cursor.execute("DELETE FROM total_traffic_volume")
        cursor.execute("DELETE FROM traffic_trafficvolume")
        print("기존 교통 데이터 삭제 완료")

        # 2025년 9월 1일부터 25일까지 데이터 생성
        start_date = dt(2025, 9, 1)
        end_date = dt(2025, 9, 25)
        
        total_records = 0
        current_date = start_date

        while current_date <= end_date:
            is_weekend = current_date.weekday() >= 5
            
            for intersection_id, intersection_name in intersections:
                # 교차로 특성 파악
                characteristics = get_intersection_characteristics(intersection_name)
                
                for hour in range(24):
                    # 교통 패턴 생성
                    total_volume, average_speed = generate_traffic_pattern(
                        characteristics, hour, is_weekend, current_date
                    )
                    
                    traffic_datetime = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    
                    # TotalTrafficVolume 데이터 삽입
                    cursor.execute("""
                        INSERT INTO total_traffic_volume 
                        (intersection_id, datetime, total_volume, average_speed)
                        VALUES (%s, %s, %s, %s)
                    """, (intersection_id, traffic_datetime, total_volume, average_speed))
                    
                    # TrafficVolume 데이터 삽입 (4방향)
                    directions = ['E', 'W', 'S', 'N']
                    for direction in directions:
                        # 방향별 교통량 차이 (교차로 특성에 따라)
                        if characteristics['traffic_type'] == 'tourist':
                            # 관광지는 동서축이 더 활발
                            if direction in ['E', 'W']:
                                direction_volume = int(total_volume * 0.6)
                            else:
                                direction_volume = int(total_volume * 0.4)
                        elif characteristics['traffic_type'] == 'business':
                            # 업무지는 출퇴근 방향이 더 활발
                            if (7 <= hour < 9 and direction == 'E') or (17 <= hour < 19 and direction == 'W'):
                                direction_volume = int(total_volume * 0.6)
                            else:
                                direction_volume = int(total_volume * 0.4)
                        else:
                            # 일반적인 분포
                            direction_volume = int(total_volume * 0.25)
                        
                        cursor.execute("""
                            INSERT INTO traffic_trafficvolume 
                            (intersection_id, datetime, direction, volume, is_simulated, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            intersection_id, traffic_datetime, direction, direction_volume, 
                            1, traffic_datetime, traffic_datetime
                        ))
                    
                    total_records += 1
                    
                    if total_records % 10000 == 0:
                        print(f"  {total_records}개 레코드 생성 완료...")
            
            current_date += timedelta(days=1)
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {total_records}개의 교통 데이터가 생성되었습니다.")
        
        # 통계 출력
        print("\n=== 교통 데이터 통계 ===")
        
        # 교차로 유형별 통계
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN name LIKE '%광화문%' OR name LIKE '%명동%' OR name LIKE '%동대문%' THEN '관광지'
                    WHEN name LIKE '%강남%' OR name LIKE '%신촌%' OR name LIKE '%홍대%' THEN '상업지구'
                    WHEN name LIKE '%아파트%' OR name LIKE '%단지%' OR name LIKE '%마을%' THEN '주거지역'
                    WHEN name LIKE '%여의도%' OR name LIKE '%마포%' OR name LIKE '%영등포%' THEN '업무지구'
                    WHEN name LIKE '%대학교%' OR name LIKE '%고등학교%' OR name LIKE '%학교%' THEN '교육기관'
                    WHEN name LIKE '%역%' OR name LIKE '%지하철%' OR name LIKE '%버스%' THEN '교통요충지'
                    ELSE '일반'
                END as traffic_type,
                COUNT(*) as count
            FROM traffic_intersection 
            GROUP BY traffic_type
            ORDER BY count DESC
        """)
        
        type_stats = cursor.fetchall()
        print("교차로 유형별 분포:")
        for traffic_type, count in type_stats:
            print(f"  {traffic_type}: {count}개")
        
        # 샘플 데이터 출력
        print("\n=== 샘플 교통 데이터 ===")
        cursor.execute("""
            SELECT i.name, t.datetime, t.total_volume, t.average_speed
            FROM total_traffic_volume t
            JOIN traffic_intersection i ON t.intersection_id = i.id
            WHERE t.datetime = '2025-09-15 12:00:00'
            ORDER BY t.total_volume DESC
            LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        print("2025-09-15 12:00 기준 상위 5개 교차로:")
        for name, datetime, volume, speed in sample_data:
            print(f"  {name}: {volume}대, {speed:.1f}km/h")
        
    except pymysql.Error as e:
        print(f"오류 발생: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    generate_all_intersections_data()
