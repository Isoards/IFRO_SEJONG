#!/bin/sh
set -e

cd /app/src

echo "Waiting for MySQL to be ready..."
until mysql -h db -u root -p"$MYSQL_PASSWORD" --skip-ssl -e "SELECT 1;" > /dev/null 2>&1; do
    echo "DB not ready yet... retrying in 1s"
    sleep 1
done

echo "MySQL is ready."

# Create fresh migrations
echo "Creating fresh migrations..."
python manage.py makemigrations user_auth
python manage.py makemigrations traffic

# Apply migrations - first migrate everything except our apps, then fake our initial migrations
echo "Applying base migrations..."
python manage.py migrate contenttypes
python manage.py migrate auth
python manage.py migrate admin
python manage.py migrate sessions

echo "Faking initial migrations for our apps..."
python manage.py migrate user_auth 0001 --fake
python manage.py migrate traffic 0001 --fake

echo "Applying remaining migrations..."
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
