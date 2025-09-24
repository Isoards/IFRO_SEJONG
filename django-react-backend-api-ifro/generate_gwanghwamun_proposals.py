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

def generate_gwanghwamun_proposals():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print("광화문 교차로 정책 제안 데이터를 생성합니다...")

        # 광화문 교차로 ID 찾기
        cursor.execute("SELECT id, name FROM traffic_intersection WHERE name = '광화문'")
        result = cursor.fetchone()
        
        if not result:
            print("광화문 교차로를 찾을 수 없습니다.")
            return
            
        intersection_id, intersection_name = result
        print(f"광화문 교차로 ID: {intersection_id}")

        # 광화문 특화 정책 제안 템플릿 (다양한 말투와 스타일)
        gwanghwamun_proposals = [
            # 관광객/시민 관점
            {
                "title": "광화문 광장 보행자 안전 강화 필요",
                "description": "광화문 광장에 관광객들이 너무 많아서 사고 위험이 높습니다. 보행자 전용 구역을 확대하고 안전시설을 강화해주세요! 특히 외국인 관광객들이 길을 잃지 않도록 안내시설도 개선이 필요해요.",
                "category": "교통안전",
                "priority": "high"
            },
            {
                "title": "광화문 신호등 대기시간 너무 김",
                "description": "광화문에서 신호등 기다리는 시간이 너무 길어요... 특히 출퇴근 시간에는 정말 답답합니다. 신호 주기를 조정해서 대기시간을 줄여주세요!",
                "category": "신호체계",
                "priority": "high"
            },
            {
                "title": "광화문 지하보도 개선 시급",
                "description": "광화문 지하보도가 너무 좁고 어두워서 위험해요. 특히 밤에는 더욱 그렇습니다. 조명을 밝게 하고 폭을 넓혀주세요. 그리고 휠체어 이용자도 쉽게 지나갈 수 있도록 경사로도 설치해주세요!",
                "category": "보행환경",
                "priority": "high"
            },
            {
                "title": "광화문 주차장 부족 문제",
                "description": "광화문 주변에 주차할 곳이 너무 없어요... 관광객들이 많이 오는데 주차공간이 부족해서 불편합니다. 지하주차장을 더 많이 만들어주세요!",
                "category": "주차문제",
                "priority": "medium"
            },
            {
                "title": "광화문 버스정류장 혼잡",
                "description": "광화문 버스정류장이 너무 복잡해요. 버스가 많아서 어느 버스를 타야 할지 모르겠습니다. 버스정류장을 정리하고 안내표지판을 더 명확하게 해주세요!",
                "category": "대중교통",
                "priority": "medium"
            },
            {
                "title": "광화문 야간 조명 개선",
                "description": "광화문이 밤에 너무 어두워요... 경복궁과 함께 서울의 대표 명소인데 조명이 부족합니다. 더 아름다운 야간 조명을 설치해서 관광객들이 더 오래 머물 수 있도록 해주세요!",
                "category": "시설개선",
                "priority": "medium"
            },
            {
                "title": "광화문 대기공기질 개선",
                "description": "광화문에서 차량 배기가스 때문에 공기가 안 좋아요... 특히 출퇴근 시간에는 더 심합니다. 공기정화시설을 설치하거나 친환경 교통수단을 장려해주세요!",
                "category": "환경보호",
                "priority": "high"
            },
            {
                "title": "광화문 스마트 교통체계 도입",
                "description": "광화문이 서울의 중심인데 교통체계가 너무 구식이에요. AI를 활용한 스마트 신호체계를 도입해서 교통흐름을 개선해주세요! 실시간 교통정보도 제공하면 좋겠어요.",
                "category": "교통흐름",
                "priority": "high"
            },
            {
                "title": "광화문 휠체어 접근성 개선",
                "description": "광화문에서 휠체어 이용자가 지나가기 너무 어려워요... 경사로가 부족하고 엘리베이터도 없어서 불편합니다. 장애인분들도 쉽게 이용할 수 있도록 접근성을 개선해주세요!",
                "category": "접근성",
                "priority": "high"
            },
            {
                "title": "광화문 도로 포장 개선",
                "description": "광화문 도로가 너무 거칠어요... 자전거 타기 어렵고 보행자도 불편합니다. 도로를 매끄럽게 포장하고 자전거 전용도로도 만들어주세요!",
                "category": "도로개선",
                "priority": "medium"
            },
            # 전문가/시민단체 관점
            {
                "title": "광화문 교통체증 해결 방안",
                "description": "광화문 교차로의 교통체증이 심각한 수준입니다. 다층 교차로나 지하도로 건설을 검토해주세요. 또한 대중교통 이용을 장려하는 정책도 필요합니다.",
                "category": "교통흐름",
                "priority": "high"
            },
            {
                "title": "광화문 보행자 우선 구역 설정",
                "description": "광화문은 보행자가 많은 지역입니다. 보행자 우선 구역을 설정하고 차량 속도를 제한하는 방안을 검토해주세요. 보행자 안전이 최우선이어야 합니다.",
                "category": "교통안전",
                "priority": "high"
            },
            {
                "title": "광화문 친환경 교통정책",
                "description": "광화문에서 친환경 교통수단을 장려하는 정책이 필요합니다. 전기차 충전소 확대, 자전거 대여소 설치, 보행자 친화적 환경 조성 등을 검토해주세요.",
                "category": "환경보호",
                "priority": "medium"
            },
            # 젊은 세대 관점
            {
                "title": "광화문 인스타그램 스팟 만들기",
                "description": "광화문을 더 예쁘게 꾸며서 젊은이들이 많이 오는 곳으로 만들어주세요! 예쁜 조명이나 아트워크를 설치하면 좋겠어요. SNS에서 화제가 될 만한 공간으로 만들어주세요!",
                "category": "시설개선",
                "priority": "low"
            },
            {
                "title": "광화문 와이파이 설치",
                "description": "광화문에서 무료 와이파이가 없어서 불편해요... 관광객들이 많이 오는 곳인데 인터넷 연결이 안 되면 불편합니다. 공용 와이파이를 설치해주세요!",
                "category": "시설개선",
                "priority": "low"
            },
            {
                "title": "광화문 푸드트럭 허용",
                "description": "광화문에 푸드트럭을 허용해주세요! 젊은이들이 좋아하는 음식들을 파는 푸드트럭이 있으면 더 활기찬 공간이 될 것 같아요. 단, 위생과 안전은 철저히 관리해주세요.",
                "category": "시설개선",
                "priority": "low"
            },
            # 시니어 관점
            {
                "title": "광화문 휴게시설 부족",
                "description": "광화문에서 쉴 곳이 너무 없어요... 나이 드신 분들이 많이 오시는데 벤치가 부족합니다. 더 많은 휴게시설을 설치해주세요. 화장실도 더 많이 만들어주세요.",
                "category": "시설개선",
                "priority": "medium"
            },
            {
                "title": "광화문 보행자 신호등 시간 연장",
                "description": "광화문 보행자 신호등 시간이 너무 짧아요... 나이 드신 분들이 건너기 어려워합니다. 보행자 신호등 시간을 늘려주세요!",
                "category": "신호체계",
                "priority": "high"
            },
            {
                "title": "광화문 의료시설 필요",
                "description": "광화문에 응급상황 대비 의료시설이 필요해요... 많은 사람들이 오는 곳인데 응급상황이 발생하면 대처하기 어려울 것 같습니다. 응급처치실이나 의료진을 배치해주세요.",
                "category": "시설개선",
                "priority": "medium"
            },
            # 비즈니스 관점
            {
                "title": "광화문 상권 활성화 방안",
                "description": "광화문 상권이 더 활성화되도록 지원해주세요! 관광객들이 더 오래 머물 수 있는 문화시설이나 쇼핑공간을 만들어주세요. 경제적 효과도 클 것 같아요.",
                "category": "시설개선",
                "priority": "medium"
            },
            {
                "title": "광화문 이벤트 공간 확대",
                "description": "광화문에서 더 많은 문화행사나 이벤트를 개최할 수 있도록 공간을 확대해주세요! 서울의 대표 공간인데 활용도가 낮은 것 같아요.",
                "category": "시설개선",
                "priority": "low"
            }
        ]

        # 기존 정책 제안 데이터 삭제
        cursor.execute("DELETE FROM traffic_proposalvote")
        cursor.execute("DELETE FROM traffic_proposalviewlog")
        cursor.execute("DELETE FROM traffic_proposalattachment")
        cursor.execute("DELETE FROM traffic_proposaltag_proposals")
        cursor.execute("DELETE FROM traffic_policyproposal")
        print("기존 정책 제안 데이터 삭제 완료")

        # 광화문 정책 제안 데이터 생성
        num_proposals = len(gwanghwamun_proposals)
        print(f"총 {num_proposals}건의 광화문 정책 제안을 생성합니다...")

        proposal_data = []
        
        # 2025년 9월 1일부터 25일까지 랜덤 날짜/시간 생성
        start_date = datetime(2025, 9, 1)
        
        for i, proposal in enumerate(gwanghwamun_proposals):
            # 랜덤 날짜/시간 생성
            random_days = random.randint(0, 24)  # 0-24일
            random_hours = random.randint(8, 22)  # 8-22시
            random_minutes = random.randint(0, 59)  # 0-59분
            
            proposal_datetime = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
            
            # 랜덤 상태 선택 (가중치 적용)
            status_weights = [0.3, 0.25, 0.25, 0.2]  # pending, under_review, approved, rejected
            status = random.choices(["pending", "under_review", "approved", "rejected"], weights=status_weights)[0]
            
            # 랜덤 투표수와 조회수 생성
            votes_count = random.randint(0, 100)
            views_count = random.randint(10, 500)
            
            # 광화문 좌표
            latitude = 37.57548334607047
            longitude = 126.9769023686653
            
            # 관리자 응답 (일부 제안에만)
            admin_response = ""
            admin_response_date = None
            if status in ["approved", "rejected"] and random.random() < 0.8:  # 80% 확률로 관리자 응답
                if status == "approved":
                    admin_responses = [
                        "시민님의 제안이 검토되어 승인되었습니다. 관련 부서에서 검토 후 시행 예정입니다.",
                        "좋은 제안 감사합니다. 해당 사항을 검토하여 개선하겠습니다.",
                        "제안해주신 내용이 타당하여 승인되었습니다. 단계적으로 시행하겠습니다."
                    ]
                    admin_response = random.choice(admin_responses)
                else:
                    admin_responses = [
                        "제안해주신 내용을 검토한 결과, 현재로서는 시행이 어려운 상황입니다. 향후 재검토하겠습니다.",
                        "예산 및 기술적 제약으로 인해 당장 시행이 어렵습니다. 다른 방안을 검토해보겠습니다.",
                        "관련 법규 및 제도상의 문제로 시행이 어렵습니다. 대안을 모색하겠습니다."
                    ]
                    admin_response = random.choice(admin_responses)
                admin_response_date = proposal_datetime + timedelta(days=random.randint(1, 10))
            
            proposal_data.append({
                'title': proposal['title'],
                'description': proposal['description'],
                'category': proposal['category'],
                'priority': proposal['priority'],
                'status': status,
                'location': f"{intersection_name} 교차로 일대",
                'latitude': latitude,
                'longitude': longitude,
                'admin_response': admin_response,
                'admin_response_date': admin_response_date,
                'votes_count': votes_count,
                'views_count': views_count,
                'created_at': proposal_datetime,
                'updated_at': proposal_datetime,
                'intersection_id': intersection_id,
                'submitted_by_id': 1
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
            
            if (i + 1) % 5 == 0:
                print(f"  {i + 1}건 정책 제안 삽입 완료...")
        
        # 변경사항 저장
        connection.commit()
        print(f"\n총 {len(proposal_data)}건의 광화문 정책 제안이 생성되었습니다.")
        
        # 통계 출력
        print("\n=== 광화문 정책 제안 통계 ===")
        
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
        
        # 우선순위별 통계
        priority_stats = {}
        for data in proposal_data:
            priority = data['priority']
            priority_stats[priority] = priority_stats.get(priority, 0) + 1
        
        print("\n우선순위별 분포:")
        for priority, count in priority_stats.items():
            print(f"  {priority}: {count}건")
        
        # 샘플 데이터 출력
        print("\n=== 광화문 정책 제안 샘플 ===")
        for i in range(0, min(5, len(proposal_data))):
            data = proposal_data[i]
            print(f"\n[{data['category']}] {data['title']} ({data['status']})")
            print(f"  {data['description'][:100]}...")
            if data['admin_response']:
                print(f"  관리자 응답: {data['admin_response'][:50]}...")
        
    except pymysql.Error as e:
        print(f"오류 발생: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    generate_gwanghwamun_proposals()
