import os
import sys
import pymysql
from pathlib import Path
from dotenv import load_dotenv
from python_encrypter import EncryptionManager
from datetime import datetime

# 환경변수 로드
load_dotenv()

# 암호화 매니저 초기화
BASE_DIR = Path(__file__).resolve().parent
KEY_DIR = BASE_DIR / "django_secret_keys"
PASSWORD = os.getenv("DJANGO_ENCRYPTION_PASSWORD")

encryption_manager = EncryptionManager(
    key_directory=KEY_DIR,
    private_key_password=PASSWORD
)

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'mysql-gpu',
    'port': 3306,
    'user': 'root',
    'password': '1234',
    'database': 'traffic',
    'charset': 'utf8mb4'
}

def encrypt_text(value) -> bytes:
    """텍스트를 암호화합니다."""
    if value is None:
        return None
    return encryption_manager.encrypt(str(value))

def debug_traffic_volume():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=== 디버깅 시작 ===")
        
        # 1. 원본 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM traffic_trafficvolume")
        count = cursor.fetchone()[0]
        print(f"원본 데이터 개수: {count}")
        
        # 2. 샘플 데이터 확인
        cursor.execute("SELECT id, datetime, direction, volume, is_simulated, intersection_id FROM traffic_trafficvolume LIMIT 3")
        rows = cursor.fetchall()
        print(f"샘플 데이터: {rows}")
        
        # 3. 암호화 테스트
        if rows:
            row = rows[0]
            print(f"첫 번째 행: {row}")
            
            # 각 필드 암호화 테스트
            try:
                enc_dt = encrypt_text(row[1])
                print(f"datetime 암호화 성공: {len(enc_dt)} bytes")
                
                enc_direction = encrypt_text(row[2])
                print(f"direction 암호화 성공: {len(enc_direction)} bytes")
                
                enc_volume = encrypt_text(row[3])
                print(f"volume 암호화 성공: {len(enc_volume)} bytes")
                
                enc_is_sim = encrypt_text(row[4])
                print(f"is_simulated 암호화 성공: {len(enc_is_sim)} bytes")
                
                enc_inter_id = encrypt_text(row[5])
                print(f"intersection_id 암호화 성공: {len(enc_inter_id)} bytes")
                
                # 삽입 테스트
                cursor.execute("DELETE FROM S_traffic_volume WHERE id = %s", (row[0],))
                cursor.execute(
                    "INSERT INTO S_traffic_volume (id, datetime, direction, volume, is_simulated, intersection_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (row[0], enc_dt, enc_direction, enc_volume, enc_is_sim, enc_inter_id)
                )
                conn.commit()
                print("✅ 삽입 성공!")
                
                # 확인
                cursor.execute("SELECT COUNT(*) FROM S_traffic_volume")
                count = cursor.fetchone()[0]
                print(f"암호화된 데이터 개수: {count}")
                
            except Exception as e:
                print(f"❌ 암호화/삽입 실패: {e}")
        
    except Exception as e:
        print(f"❌ 전체 실패: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    debug_traffic_volume()
