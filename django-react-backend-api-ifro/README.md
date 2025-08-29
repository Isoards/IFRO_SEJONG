# IFRO Backend (Django + Ninja)

교통 대시보드/분석 서비스의 백엔드 API 서버입니다.  
Django, django-ninja-extra, JWT 인증, MySQL/SQLite 지원 등 최신 스택을 사용합니다.

---

## 주요 기능

- **JWT 인증**: django-ninja-jwt[crypto] 기반, access(60분)/refresh(7일) 만료
- **회원가입/로그인**: Pydantic 스키마, username/password 검증(영문/숫자, 길이 등)
- **API 구조화**: django-ninja-extra로 RESTful 설계
- **데이터 모델**: Intersection, TrafficVolume, Incident 등 주요 모델에 created_at/updated_at 필드 포함
- **DB 지원**: 기본 SQLite, MySQL로 손쉽게 전환 가능
- **보호 API**: 대시보드 등 주요 데이터는 JWT 인증 필요

---

## 프로젝트 구조

```
src/
  ├─ dashboard/         # Django 프로젝트 설정
  ├─ traffic/           # 교통 데이터 앱 (모델, API, 관리 커맨드 등)
  ├─ db.sqlite3         # 기본 SQLite DB
  └─ manage.py
```

---

## 실행 방법

1. **의존성 설치**
   ```sh
   pip install -r requirements.txt
   ```

2. **마이그레이션 적용**
   ```sh
   cd src
   python manage.py migrate
   ```

3. **서버 실행**
   ```sh
   python manage.py runserver
   ```

4. **관리자 계정 생성(선택)**
   ```sh
   python manage.py createsuperuser
   ```

---

## DB 전환(MySQL 예시)

1. `settings.py`에서 DATABASES 설정을 MySQL로 변경:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'ifro_db',
           'USER': 'youruser',
           'PASSWORD': 'yourpassword',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```
2. MySQL 드라이버 설치:
   ```sh
   pip install mysqlclient
   ```

---

## 데이터 이전/백업

- 데이터 덤프:  
  `python manage.py dumpdata > data.json`
- 데이터 복원:  
  `python manage.py loaddata data.json`

---

## 기타

- 모든 시간 정보는 datetime 필드로 기록/표시
- 추가 기능, 보안, 다국어(i18n) 등 확장 가능