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

def generate_diverse_proposals():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        print("다양한 교차로 정책 제안 데이터를 생성합니다...")

        # 실제 유저들 생성
        users = [
            {"id": 2, "username": "김민수", "email": "minsu.kim@email.com", "name": "김민수", "role": "citizen"},
            {"id": 3, "username": "이영희", "email": "younghee.lee@email.com", "name": "이영희", "role": "citizen"},
            {"id": 4, "username": "박철수", "email": "chulsoo.park@email.com", "name": "박철수", "role": "citizen"},
            {"id": 5, "username": "정수진", "email": "sujin.jung@email.com", "name": "정수진", "role": "citizen"},
            {"id": 6, "username": "최동호", "email": "dongho.choi@email.com", "name": "최동호", "role": "citizen"},
            {"id": 7, "username": "한미영", "email": "miyoung.han@email.com", "name": "한미영", "role": "citizen"},
            {"id": 8, "username": "윤태식", "email": "taesik.yoon@email.com", "name": "윤태식", "role": "citizen"},
            {"id": 9, "username": "강지은", "email": "jieun.kang@email.com", "name": "강지은", "role": "citizen"},
            {"id": 10, "username": "임성호", "email": "sungho.lim@email.com", "name": "임성호", "role": "citizen"},
            {"id": 11, "username": "조현정", "email": "hyunjung.cho@email.com", "name": "조현정", "role": "citizen"},
            {"id": 12, "username": "서민호", "email": "minho.seo@email.com", "name": "서민호", "role": "citizen"},
            {"id": 13, "username": "오지영", "email": "jiyoung.oh@email.com", "name": "오지영", "role": "citizen"},
            {"id": 14, "username": "신동욱", "email": "dongwook.shin@email.com", "name": "신동욱", "role": "citizen"},
            {"id": 15, "username": "배수진", "email": "sujin.bae@email.com", "name": "배수진", "role": "citizen"},
            {"id": 16, "username": "홍길동", "email": "gildong.hong@email.com", "name": "홍길동", "role": "citizen"}
        ]

        # 사용자 데이터 삽입
        for user in users:
            try:
                cursor.execute("""
                    INSERT INTO user_auth_user 
                    (id, username, email, password, first_name, last_name, name, role, is_active, is_staff, is_superuser, date_joined, created_at, updated_at, password_salt)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user['id'], user['username'], user['email'], 'pbkdf2_sha256$320000$test$test',
                    user['name'], '', user['name'], user['role'], 1, 0, 0, 
                    datetime.now(), datetime.now(), datetime.now(), 'salt123'
                ))
            except pymysql.IntegrityError:
                pass  # 이미 존재하는 사용자는 무시

        # 교차로별 특성에 따른 정책 제안 템플릿
        proposal_templates = {
            # 관광지/명소
            "tourist": [
                {
                    "title": "{intersection} 관광객 안전 강화 필요",
                    "description": "{intersection}에 관광객들이 너무 많아서 사고 위험이 높습니다. 안전시설을 강화해주세요.",
                    "category": "교통안전"
                },
                {
                    "title": "{intersection} 관광객 편의시설 부족",
                    "description": "{intersection}에 화장실이나 휴게시설이 없어서 관광객들이 불편해합니다. 편의시설을 설치해주세요.",
                    "category": "시설개선"
                },
                {
                    "title": "{intersection} 관광객 안내시설 개선",
                    "description": "{intersection}에 외국인 관광객들을 위한 안내시설이 부족합니다. 다국어 안내판을 설치해주세요.",
                    "category": "시설개선"
                }
            ],
            # 상업지구
            "commercial": [
                {
                    "title": "{intersection} 상권 활성화 방안",
                    "description": "{intersection} 상권이 더 활성화되도록 지원해주세요. 보행자 친화적 환경을 만들어주세요.",
                    "category": "시설개선"
                },
                {
                    "title": "{intersection} 주차문제 해결",
                    "description": "{intersection} 주변에 주차할 곳이 너무 없어서 상권 이용이 어렵습니다. 주차공간을 늘려주세요.",
                    "category": "주차문제"
                },
                {
                    "title": "{intersection} 야간 조명 개선",
                    "description": "{intersection}이 밤에 너무 어두워서 상권 이용이 어렵습니다. 조명을 개선해주세요.",
                    "category": "시설개선"
                }
            ],
            # 주거지역
            "residential": [
                {
                    "title": "{intersection} 주민 안전 강화",
                    "description": "{intersection}에서 아이들이 많이 지나다니는데 안전시설이 부족합니다. 어린이보호구역을 설정해주세요.",
                    "category": "교통안전"
                },
                {
                    "title": "{intersection} 주민 편의시설 설치",
                    "description": "{intersection}에 주민들이 쉴 수 있는 공간이 없습니다. 벤치나 작은 공원을 만들어주세요.",
                    "category": "시설개선"
                },
                {
                    "title": "{intersection} 소음 문제 해결",
                    "description": "{intersection}에서 소음이 심해서 주민들이 불편해합니다. 소음방지시설을 설치해주세요.",
                    "category": "환경보호"
                }
            ],
            # 업무지구
            "business": [
                {
                    "title": "{intersection} 출퇴근 교통체증 해결",
                    "description": "{intersection}에서 출퇴근 시간 교통체증이 심각합니다. 교통흐름을 개선해주세요.",
                    "category": "교통흐름"
                },
                {
                    "title": "{intersection} 직장인 편의시설",
                    "description": "{intersection}에 직장인들을 위한 편의시설이 부족합니다. 휴게시설을 설치해주세요.",
                    "category": "시설개선"
                },
                {
                    "title": "{intersection} 대중교통 개선",
                    "description": "{intersection}에서 대중교통 이용이 불편합니다. 버스 배차를 늘려주세요.",
                    "category": "대중교통"
                }
            ],
            # 교육기관
            "educational": [
                {
                    "title": "{intersection} 학생 안전 강화",
                    "description": "{intersection}에서 학생들이 많이 지나다니는데 안전시설이 부족합니다. 안전시설을 강화해주세요.",
                    "category": "교통안전"
                },
                {
                    "title": "{intersection} 학생 편의시설",
                    "description": "{intersection}에 학생들을 위한 편의시설이 부족합니다. 휴게시설을 설치해주세요.",
                    "category": "시설개선"
                },
                {
                    "title": "{intersection} 보행자 안전 강화",
                    "description": "{intersection}에서 보행자 사고가 자주 발생합니다. 보행자 안전시설을 강화해주세요.",
                    "category": "보행환경"
                }
            ],
            # 교통요충지
            "transportation": [
                {
                    "title": "{intersection} 교통흐름 개선",
                    "description": "{intersection}에서 교통체증이 심각합니다. 교통흐름을 개선해주세요.",
                    "category": "교통흐름"
                },
                {
                    "title": "{intersection} 대중교통 연계 개선",
                    "description": "{intersection}에서 대중교통 간 환승이 불편합니다. 환승시설을 개선해주세요.",
                    "category": "대중교통"
                },
                {
                    "title": "{intersection} 접근성 개선",
                    "description": "{intersection}에서 장애인 접근이 어렵습니다. 접근성을 개선해주세요.",
                    "category": "접근성"
                }
            ]
        }

        # 다양한 말투와 스타일
        speaking_styles = [
            # 정중한 말투
            "~해주세요", "~요청드립니다", "~부탁드립니다", "~검토해주세요",
            # 친근한 말투  
            "~해주면 좋겠어요", "~했으면 좋겠습니다", "~부탁해요", "~해주세요!",
            # 간단한 말투
            "~필요합니다", "~부족합니다", "~개선해주세요", "~설치해주세요",
            # 전문적인 말투
            "~검토가 필요합니다", "~개선이 시급합니다", "~해결이 필요합니다", "~대책이 필요합니다"
        ]

        # 교차로별 특성 파악 함수
        def get_intersection_type(intersection_name):
            name_lower = intersection_name.lower()
            
            if any(keyword in name_lower for keyword in ['광화문', '명동', '동대문', '남대문', '경복궁', '청계천', '한강', '63빌딩', '롯데월드', '에버랜드']):
                return "tourist"
            elif any(keyword in name_lower for keyword in ['강남', '신촌', '홍대', '이태원', '압구정', '청담', '삼성', '잠실', '건대', '성신여대']):
                return "commercial"
            elif any(keyword in name_lower for keyword in ['아파트', '단지', '마을', '동네', '주민센터', '학교', '병원', '시장']):
                return "residential"
            elif any(keyword in name_lower for keyword in ['여의도', '마포', '영등포', '구로', '가산', '판교', '분당', '일산']):
                return "business"
            elif any(keyword in name_lower for keyword in ['대학교', '고등학교', '중학교', '초등학교', '학교', '캠퍼스']):
                return "educational"
            elif any(keyword in name_lower for keyword in ['역', '지하철', '버스', '터미널', '공항', '고속도로', '터널', '대교']):
                return "transportation"
            else:
                return "residential"  # 기본값

        # 모든 교차로 가져오기
        cursor.execute("SELECT id, name FROM traffic_intersection ORDER BY RAND()")
        intersections = cursor.fetchall()
        print(f"총 {len(intersections)}개의 교차로 중에서 선택")

        # 기존 정책 제안 데이터 삭제
        cursor.execute("DELETE FROM traffic_proposalvote")
        cursor.execute("DELETE FROM traffic_proposalviewlog")
        cursor.execute("DELETE FROM traffic_proposalattachment")
        cursor.execute("DELETE FROM traffic_proposaltag_proposals")
        cursor.execute("DELETE FROM traffic_policyproposal")
        print("기존 정책 제안 데이터 삭제 완료")

        # 2025년 9월 1일부터 25일까지 랜덤 날짜/시간 생성
        start_date = datetime(2025, 9, 1)
        end_date = datetime(2025, 9, 25)
        
        # 교차로별로 정책 제안 생성
        proposal_data = []
        used_intersections = set()  # 중복 방지
        
        # 각 교차로 유형별로 3-5개씩 제안 생성
        for intersection_id, intersection_name in intersections:
            if len(used_intersections) >= 200:  # 최대 200개 교차로만 사용
                break
                
            intersection_type = get_intersection_type(intersection_name)
            templates = proposal_templates.get(intersection_type, proposal_templates["residential"])
            
            # 각 교차로당 1-3개의 제안 생성
            num_proposals = random.randint(1, 3)
            
            for _ in range(num_proposals):
                if intersection_id in used_intersections:
                    continue
                    
                used_intersections.add(intersection_id)
                
                # 랜덤 날짜/시간 생성
                random_days = random.randint(0, 24)
                random_hours = random.randint(8, 22)
                random_minutes = random.randint(0, 59)
                
                proposal_datetime = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
                
                # 랜덤 템플릿 선택
                template = random.choice(templates)
                
                # 제안 내용 생성
                title = template["title"].format(intersection=intersection_name)
                description = template["description"].format(intersection=intersection_name)
                
                # 말투 변경
                style = random.choice(speaking_styles)
                if "~해주세요" in description:
                    description = description.replace("~해주세요", style)
                elif "~설치해주세요" in description:
                    description = description.replace("~설치해주세요", style)
                
                # 랜덤 우선순위와 상태 선택
                priority = random.choice(["high", "medium", "low"])
                status = random.choice(["pending", "under_review", "approved", "rejected"])
                
                # 랜덤 투표수와 조회수 생성
                votes_count = random.randint(0, 50)
                views_count = random.randint(1, 200)
                
                # 랜덤 사용자 선택
                user = random.choice(users)
                
                # 랜덤 좌표 (서울 범위 내)
                latitude = random.uniform(37.4, 37.7)
                longitude = random.uniform(126.8, 127.2)
                
                # 관리자 응답 (일부 제안에만)
                admin_response = ""
                admin_response_date = None
                if status in ["approved", "rejected"] and random.random() < 0.6:
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
                    'title': title,
                    'description': description,
                    'category': template['category'],
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
                    'submitted_by_id': user['id']
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
        
        # 사용자별 통계
        user_stats = {}
        for data in proposal_data:
            user_id = data['submitted_by_id']
            user_stats[user_id] = user_stats.get(user_id, 0) + 1
        
        print("\n사용자별 제안 수 (상위 5명):")
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1], reverse=True)
        for user_id, count in sorted_users[:5]:
            user_name = next((u['name'] for u in users if u['id'] == user_id), f"사용자{user_id}")
            print(f"  {user_name}: {count}건")
        
        # 샘플 데이터 출력
        print("\n=== 샘플 정책 제안 ===")
        for i in range(0, min(5, len(proposal_data))):
            data = proposal_data[i]
            user_name = next((u['name'] for u in users if u['id'] == data['submitted_by_id']), f"사용자{data['submitted_by_id']}")
            print(f"\n[{data['category']}] {data['title']} ({data['status']})")
            print(f"  제안자: {user_name}")
            print(f"  {data['description'][:80]}...")
        
    except pymysql.Error as e:
        print(f"오류 발생: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    generate_diverse_proposals()
