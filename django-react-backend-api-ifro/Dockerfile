FROM python:3.10-slim

# 한글 지원을 위한 로케일 설정
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV LC_CTYPE=ko_KR.UTF-8

WORKDIR /app

RUN apt-get update && apt-get install -y \
  gcc \
  default-libmysqlclient-dev \
  build-essential \
  libssl-dev \
  pkg-config \
  default-mysql-client \
  locales \
  && rm -rf /var/lib/apt/lists/*

# 한글 로케일 생성
RUN locale-gen ko_KR.UTF-8

COPY python_encrypter-0.1.0-py3-none-any.whl ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# entrypoint.sh 대신 직접 실행하는 스크립트 생성
RUN echo '#!/bin/sh\n\
set -e\n\
cd /app/src\n\
echo "Waiting for MySQL to be ready..."\n\
until mysql -h db -u root -p"$MYSQL_PASSWORD" --skip-ssl -e "SELECT 1;" > /dev/null 2>&1; do\n\
    sleep 1\n\
done\n\
echo "MySQL is ready."\n\
echo "Running migrations..."\n\
python manage.py migrate --run-syncdb --verbosity=0 || echo "Initial migration attempt completed"\n\
python manage.py migrate traffic --verbosity=0 || echo "Traffic migration attempt completed"\n\
echo "Starting services..."\n\
echo "[ENCRYPT] 🔄 encrypt_transfer.py 시작됨..."\n\
python ../encrypt_transfer.py &\n\
ENCRYPT_PID=$!\n\
echo "Starting Django server..."\n\
python manage.py runserver 0.0.0.0:8000 &\n\
wait $ENCRYPT_PID\n\
echo "[ENCRYPT] ✅ encrypt_transfer.py 완료됨."\n\
wait' > /usr/local/bin/docker-entrypoint.sh \
  && chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]