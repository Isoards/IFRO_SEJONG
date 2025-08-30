#!/bin/sh
set -e

# 한글 지원 설정
export LANG=ko_KR.UTF-8
export LC_ALL=ko_KR.UTF-8
export LC_CTYPE=ko_KR.UTF-8

cd /app/src

echo "MySQL 준비 대기 중..."
until mysql -h db -u root -p"$MYSQL_PASSWORD" --skip-ssl -e "SELECT 1;" > /dev/null 2>&1; do
    sleep 1
done

echo "MySQL 준비 완료."

echo "[ENCRYPT] 🔄 encrypt_transfer.py 시작됨..."
python ../encrypt_transfer.py &
ENCRYPT_PID=$!

echo "Django 서버 시작 중..."
python manage.py runserver 0.0.0.0:8000 &

# encrypt 완료까지 기다린 후 알림
wait $ENCRYPT_PID
echo "[ENCRYPT] ✅ encrypt_transfer.py 완료됨."

# 서버가 포그라운드로 계속 유지되도록
wait
