import os
import sys
import pymysql
from pathlib import Path
from dotenv import load_dotenv
from python_encrypter import EncryptionManager
from datetime import datetime

# === 환경 설정 ===
BASE_DIR = Path(__file__).resolve().parent
KEY_DIR = BASE_DIR / "django_secret_keys"

PASSWORD = os.getenv("DJANGO_ENCRYPTION_PASSWORD")

if not PASSWORD:
    print("❌ 환경 변수 DJANGO_ENCRYPTION_PASSWORD가 비어 있습니다.")
    sys.exit(1)

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
    "host": os.getenv('MYSQL_HOST', 'db'),
    "user": os.getenv('MYSQL_USER', 'root'),
    "password": os.getenv('MYSQL_PASSWORD', '1234'),
    "database": os.getenv('MYSQL_DATABASE', 'traffic'),
    "charset": "utf8mb4",
    "port": int(os.getenv('MYSQL_PORT', 3306))
}

# === 안전한 암호화 함수 ===
def encrypt_text(value) -> bytes:
    try:
        if isinstance(value, bytes):
            return encryption_service.encrypt(value.decode("utf-8"))
        elif isinstance(value, str):
            return encryption_service.encrypt(value)
        elif isinstance(value, float):
            return encryption_service.encrypt(f"{value:.10f}")
        elif isinstance(value, int):
            return encryption_service.encrypt(str(value))
        elif isinstance(value, datetime):
            return encryption_service.encrypt(value.isoformat())
        else:
            return encryption_service.encrypt(str(value))
    except Exception as e:
        print(f"❌ 암호화 실패 ({type(value)}): {value} → {e}")
        raise

# === 테이블 존재 여부 확인 후 없으면 생성 ===
def ensure_table_exists(cursor, table_name: str, create_sql: str):
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    if cursor.fetchone() is None:
        print(f"⚙️  테이블 {table_name} 이 존재하지 않아 생성합니다.")
        cursor.execute(create_sql)
    else:
        print(f"✅ 테이블 {table_name} 이 이미 존재합니다.")

