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

def main():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("=== 교통량 데이터 암호화 시작 ===")
        
        # 기존 암호화된 데이터 삭제
        cursor.execute("DELETE FROM S_traffic_volume")
        print("기존 암호화된 데이터 삭제 완료")
        
        # 원본 데이터 가져오기
        cursor.execute("SELECT id, datetime, direction, volume, is_simulated, intersection_id FROM traffic_trafficvolume")
        rows = cursor.fetchall()
        print(f"읽은 행 수: {len(rows)}")
        
        inserted = 0
        for i, row in enumerate(rows):
            try:
                id_, dt, direction, volume, is_sim, inter_id = row
                
                # 암호화
                enc_dt = encrypt_text(dt)
                enc_direction = encrypt_text(direction)
                enc_volume = encrypt_text(volume)
                enc_is_sim = encrypt_text(is_sim)
                enc_inter_id = encrypt_text(inter_id)
                
                # 삽입
                cursor.execute(
                    "INSERT INTO S_traffic_volume (id, datetime, direction, volume, is_simulated, intersection_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (id_, enc_dt, enc_direction, enc_volume, enc_is_sim, enc_inter_id)
                )
                inserted += 1
                
                if (i + 1) % 500 == 0:
                    print(f"  {i + 1}개 처리 완료...")
                    
            except Exception as e:
                print(f"❌ {id_}번 행 실패: {e}")
        
        conn.commit()
        print(f"✅ {inserted}개 행 암호화 및 삽입 완료")
        
        # 확인
        cursor.execute("SELECT COUNT(*) FROM S_traffic_volume")
        count = cursor.fetchone()[0]
        print(f"최종 암호화된 데이터 개수: {count}")
        
    except Exception as e:
        print(f"❌ 전체 실패: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    main()
