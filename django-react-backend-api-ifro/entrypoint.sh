#!/bin/sh
set -e

cd /app/src

echo "Waiting for MySQL to be ready..."
until mysqladmin ping -h db -u root -p"$MYSQL_PASSWORD" --silent --protocol=tcp --skip-ssl; do
    echo "DB not ready yet... retrying in 1s"
    sleep 1
done

echo "MySQL is ready."

echo "Running migrations..."
python manage.py migrate traffic --fake
python manage.py migrate

# 병렬로 encrypt_transfer.py 실행
echo "[ENCRYPT] 🔄 encrypt_transfer.py 시작됨..."
python ../encrypt_transfer.py &
ENCRYPT_PID=$!

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000 &

# 백엔드 서버를 백그라운드로 띄우고, encrypt 완료까지 기다린 후 알림
wait $ENCRYPT_PID
echo "[ENCRYPT] ✅ encrypt_transfer.py 완료됨."

# 서버가 포그라운드로 계속 유지되도록
wait
