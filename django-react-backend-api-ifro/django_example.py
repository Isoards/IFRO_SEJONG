import os
from pathlib import Path
import sys

# --- Django 프로젝트 환경 시뮬레이션 --- #
class DjangoSettings:
    BASE_DIR = Path(__file__).resolve().parent
    ENCRYPTION_KEY_DIR = BASE_DIR / 'django_secret_keys'

    # [수정] 환경 변수 대신 직접 지정
    ENCRYPTION_PRIVATE_KEY_PASSWORD = "forBus_password"

settings = DjangoSettings()

# --- 애플리케이션 로직 시작 --- #
try:
    from python_encrypter import EncryptionManager
except ImportError:
    print("오류: python-encrypter 모듈이 설치되지 않았습니다.")
    print("먼저 'pip install .' 명령어로 모듈을 설치해주세요.")
    sys.exit(1)

def initialize_encryption_service():
    """settings의 값을 사용하여 EncryptionManager를 초기화합니다."""
    if not settings.ENCRYPTION_PRIVATE_KEY_PASSWORD:
        print("오류: ENCRYPTION_PRIVATE_KEY_PASSWORD가 설정되지 않았습니다.")
        sys.exit(1)

    try:
        manager = EncryptionManager(
            key_directory=settings.ENCRYPTION_KEY_DIR,
            private_key_password=settings.ENCRYPTION_PRIVATE_KEY_PASSWORD
        )
        print(f"성공: EncryptionManager가 초기화되었습니다.")
        print(f"키 저장 경로: {settings.ENCRYPTION_KEY_DIR.resolve()}")
        return manager
    except Exception as e:
        print(f"EncryptionManager 초기화 중 오류 발생: {e}")
        return None

def main():
    encryption_service = initialize_encryption_service()
    if not encryption_service:
        return

    print("\n--- Django에서 양방향 암호화 사용 예제 ---")
    user_api_key = "abcdef1234567890_this_is_a_secret_api_key"
    encrypted_key = encryption_service.encrypt(user_api_key)
    print(f"사용자 API 키 (원본): {user_api_key}")
    print(f"암호화된 키 (DB 저장용): {encrypted_key.hex()}")

    decrypted_key = encryption_service.decrypt(encrypted_key)
    print(f"복호화된 키 (사용 시): {decrypted_key}")
    assert user_api_key == decrypted_key
    print("성공: 원본과 복호화된 키가 일치합니다.")

    print("\n--- Django에서 단방향 암호화 (해싱) 사용 예제 ---")
    user_password = "my_secure_password_123"
    password_salt = os.urandom(16).hex()

    hashed_password = EncryptionManager.hash_string(user_password, salt=password_salt)
    print(f"원본 비밀번호: {user_password}")
    print(f"사용된 Salt: {password_salt}")
    print(f"해싱된 비밀번호 (DB 저장용): {hashed_password}")

    input_password = "my_secure_password_123"
    hashed_input_password = EncryptionManager.hash_string(input_password, salt=password_salt)

    if hashed_input_password == hashed_password:
        print("비밀번호 검증 성공: 로그인 허용")
    else:
        print("비밀번호 검증 실패: 로그인 거부")

if __name__ == "__main__":
    print("--- Django 프로젝트용 EncryptionManager 사용 예제 ---")
    main()
