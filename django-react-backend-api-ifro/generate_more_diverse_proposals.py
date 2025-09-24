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

def generate_more_diverse_proposals():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print("더 다양한 교차로 정책 제안 데이터를 생성합니다...")

        # 기존 사용자들 가져오기
        cursor.execute("SELECT id, name FROM user_auth_user WHERE id > 1")
        existing_users = cursor.fetchall()
        
        # 추가 사용자들 생성 (더 다양한 성격)
        additional_users = [
            {"id": 17, "username": "김철수", "name": "김철수", "personality": "직설적"},
            {"id": 18, "username": "박영희", "name": "박영희", "personality": "온화한"},
            {"id": 19, "username": "이민호", "name": "이민호", "personality": "열정적"},
            {"id": 20, "username": "정수연", "name": "정수연", "personality": "신중한"},
            {"id": 21, "username": "최지훈", "name": "최지훈", "personality": "냉정한"},
            {"id": 22, "username": "한소영", "name": "한소영", "personality": "감성적"},
            {"id": 23, "username": "윤태민", "name": "윤태민", "personality": "활발한"},
            {"id": 24, "username": "강미경", "name": "강미경", "personality": "차분한"},
            {"id": 25, "username": "임동현", "name": "임동현", "personality": "현실적"},
            {"id": 26, "username": "조은정", "name": "조은정", "personality": "이상주의적"},
            {"id": 27, "username": "서준호", "name": "서준호", "personality": "실용적"},
            {"id": 28, "username": "오지은", "name": "오지은", "personality": "완벽주의적"},
            {"id": 29, "username": "신현우", "name": "신현우", "personality": "혁신적"},
            {"id": 30, "username": "배수정", "name": "배수정", "personality": "협력적"},
            {"id": 31, "username": "홍민수", "name": "홍민수", "personality": "보수적"}
        ]

        # 추가 사용자 데이터 삽입
        for user in additional_users:
            try:
                cursor.execute("""
                    INSERT INTO user_auth_user 
                    (id, username, email, password, first_name, last_name, name, role, is_active, is_staff, is_superuser, date_joined, created_at, updated_at, password_salt)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user['id'], user['username'], f"{user['username']}@email.com", 'pbkdf2_sha256$320000$test$test',
                    user['name'], '', user['name'], 'citizen', 1, 0, 0, 
                    datetime.now(), datetime.now(), datetime.now(), 'salt123'
                ))
            except pymysql.IntegrityError:
                pass

        # 성격별 말투와 표현
        personality_styles = {
            "직설적": [
                "이거 정말 문제가 심각합니다. 빨리 해결해주세요!",
                "이런 상황이 계속되면 안 됩니다. 즉시 개선해주세요!",
                "이건 명백한 문제입니다. 당장 해결책을 내놓으세요!",
                "더 이상 참을 수 없습니다. 반드시 개선해주세요!"
            ],
            "온화한": [
                "혹시 가능하시다면 개선해주시면 감사하겠습니다.",
                "부디 검토해보시고 개선해주시면 좋겠습니다.",
                "가능하시다면 이 부분을 개선해주시면 감사하겠습니다.",
                "시간이 되실 때 검토해주시면 감사하겠습니다."
            ],
            "열정적": [
                "이 문제를 해결하면 정말 좋을 것 같습니다! 화이팅!",
                "함께 노력해서 더 좋은 환경을 만들어봅시다!",
                "이런 좋은 제안이 실현되면 정말 기쁠 것 같아요!",
                "모두가 함께 만들어가는 아름다운 도시가 되었으면 좋겠어요!"
            ],
            "신중한": [
                "신중히 검토해보시고 결정해주시면 감사하겠습니다.",
                "다각도로 검토해보시고 최선의 방안을 찾아주세요.",
                "신중한 검토 후에 결정해주시면 좋겠습니다.",
                "충분한 검토를 거쳐서 결정해주시면 감사하겠습니다."
            ],
            "냉정한": [
                "객관적으로 봤을 때 이 문제는 해결이 필요합니다.",
                "데이터를 보면 이 문제는 명확합니다.",
                "논리적으로 생각해보면 이 개선이 필요합니다.",
                "실용적인 관점에서 이 문제를 해결해야 합니다."
            ],
            "감성적": [
                "이 문제 때문에 마음이 아픕니다. 해결해주세요...",
                "정말 안타까운 상황입니다. 부디 개선해주세요.",
                "이런 일이 계속되면 정말 슬픕니다. 도와주세요.",
                "마음이 무거워집니다. 이 문제를 해결해주세요."
            ],
            "활발한": [
                "이거 정말 좋은 아이디어인 것 같아요! 해봅시다!",
                "와! 이런 개선이 있으면 정말 좋을 것 같아요!",
                "이거 진짜 필요한 것 같아요! 빨리 해봅시다!",
                "이런 좋은 제안이 있으면 정말 좋겠어요!"
            ],
            "차분한": [
                "차근차근 검토해보시고 개선해주시면 좋겠습니다.",
                "차분히 생각해보시고 최선의 방안을 찾아주세요.",
                "여유를 가지고 검토해보시고 결정해주세요.",
                "차분한 마음으로 검토해주시면 감사하겠습니다."
            ],
            "현실적": [
                "현실적으로 가능한 범위에서 개선해주세요.",
                "예산과 시간을 고려해서 현실적인 방안을 찾아주세요.",
                "실제로 가능한 방법으로 개선해주시면 좋겠습니다.",
                "현실적인 제약을 고려해서 해결책을 찾아주세요."
            ],
            "이상주의적": [
                "모든 시민이 행복한 도시를 만들어봅시다!",
                "이상적인 도시 환경을 만들어봅시다!",
                "모든 사람이 만족할 수 있는 완벽한 환경을 만들어주세요!",
                "꿈꾸던 아름다운 도시를 함께 만들어봅시다!"
            ],
            "실용적": [
                "실용적인 관점에서 이 문제를 해결해주세요.",
                "효율적으로 개선할 수 있는 방안을 찾아주세요.",
                "실제로 도움이 되는 방법으로 개선해주세요.",
                "실용적인 해결책을 제시해주시면 감사하겠습니다."
            ],
            "완벽주의적": [
                "완벽하게 개선해주시면 감사하겠습니다.",
                "모든 세부사항을 꼼꼼히 검토해서 완벽하게 해결해주세요.",
                "완벽한 결과를 위해 신중하게 진행해주세요.",
                "모든 부분이 완벽하게 개선되기를 바랍니다."
            ],
            "혁신적": [
                "새로운 방식으로 접근해서 해결해봅시다!",
                "혁신적인 방법으로 이 문제를 해결해봅시다!",
                "창의적인 아이디어로 개선해봅시다!",
                "새로운 기술을 활용해서 해결해봅시다!"
            ],
            "협력적": [
                "함께 협력해서 이 문제를 해결해봅시다!",
                "모든 관련자들이 함께 노력해서 개선해봅시다!",
                "협력적인 자세로 이 문제를 해결해봅시다!",
                "함께 만들어가는 도시가 되었으면 좋겠어요!"
            ],
            "보수적": [
                "기존 방식을 유지하면서 점진적으로 개선해주세요.",
                "안정적인 방법으로 개선해주시면 좋겠습니다.",
                "검증된 방법으로 신중하게 개선해주세요.",
                "기존 시스템을 유지하면서 개선해주세요."
            ]
        }

        # 다양한 감정 표현
        emotional_expressions = [
            # 긍정적 감정
            "정말 기대됩니다!", "와! 정말 좋겠어요!", "이거 진짜 필요해요!", "정말 감사하겠습니다!",
            # 부정적 감정  
            "정말 답답합니다...", "이거 진짜 문제예요", "더 이상 참을 수 없어요", "정말 안타까워요",
            # 중립적 감정
            "검토해주시면 감사하겠습니다", "개선이 필요해 보입니다", "이 부분을 확인해주세요", "검토 부탁드립니다",
            # 강한 감정
            "이거 정말 심각한 문제입니다!!!", "당장 해결해주세요!!!", "이런 일이 계속되면 안 됩니다!!!", "반드시 개선해주세요!!!",
            # 부드러운 감정
            "혹시 가능하시다면...", "부디 검토해주시면...", "가능하시다면...", "시간이 되실 때..."
        ]

        # 교차로별 특성에 따른 다양한 제안 내용
        diverse_proposals = {
            "교통안전": [
                "사고 위험이 높습니다", "안전시설이 부족합니다", "위험한 상황이 자주 발생합니다", 
                "안전사고가 우려됩니다", "보행자 안전이 위험합니다", "차량 사고 위험이 높습니다"
            ],
            "시설개선": [
                "편의시설이 부족합니다", "휴게시설이 없습니다", "화장실이 없어서 불편합니다", 
                "안내시설이 부족합니다", "편의시설을 설치해주세요", "휴게공간이 필요합니다"
            ],
            "환경보호": [
                "소음이 심합니다", "공기질이 나쁩니다", "환경이 오염되고 있습니다", 
                "소음방지시설이 필요합니다", "공기정화시설을 설치해주세요", "환경개선이 시급합니다"
            ],
            "대중교통": [
                "버스 배차가 부족합니다", "지하철 연결이 불편합니다", "대중교통 이용이 어렵습니다", 
                "버스정류장이 부족합니다", "대중교통 연계가 필요합니다", "교통편이 부족합니다"
            ],
            "주차문제": [
                "주차공간이 부족합니다", "주차할 곳이 없습니다", "주차문제가 심각합니다", 
                "주차장을 늘려주세요", "주차공간 확보가 필요합니다", "주차 불편이 심각합니다"
            ],
            "보행환경": [
                "보행하기 어렵습니다", "보도가 좁습니다", "보행자 안전이 위험합니다", 
                "횡단보도가 부족합니다", "보행환경 개선이 필요합니다", "보행자 편의시설이 부족합니다"
            ],
            "교통흐름": [
                "교통체증이 심각합니다", "교통흐름이 원활하지 않습니다", "교통체증 해결이 필요합니다", 
                "교통흐름 개선이 시급합니다", "교통체증으로 불편합니다", "교통 최적화가 필요합니다"
            ],
            "접근성": [
                "장애인 접근이 어렵습니다", "휠체어 이용이 불편합니다", "접근성이 부족합니다", 
                "장애인 편의시설이 필요합니다", "접근성 개선이 시급합니다", "모든 사람이 이용하기 어렵습니다"
            ]
        }

        # 모든 교차로 가져오기 (이미 사용된 교차로 제외)
        cursor.execute("""
            SELECT i.id, i.name 
            FROM traffic_intersection i 
            LEFT JOIN traffic_policyproposal p ON i.id = p.intersection_id 
            WHERE p.intersection_id IS NULL
            ORDER BY RAND()
        """)
        available_intersections = cursor.fetchall()
        print(f"사용 가능한 교차로: {len(available_intersections)}개")

        # 2025년 9월 1일부터 25일까지 랜덤 날짜/시간 생성
        start_date = datetime(2025, 9, 1)
        end_date = datetime(2025, 9, 25)
        
        # 1000개 제안 생성
        num_proposals = min(1000, len(available_intersections))
        proposal_data = []
        
        for i in range(num_proposals):
            if i >= len(available_intersections):
                break
                
            intersection_id, intersection_name = available_intersections[i]
            
            # 랜덤 날짜/시간 생성
            random_days = random.randint(0, 24)
            random_hours = random.randint(8, 22)
            random_minutes = random.randint(0, 59)
            
            proposal_datetime = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
            
            # 랜덤 사용자 선택 (성격 포함)
            user = random.choice(additional_users)
            personality = user['personality']
            
            # 랜덤 카테고리 선택
            category = random.choice(list(diverse_proposals.keys()))
            problem_description = random.choice(diverse_proposals[category])
            
            # 성격별 말투 선택
            personality_style = random.choice(personality_styles[personality])
            
            # 감정 표현 선택
            emotional_expression = random.choice(emotional_expressions)
            
            # 제안 제목 생성
            title = f"{intersection_name} {category} 개선 제안"
            
            # 제안 내용 생성 (성격과 감정이 반영된)
            description = f"{intersection_name}에서 {problem_description}. {personality_style} {emotional_expression}"
            
            # 랜덤 우선순위와 상태 선택
            priority = random.choice(["high", "medium", "low"])
            status = random.choice(["pending", "under_review", "approved", "rejected"])
            
            # 랜덤 투표수와 조회수 생성
            votes_count = random.randint(0, 100)
            views_count = random.randint(1, 500)
            
            # 랜덤 좌표 (서울 범위 내)
            latitude = random.uniform(37.4, 37.7)
            longitude = random.uniform(126.8, 127.2)
            
            # 관리자 응답 (일부 제안에만)
            admin_response = ""
            admin_response_date = None
            if status in ["approved", "rejected"] and random.random() < 0.5:
                if status == "approved":
                    admin_responses = [
                        "시민님의 제안이 검토되어 승인되었습니다. 관련 부서에서 검토 후 시행 예정입니다.",
                        "좋은 제안 감사합니다. 해당 사항을 검토하여 개선하겠습니다.",
                        "제안해주신 내용이 타당하여 승인되었습니다. 단계적으로 시행하겠습니다.",
                        "시민님의 의견이 반영되어 승인되었습니다. 신속히 처리하겠습니다."
                    ]
                    admin_response = random.choice(admin_responses)
                else:
                    admin_responses = [
                        "제안해주신 내용을 검토한 결과, 현재로서는 시행이 어려운 상황입니다. 향후 재검토하겠습니다.",
                        "예산 및 기술적 제약으로 인해 당장 시행이 어렵습니다. 다른 방안을 검토해보겠습니다.",
                        "관련 법규 및 제도상의 문제로 시행이 어렵습니다. 대안을 모색하겠습니다.",
                        "현재로서는 시행이 어려운 상황입니다. 다른 우선순위를 고려하여 재검토하겠습니다."
                    ]
                    admin_response = random.choice(admin_responses)
                admin_response_date = proposal_datetime + timedelta(days=random.randint(1, 15))
            
            proposal_data.append({
                'title': title,
                'description': description,
                'category': category,
                'priority': priority,
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
                'submitted_by_id': user['id'],
                'personality': personality
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
            
            if (i + 1) % 100 == 0:
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
        
        # 성격별 통계
        personality_stats = {}
        for data in proposal_data:
            personality = data['personality']
            personality_stats[personality] = personality_stats.get(personality, 0) + 1
        
        print("\n성격별 분포:")
        for personality, count in personality_stats.items():
            print(f"  {personality}: {count}건")
        
        # 상태별 통계
        status_stats = {}
        for data in proposal_data:
            status = data['status']
            status_stats[status] = status_stats.get(status, 0) + 1
        
        print("\n상태별 분포:")
        for status, count in status_stats.items():
            print(f"  {status}: {count}건")
        
        # 샘플 데이터 출력 (다양한 성격별)
        print("\n=== 성격별 샘플 정책 제안 ===")
        personality_samples = {}
        for data in proposal_data:
            personality = data['personality']
            if personality not in personality_samples:
                personality_samples[personality] = data
        
        for personality, data in personality_samples.items():
            user_name = next((u['name'] for u in additional_users if u['id'] == data['submitted_by_id']), f"사용자{data['submitted_by_id']}")
            print(f"\n[{personality}] {user_name}님의 제안:")
            print(f"  {data['title']} ({data['status']})")
            print(f"  \"{data['description']}\"")
        
    except pymysql.Error as e:
        print(f"오류 발생: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    generate_more_diverse_proposals()
