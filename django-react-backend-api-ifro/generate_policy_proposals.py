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

def generate_policy_proposals():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print("서울 교차로 정책 제안 데이터를 생성합니다...")

        # 모든 교차로 ID와 이름 가져오기
        cursor.execute("SELECT id, name FROM traffic_intersection ORDER BY RAND()")
        intersections = cursor.fetchall()
        print(f"총 {len(intersections)}개의 교차로 중에서 랜덤 선택")

        # 정책 제안 카테고리
        categories = [
            "교통안전", "신호체계", "도로개선", "보행환경", "대중교통", 
            "주차문제", "교통흐름", "시설개선", "환경보호", "접근성"
        ]

        # 우선순위
        priorities = ["high", "medium", "low"]

        # 상태
        statuses = ["pending", "under_review", "approved", "rejected"]

        # 다양한 말투와 제안 내용
        proposal_templates = [
            # 교통안전 관련
            {
                "category": "교통안전",
                "templates": [
                    "{intersection}에서 사고가 너무 자주 발생해요. 안전시설을 강화해주세요.",
                    "{intersection} 교차로가 위험합니다. 안전벽이나 가드레일 설치를 요청드립니다.",
                    "아이들이 많이 지나다니는 {intersection}에 어린이보호구역을 설정해주세요.",
                    "{intersection}에서 야간 사고가 빈번합니다. 가로등을 더 밝게 해주세요."
                ]
            },
            # 신호체계 관련
            {
                "category": "신호체계",
                "templates": [
                    "{intersection} 신호등이 너무 짧아서 급하게 건너게 됩니다. 시간을 늘려주세요.",
                    "{intersection}에서 좌회전 신호가 없어서 사고 위험이 높습니다. 좌회전 신호를 추가해주세요.",
                    "{intersection} 보행신호가 너무 짧습니다. 노인분들이 건너기 어려워요.",
                    "{intersection}에서 야간 신호등이 깜빡거려서 위험합니다. 수리를 요청드립니다."
                ]
            },
            # 도로개선 관련
            {
                "category": "도로개선",
                "templates": [
                    "{intersection} 도로가 너무 좁아서 교통체증이 심합니다. 도로를 확장해주세요.",
                    "{intersection}에서 포장이 벗겨져서 위험합니다. 도로 포장을 새로 해주세요.",
                    "{intersection} 교차로가 복잡해서 길을 잃기 쉽습니다. 안내표지판을 개선해주세요.",
                    "{intersection}에서 배수로가 막혀서 비 올 때마다 침수됩니다. 배수시설을 개선해주세요."
                ]
            },
            # 보행환경 관련
            {
                "category": "보행환경",
                "templates": [
                    "{intersection} 횡단보도가 없어서 위험합니다. 횡단보도를 설치해주세요.",
                    "{intersection}에서 보행자 신호등이 없어서 사고 위험이 높습니다.",
                    "{intersection} 보도가 너무 좁아서 보행하기 어려워요. 보도를 확장해주세요.",
                    "{intersection}에서 휠체어 이용자가 지나가기 어려워요. 접근성을 개선해주세요."
                ]
            },
            # 대중교통 관련
            {
                "category": "대중교통",
                "templates": [
                    "{intersection}에 버스정류장이 없어서 불편합니다. 버스정류장을 설치해주세요.",
                    "{intersection}에서 지하철역까지 거리가 너무 멉니다. 셔틀버스를 운행해주세요.",
                    "{intersection} 버스정류장에 지붕이 없어서 비 올 때 불편합니다. 대합실을 설치해주세요.",
                    "{intersection}에서 버스 배차간격이 너무 깁니다. 배차를 늘려주세요."
                ]
            },
            # 주차문제 관련
            {
                "category": "주차문제",
                "templates": [
                    "{intersection} 주변에 주차공간이 부족합니다. 공영주차장을 건설해주세요.",
                    "{intersection}에서 불법주차가 심각합니다. 단속을 강화해주세요.",
                    "{intersection} 주변 주차요금이 너무 비쌉니다. 요금을 낮춰주세요.",
                    "{intersection}에서 주차장 찾기가 어려워요. 주차안내시스템을 설치해주세요."
                ]
            },
            # 교통흐름 관련
            {
                "category": "교통흐름",
                "templates": [
                    "{intersection}에서 교통체증이 심각합니다. 교통흐름을 개선해주세요.",
                    "{intersection} 교차로가 복잡해서 교통체증이 발생합니다. 단순화해주세요.",
                    "{intersection}에서 우회로가 없어서 교통체증이 심합니다. 우회로를 만들어주세요.",
                    "{intersection} 교통신호 최적화가 필요합니다. 스마트 신호체계를 도입해주세요."
                ]
            },
            # 시설개선 관련
            {
                "category": "시설개선",
                "templates": [
                    "{intersection}에 공원이 없어서 휴식공간이 부족합니다. 작은 공원을 만들어주세요.",
                    "{intersection}에서 화장실이 없어서 불편합니다. 공중화장실을 설치해주세요.",
                    "{intersection}에 벤치가 없어서 쉴 곳이 없습니다. 벤치를 설치해주세요.",
                    "{intersection}에서 음료수 자판기가 없어서 불편합니다. 편의시설을 설치해주세요."
                ]
            },
            # 환경보호 관련
            {
                "category": "환경보호",
                "templates": [
                    "{intersection} 주변에 나무가 없어서 더위가 심합니다. 가로수를 심어주세요.",
                    "{intersection}에서 대기질이 나쁩니다. 공기정화시설을 설치해주세요.",
                    "{intersection}에 쓰레기통이 부족해서 쓰레기가 버려집니다. 쓰레기통을 늘려주세요.",
                    "{intersection}에서 소음이 심합니다. 소음방지시설을 설치해주세요."
                ]
            },
            # 접근성 관련
            {
                "category": "접근성",
                "templates": [
                    "{intersection}에서 휠체어 이용자가 지나가기 어려워요. 접근성을 개선해주세요.",
                    "{intersection} 보도에 경사로가 없어서 불편합니다. 경사로를 설치해주세요.",
                    "{intersection}에서 시각장애인을 위한 음성안내가 없습니다. 음성안내를 설치해주세요.",
                    "{intersection}에 엘리베이터가 없어서 불편합니다. 엘리베이터를 설치해주세요."
                ]
            }
        ]

        # 기존 정책 제안 데이터 삭제
        cursor.execute("DELETE FROM traffic_proposalvote")
        cursor.execute("DELETE FROM traffic_proposalviewlog")
        cursor.execute("DELETE FROM traffic_proposalattachment")
        cursor.execute("DELETE FROM traffic_proposaltag_proposals")
        cursor.execute("DELETE FROM traffic_policyproposal")
        print("기존 정책 제안 데이터 삭제 완료")

        # 서울 규모에 맞는 정책 제안 데이터 생성 (약 150-200건)
        num_proposals = random.randint(150, 200)
        print(f"총 {num_proposals}건의 정책 제안을 생성합니다...")

        proposal_data = []
        
        # 2025년 9월 1일부터 25일까지 랜덤 날짜/시간 생성
        start_date = datetime(2025, 9, 1)
        
        for i in range(num_proposals):
            # 랜덤 교차로 선택
            intersection_id, intersection_name = random.choice(intersections)
            
            # 랜덤 날짜/시간 생성
            random_days = random.randint(0, 24)  # 0-24일
            random_hours = random.randint(8, 22)  # 8-22시 (시민들이 제안할 시간대)
            random_minutes = random.randint(0, 59)  # 0-59분
            
            proposal_datetime = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
            
            # 랜덤 카테고리와 템플릿 선택
            category_template = random.choice(proposal_templates)
            category = category_template["category"]
            template = random.choice(category_template["templates"])
            
            # 제안 내용 생성
            title = f"{intersection_name} {category} 개선 제안"
            description = template.format(intersection=intersection_name)
            
            # 랜덤 우선순위와 상태 선택
            priority = random.choice(priorities)
            status = random.choice(statuses)
            
            # 랜덤 투표수와 조회수 생성
            votes_count = random.randint(0, 50)
            views_count = random.randint(1, 200)
            
            # 랜덤 위치 정보
            location = f"{intersection_name} 교차로 일대"
            
            # 랜덤 좌표 (서울 범위 내)
            latitude = random.uniform(37.4, 37.7)
            longitude = random.uniform(126.8, 127.2)
            
            # 관리자 응답 (일부 제안에만)
            admin_response = ""
            admin_response_date = None
            if status in ["approved", "rejected"] and random.random() < 0.7:  # 70% 확률로 관리자 응답
                if status == "approved":
                    admin_response = "시민님의 제안이 검토되어 승인되었습니다. 관련 부서에서 검토 후 시행 예정입니다."
                else:
                    admin_response = "제안해주신 내용을 검토한 결과, 현재로서는 시행이 어려운 상황입니다. 향후 재검토하겠습니다."
                admin_response_date = proposal_datetime + timedelta(days=random.randint(1, 7))
            
            proposal_data.append({
                'title': title,
                'description': description,
                'category': category,
                'priority': priority,
                'status': status,
                'location': location,
                'latitude': latitude,
                'longitude': longitude,
                'admin_response': admin_response,
                'admin_response_date': admin_response_date,
                'votes_count': votes_count,
                'views_count': views_count,
                'created_at': proposal_datetime,
                'updated_at': proposal_datetime,
                'intersection_id': intersection_id,
                'submitted_by_id': 1  # 기본 사용자 ID (나중에 생성)
            })
        
        # 데이터베이스에 삽입
        print(f"총 {len(proposal_data)}건의 정책 제안을 삽입합니다...")
        
        for i, data in enumerate(proposal_data):
            cursor.execute("""
                INSERT INTO traffic_policyproposal 
                (title, description, category, priority, status, location, latitude, longitude, 
                 admin_response, admin_response_date, votes_count, views_count, created_at, updated_at, 
                 intersection_id, submitted_by_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['title'],
                data['description'],
                data['category'],
                data['priority'],
                data['status'],
                data['location'],
                data['latitude'],
                data['longitude'],
                data['admin_response'],
                data['admin_response_date'],
                data['votes_count'],
                data['views_count'],
                data['created_at'],
                data['updated_at'],
                data['intersection_id'],
                data['submitted_by_id']
            ))
            
            if (i + 1) % 50 == 0:
                print(f"  {i + 1}건 정책 제안 삽입 완료...")
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {len(proposal_data)}건의 정책 제안이 생성되었습니다.")
        
        # 통계 출력
        print("\n=== 정책 제안 통계 ===")
        
        # 카테고리별 통계
        category_stats = {}
        for data in proposal_data:
            category = data['category']
            category_stats[category] = category_stats.get(category, 0) + 1
        
        for category, count in category_stats.items():
            print(f"  {category}: {count}건")
        
        # 상태별 통계
        status_stats = {}
        for data in proposal_data:
            status = data['status']
            status_stats[status] = status_stats.get(status, 0) + 1
        
        print("\n상태별 분포:")
        for status, count in status_stats.items():
            print(f"  {status}: {count}건")
        
        # 샘플 데이터 출력
        print("\n샘플 정책 제안:")
        for i in range(0, min(5, len(proposal_data))):
            data = proposal_data[i]
            print(f"  [{data['category']}] {data['title']} ({data['status']})")
            print(f"    {data['description'][:50]}...")
        
    except pymysql.Error as e:
        print(f"오류 발생: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    generate_policy_proposals()
