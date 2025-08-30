#!/bin/sh
set -e

cd /app/src

echo "Waiting for MySQL to be ready..."
until mysql -h db -u root -p"$MYSQL_PASSWORD" --skip-ssl -e "SELECT 1;" > /dev/null 2>&1; do
    sleep 1
done

echo "MySQL is ready."

echo "Running migrations..."
# 기존 테이블이 있으므로 fake로 처리
python manage.py migrate --fake

echo "[ENCRYPT] 🔄 encrypt_transfer.py 시작됨..."
python ../encrypt_transfer.py &
ENCRYPT_PID=$!

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000 &

# encrypt 완료까지 기다린 후 알림
wait $ENCRYPT_PID
echo "[ENCRYPT] ✅ encrypt_transfer.py 완료됨."

# 서버가 포그라운드로 계속 유지되도록
wait
