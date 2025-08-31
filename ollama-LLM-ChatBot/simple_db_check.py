#!/usr/bin/env python3
"""
간단한 데이터베이스 확인 스크립트
"""

import pymysql
import os

def check_database():
    """데이터베이스 확인"""
    
    # Docker MySQL 연결 설정
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '1234',
        'port': 3307,  # Docker 포트 매핑
        'charset': 'utf8mb4'
    }
    
    try:
        # 연결
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        print("=" * 60)
        print("데이터베이스 확인")
        print("=" * 60)
        
        # 1. 데이터베이스 목록 확인
        print("\n1. 데이터베이스 목록:")
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        for db in databases:
            print(f"  - {db[0]}")
        
        # 2. traffic 데이터베이스 사용
        print("\n2. traffic 데이터베이스 테이블:")
        cursor.execute("USE traffic")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            
            # 테이블 구조 확인
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            print(f"    컬럼:")
            for col in columns:
                print(f"      - {col[0]}: {col[1]} ({col[2]})")
            
            # 샘플 데이터 확인
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            sample_data = cursor.fetchall()
            
            if sample_data:
                print(f"    샘플 데이터:")
                for i, row in enumerate(sample_data, 1):
                    print(f"      {i}. {row}")
            else:
                print(f"    샘플 데이터: 없음")
            print()
        
        cursor.close()
        connection.close()
        
        print("✓ 데이터베이스 확인 완료")
        
    except Exception as e:
        print(f"✗ 오류: {e}")

if __name__ == "__main__":
    check_database()

