FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
  gcc \
  default-libmysqlclient-dev \
  build-essential \
  libssl-dev \
  pkg-config \
  default-mysql-client \
  && rm -rf /var/lib/apt/lists/*

COPY python_encrypter-0.1.0-py3-none-any.whl ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]