# === S_traffic_intersection 이관 ===
def migrate_intersection(cursor):
    print("\n--- [1] S_traffic_intersection 이관 시작 ---")
    create_sql = """
    CREATE TABLE IF NOT EXISTS S_traffic_intersection (
        id BIGINT NOT NULL PRIMARY KEY,
        name BLOB,
        latitude BLOB,
        longitude BLOB,
        created_at BLOB,
        updated_at BLOB
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    ensure_table_exists(cursor, "S_traffic_intersection", create_sql)

    cursor.execute("SELECT id, name, latitude, longitude, created_at, updated_at FROM traffic_intersection")
    rows = cursor.fetchall()
    print(f"🔄 읽은 행 수: {len(rows)}")

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
                "INSERT IGNORE INTO S_traffic_intersection (id, name, latitude, longitude, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s)",
                (id_, enc_name, enc_lat, enc_lng, enc_created, enc_updated)
            )
            inserted += 1
        except Exception as e:
            print(f"❌ {id_}번 행 실패: {e}")
    print(f"✅ {inserted}개 행 암호화 및 삽입 완료")

# === S_total_traffic_volume 이관 ===
def migrate_volume(cursor):
    print("\n--- [2] S_total_traffic_volume 이관 시작 ---")
    create_sql = """
    CREATE TABLE IF NOT EXISTS S_total_traffic_volume (
        id BIGINT NOT NULL PRIMARY KEY,
        datetime BLOB,
        total_volume BLOB,
        average_speed BLOB,
        intersection_id BLOB
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    ensure_table_exists(cursor, "S_total_traffic_volume", create_sql)

    cursor.execute("SELECT id, datetime, total_volume, average_speed, intersection_id FROM total_traffic_volume")
    rows = cursor.fetchall()
    print(f"🔄 읽은 행 수: {len(rows)}")

    inserted = 0
    for row in rows:
        id_, dt, volume, speed, inter_id = row
        try:
            enc_dt = encrypt_text(dt)
            enc_volume = encrypt_text(volume)
            enc_speed = encrypt_text(speed)
            enc_inter_id = encrypt_text(inter_id)
            cursor.execute(
                "INSERT IGNORE INTO S_total_traffic_volume (id, datetime, total_volume, average_speed, intersection_id) VALUES (%s, %s, %s, %s, %s)",
                (id_, enc_dt, enc_volume, enc_speed, enc_inter_id)
            )
            inserted += 1
        except Exception as e:
            print(f"❌ {id_}번 행 실패: {e}")
    print(f"✅ {inserted}개 행 암호화 및 삽입 완료")

# === S_traffic_volume 이관 ===
def migrate_traffic_volume(cursor):
    print("\n--- [4] S_traffic_volume 이관 시작 ---")
    create_sql = """
    CREATE TABLE IF NOT EXISTS S_traffic_volume (
        id BIGINT NOT NULL PRIMARY KEY,
        datetime BLOB,
        direction BLOB,
        volume BLOB,
        is_simulated BLOB,
        intersection_id BLOB
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    ensure_table_exists(cursor, "S_traffic_volume", create_sql)
    
    # 기존 데이터 삭제
    cursor.execute("DELETE FROM S_traffic_volume")

    cursor.execute("SELECT id, datetime, direction, volume, is_simulated, intersection_id FROM traffic_trafficvolume")
    rows = cursor.fetchall()
    print(f"🔄 읽은 행 수: {len(rows)}")

    inserted = 0
    for row in rows:
        id_, dt, direction, volume, is_sim, inter_id = row
        try:
            enc_dt = encrypt_text(dt)
            enc_direction = encrypt_text(direction)
            enc_volume = encrypt_text(volume)
            enc_is_sim = encrypt_text(is_sim)
            enc_inter_id = encrypt_text(inter_id)
            
            cursor.execute(
                "INSERT INTO S_traffic_volume (id, datetime, direction, volume, is_simulated, intersection_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (id_, enc_dt, enc_direction, enc_volume, enc_is_sim, enc_inter_id)
            )
            inserted += 1
        except Exception as e:
            print(f"❌ {id_}번 행 실패: {e}")
    print(f"✅ {inserted}개 행 암호화 및 삽입 완료")

# === S_incident 이관 ===
def migrate_incident(cursor):
    print("\n--- [3] S_incident 이관 시작 ---")
    create_sql = """
    CREATE TABLE IF NOT EXISTS S_incident (
        id BIGINT NOT NULL PRIMARY KEY,
        incident_type BLOB,
        intersection_id BLOB,
        created_at BLOB,
        sii_id BLOB,
        description BLOB,
        severity BLOB,
        status BLOB,
        location BLOB,
        ip_address BLOB,
        timestamp BLOB
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    ensure_table_exists(cursor, "S_incident", create_sql)

    cursor.execute("SELECT id, incident_type, intersection_id, created_at, sii_id, description, severity, status, location, ip_address, timestamp FROM traffic_incident")
    rows = cursor.fetchall()
    print(f"🔄 읽은 행 수: {len(rows)}")

    inserted = 0
    for row in rows:
        id_, incident_type, intersection_id, created_at, sii_id, description, severity, status, location, ip_address, timestamp = row
        try:
            enc_incident_type = encrypt_text(incident_type)
            enc_intersection_id = encrypt_text(intersection_id)
            enc_created_at = encrypt_text(created_at)
            enc_sii_id = encrypt_text(sii_id)
            enc_description = encrypt_text(description)
            enc_severity = encrypt_text(severity)
            enc_status = encrypt_text(status)
            enc_location = encrypt_text(location)
            enc_ip_address = encrypt_text(ip_address)
            enc_timestamp = encrypt_text(timestamp)
            cursor.execute(
                "INSERT IGNORE INTO S_incident (id, incident_type, intersection_id, created_at, sii_id, description, severity, status, location, ip_address, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (id_, enc_incident_type, enc_intersection_id, enc_created_at, enc_sii_id, enc_description, enc_severity, enc_status, enc_location, enc_ip_address, enc_timestamp)
            )
            inserted += 1
        except Exception as e:
            print(f"❌ {id_}번 행 실패: {e}")
    print(f"✅ {inserted}개 행 암호화 및 삽입 완료")

# === 메인 ===
def main():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        migrate_intersection(cursor)
        migrate_volume(cursor)
        migrate_traffic_volume(cursor)
        migrate_incident(cursor)

        conn.commit()
        print("\n🎉 모든 암호화 이관 작업 완료!")

    except Exception as e:
        print(f"❌ 전체 처리 실패: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    print("=== 암호화 테이블 자동 생성 및 이관 시작 ===")
    main()
