#!/usr/bin/env python
import os
import sys
import pymysql
from pathlib import Path
from python_encrypter import EncryptionManager

# === 환경 설정 ===
BASE_DIR = Path(__file__).resolve().parent
KEY_DIR = BASE_DIR / "django_secret_keys"
PASSWORD = "forBus_password"

# === EncryptionManager 초기화 ===
try:
    encryption_service = EncryptionManager(
        key_directory=KEY_DIR,
        private_key_password=PASSWORD
    )
    print("✅ EncryptionManager 초기화 완료")
except Exception as e:
    print(f"❌ EncryptionManager 초기화 실패: {e}")
    sys.exit(1)

# === DB 연결 설정 ===
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "traffic",
    "charset": "utf8mb4",
    "port": 3307
}

def encrypt_text(value):
    """안전한 암호화 함수"""
    try:
        if isinstance(value, bytes):
            return encryption_service.encrypt(value.decode("utf-8"))
        elif isinstance(value, str):
            return encryption_service.encrypt(value)
        elif isinstance(value, float):
            return encryption_service.encrypt(f"{value:.10f}")
        elif isinstance(value, int):
            return encryption_service.encrypt(str(value))
        elif hasattr(value, 'isoformat'):  # datetime
            return encryption_service.encrypt(value.isoformat())
        else:
            return encryption_service.encrypt(str(value))
    except Exception as e:
        print(f"❌ 암호화 실패 ({type(value)}): {value} → {e}")
        raise

def encrypt_all_intersections():
    """모든 교차로 데이터 암호화"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 모든 교차로 데이터 가져오기
        cursor.execute("SELECT id, name, latitude, longitude, created_at, updated_at FROM traffic_intersection")
        rows = cursor.fetchall()
        print(f"🔄 총 {len(rows)}개의 교차로 데이터를 암호화합니다.")
        
        # 기존 암호화 데이터 삭제
        cursor.execute("DELETE FROM S_traffic_intersection")
        print("🗑️ 기존 암호화 데이터 삭제 완료")
        
        inserted = 0
        for row in rows:
            id_, name, lat, lng, created_at, updated_at = row
            try:
                enc_name = encrypt_text(name)
                enc_lat = encrypt_text(lat)
                enc_lng = encrypt_text(lng)
                enc_created = encrypt_text(created_at)
                enc_updated = encrypt_text(updated_at)
                
                cursor.execute(
                    "INSERT INTO S_traffic_intersection (id, name, latitude, longitude, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (id_, enc_name, enc_lat, enc_lng, enc_created, enc_updated)
                )
                inserted += 1
                
                if inserted % 1000 == 0:
                    print(f"암호화 중... {inserted}개 완료")
                    
            except Exception as e:
                print(f"❌ {id_}번 교차로 암호화 실패: {e}")
                continue
        
        conn.commit()
        print(f"✅ {inserted}개 교차로 암호화 완료!")
        
    except Exception as e:
        print(f"❌ 암호화 실패: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    print("=== 교차로 데이터 암호화 시작 ===")
    encrypt_all_intersections()
    print("=== 교차로 데이터 암호화 완료 ===")
