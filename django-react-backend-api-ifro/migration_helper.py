#!/usr/bin/env python
# migration_helper.py - Django migration 상태 확인 및 처리

import os
import sys
import django
from django.core.management import execute_from_command_line, call_command
from django.db import connection, transaction
from django.core.management.base import BaseCommand

# Django 설정 초기화
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard.settings')

# src 디렉토리를 Python path에 추가
sys.path.insert(0, '/app/src')

django.setup()

def check_table_exists(table_name):
    """테이블 존재 여부 확인"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = %s
        """, [connection.settings_dict['NAME'], table_name])
        return cursor.fetchone()[0] > 0

def safe_migrate():
    """안전한 migration 실행"""
    try:
        print("🔍 데이터베이스 상태 확인 중...")
        
        # Django 시스템 테이블 확인
        django_tables_exist = check_table_exists('django_migrations')
        print(f"Django 시스템 테이블: {'존재' if django_tables_exist else '없음'}")
        
        # Traffic 앱 테이블 확인 (예시: traffic_intersection)
        traffic_tables_exist = check_table_exists('traffic_intersection')
        print(f"Traffic 테이블: {'존재' if traffic_tables_exist else '없음'}")
        
        # 시나리오별 처리
        if not django_tables_exist:
            print("📝 Django 시스템 테이블 생성 중...")
            call_command('migrate', '--fake-initial', verbosity=1)
            
        if not traffic_tables_exist:
            print("🚦 Traffic 테이블 생성 중...")
            call_command('migrate', 'traffic', verbosity=1)
        else:
            print("🔄 Traffic 테이블 migration 상태 확인...")
            try:
                # 이미 존재하는 경우 fake로 처리
                call_command('migrate', 'traffic', '--fake', verbosity=1)
            except Exception as e:
                print(f"⚠️ Fake migration 실패, 일반 migration 시도: {e}")
                call_command('migrate', 'traffic', verbosity=1)
        
        print("✅ Migration 완료!")
        return True
        
    except Exception as e:
        print(f"❌ Migration 오류: {e}")
        print("⚠️ 계속 진행합니다...")
        return False

if __name__ == "__main__":
    safe_migrate()
