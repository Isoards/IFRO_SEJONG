#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Django 설정
sys.path.append('/app/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')
django.setup()

from traffic.models import Intersection, TrafficFlowAnalysisFavorite, TrafficFlowAnalysisStats
from user_auth.models import User

def add_test_data():
    # 기존 교차로 가져오기
    intersections = list(Intersection.objects.all())
    if len(intersections) < 2:
        print("교차로가 부족합니다. 최소 2개의 교차로가 필요합니다.")
        return
    
    # 기존 사용자 가져오기 또는 생성
    users = list(User.objects.all())
    if not users:
        # 테스트 사용자 생성
        for i in range(5):
            user = User.objects.create_user(
                username=f'testuser{i+1}',
                email=f'test{i+1}@example.com',
                password='testpass123'
            )
            users.append(user)
    
    # 교통 흐름 분석 즐겨찾기 테스트 데이터 생성
    favorite_routes = []
    for i in range(20):  # 20개의 즐겨찾기 생성
        start_intersection = random.choice(intersections)
        end_intersection = random.choice([x for x in intersections if x != start_intersection])
        user = random.choice(users)
        
        # 중복 체크
        existing = TrafficFlowAnalysisFavorite.objects.filter(
            user=user,
            start_intersection=start_intersection,
            end_intersection=end_intersection
        ).first()
        
        if not existing:
            favorite = TrafficFlowAnalysisFavorite.objects.create(
                user=user,
                start_intersection=start_intersection,
                end_intersection=end_intersection,
                access_count=random.randint(1, 50),
                last_accessed=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            favorite_routes.append((start_intersection, end_intersection))
            print(f"즐겨찾기 생성: {user.username} - {start_intersection.name} → {end_intersection.name}")
    
    # 교통 흐름 분석 통계 데이터 생성
    route_stats = {}
    for start, end in favorite_routes:
        key = (start.id, end.id)
        if key not in route_stats:
            route_stats[key] = {
                'start': start,
                'end': end,
                'favorites': 0,
                'accesses': 0,
                'users': set()
            }
    
    # 즐겨찾기 데이터를 기반으로 통계 계산
    for favorite in TrafficFlowAnalysisFavorite.objects.all():
        key = (favorite.start_intersection.id, favorite.end_intersection.id)
        if key in route_stats:
            route_stats[key]['favorites'] += 1
            route_stats[key]['accesses'] += favorite.access_count
            route_stats[key]['users'].add(favorite.user.id)
    
    # 통계 데이터 저장
    for key, stats in route_stats.items():
        stat, created = TrafficFlowAnalysisStats.objects.get_or_create(
            start_intersection=stats['start'],
            end_intersection=stats['end'],
            defaults={
                'total_favorites': stats['favorites'],
                'total_accesses': stats['accesses'],
                'unique_users': len(stats['users']),
                'last_accessed': datetime.now() - timedelta(days=random.randint(0, 7))
            }
        )
        if created:
            print(f"통계 생성: {stats['start'].name} → {stats['end'].name} (즐겨찾기: {stats['favorites']}명)")
    
    print(f"\n테스트 데이터 생성 완료!")
    print(f"- 즐겨찾기: {TrafficFlowAnalysisFavorite.objects.count()}개")
    print(f"- 통계: {TrafficFlowAnalysisStats.objects.count()}개")

if __name__ == "__main__":
    add_test_data()