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

def generate_incident_data():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print("서울 교차로 사고 데이터를 생성합니다...")

        # 모든 교차로 ID 가져오기
        cursor.execute("SELECT id, name FROM traffic_intersection ORDER BY RAND()")
        intersections = cursor.fetchall()
        print(f"총 {len(intersections)}개의 교차로 중에서 랜덤 선택")

        # 사고 유형 정의 (실제 서울 교통사고 유형 기반)
        incident_types = [
            "차량 충돌",
            "보행자 사고", 
            "신호 위반",
            "과속 사고",
            "음주 운전",
            "횡단보도 사고",
            "좌회전 사고",
            "우회전 사고",
            "정면 충돌",
            "측면 충돌",
            "후진 사고",
            "주정차 위반",
            "안전거리 미확보",
            "신호등 고장",
            "도로 공사 관련"
        ]

        # 심각도 정의
        severity_levels = ["경미", "보통", "심각", "매우 심각"]
        
        # 상태 정의
        status_options = ["처리중", "완료", "조사중", "재검토"]

        # 기존 사고 데이터 삭제
        cursor.execute("DELETE FROM traffic_incident")
        print("기존 사고 데이터 삭제 완료")

        # 서울 규모에 맞는 사고 데이터 생성 (25일간 약 200-300건)
        num_incidents = random.randint(200, 300)
        print(f"총 {num_incidents}건의 사고 데이터를 생성합니다...")

        incident_data = []
        
        # 2025년 9월 1일부터 25일까지 랜덤 날짜/시간 생성
        start_date = datetime(2025, 9, 1)
        end_date = datetime(2025, 9, 25)
        
        for i in range(num_incidents):
            # 랜덤 교차로 선택
            intersection_id, intersection_name = random.choice(intersections)
            
            # 랜덤 날짜/시간 생성
            random_days = random.randint(0, 24)  # 0-24일
            random_hours = random.randint(0, 23)  # 0-23시
            random_minutes = random.randint(0, 59)  # 0-59분
            
            incident_datetime = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
            
            # 랜덤 사고 유형 선택
            incident_type = random.choice(incident_types)
            
            # 랜덤 심각도 선택 (가중치 적용: 경미 > 보통 > 심각 > 매우 심각)
            severity_weights = [0.4, 0.3, 0.2, 0.1]  # 경미 40%, 보통 30%, 심각 20%, 매우 심각 10%
            severity = random.choices(severity_levels, weights=severity_weights)[0]
            
            # 랜덤 상태 선택
            status = random.choice(status_options)
            
            # 랜덤 IP 주소 생성 (서울 지역)
            ip_address = f"203.248.{random.randint(1, 255)}.{random.randint(1, 255)}"
            
            # SII ID 생성
            sii_id = random.randint(100000, 999999)
            
            incident_data.append({
                'incident_type': incident_type,
                'intersection_name': intersection_name,
                'district': random.choice(['강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구']),
                'managed_by': random.choice(['서울시 교통정보과', '서울시 교통관리센터', '서울시 교통안전과']),
                'assigned_to': random.choice(['김철수', '이영희', '박민수', '정수진', '최동호']),
                'registered_at': incident_datetime,
                'status': status,
                'user': random.choice(['admin', 'operator1', 'operator2', 'manager']),
                'equipment_locked': random.choice(['Y', 'N']),
                'last_status_update': incident_datetime,
                'ip_address': ip_address,
                'sii_id': sii_id,
                'created_at': incident_datetime,
                'updated_at': incident_datetime,
                'type': incident_type,
                'intersection_id': intersection_id
            })
        
        # 데이터베이스에 삽입
        print(f"총 {len(incident_data)}건의 사고 데이터를 삽입합니다...")
        
        for i, data in enumerate(incident_data):
            cursor.execute("""
                INSERT INTO traffic_incident 
                (incident_type, intersection_name, district, managed_by, assigned_to, registered_at, status, user, equipment_locked, last_status_update, ip_address, sii_id, created_at, updated_at, type, intersection_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['incident_type'],
                data['intersection_name'],
                data['district'],
                data['managed_by'],
                data['assigned_to'],
                data['registered_at'],
                data['status'],
                data['user'],
                data['equipment_locked'],
                data['last_status_update'],
                data['ip_address'],
                data['sii_id'],
                data['created_at'],
                data['updated_at'],
                data['type'],
                data['intersection_id']
            ))
            
            if (i + 1) % 50 == 0:
                print(f"  {i + 1}건 사고 데이터 삽입 완료...")
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {len(incident_data)}건의 사고 데이터가 생성되었습니다.")
        
        # 통계 출력
        print("\n=== 사고 데이터 통계 ===")
        
        # 상태별 통계
        status_stats = {}
        for data in incident_data:
            status = data['status']
            status_stats[status] = status_stats.get(status, 0) + 1
        
        for status, count in status_stats.items():
            print(f"  {status}: {count}건")
        
        # 사고 유형별 상위 5개
        type_stats = {}
        for data in incident_data:
            incident_type = data['incident_type']
            type_stats[incident_type] = type_stats.get(incident_type, 0) + 1
        
        print("\n상위 사고 유형:")
        sorted_types = sorted(type_stats.items(), key=lambda x: x[1], reverse=True)
        for incident_type, count in sorted_types[:5]:
            print(f"  {incident_type}: {count}건")
        
        # 샘플 데이터 출력
        print("\n샘플 사고 데이터:")
        for i in range(0, min(5, len(incident_data))):
            data = incident_data[i]
            print(f"  {data['created_at']}: {data['intersection_name']} - {data['incident_type']} ({data['status']})")
        
    except pymysql.Error as e:
        print(f"오류 발생: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    generate_incident_data()
