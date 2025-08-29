# SQL 데이터 백업 및 복원 가이드

## MySQL 데이터 Import 방법

### 1. traffic 스키마 생성
먼저 MySQL에서 `traffic` 스키마를 생성해야 합니다:

```sql
CREATE DATABASE traffic;
USE traffic;
```

### 2. SQL 파일 Import
MySQL에서 직접 다음 SQL 파일들을 순서대로 import하세요:

1. **기본 테이블 구조**
   - `traffic_django_content_type.sql`
   - `traffic_django_migrations.sql`
   - `traffic_django_admin_log.sql`
   - `traffic_django_session.sql`

2. **인증 관련 테이블**
   - `traffic_auth_permission.sql`
   - `traffic_auth_group.sql`
   - `traffic_auth_group_permissions.sql`
   - `traffic_auth_user.sql`
   - `traffic_auth_user_groups.sql`
   - `traffic_auth_user_user_permissions.sql`

3. **트래픽 데이터 테이블**
   - `traffic_traffic_intersection.sql`
   - `traffic_traffic_incident.sql`
   - `traffic_traffic_trafficvolume.sql`
   - `traffic_total_traffic_volume.sql`

### 3. Import 명령어 예시
MySQL 명령줄에서:
```bash
mysql -u username -p traffic < traffic_django_content_type.sql
mysql -u username -p traffic < traffic_auth_permission.sql
# ... 나머지 파일들도 동일한 방식으로 import
```

또는 MySQL Workbench에서 각 SQL 파일을 열어서 실행할 수 있습니다.

### 주의사항
- 반드시 `traffic` 스키마를 먼저 생성한 후 import를 진행하세요
- 파일 import 순서를 지켜주세요 (외래키 의존성 때문)
- 데이터베이스 사용자에게 적절한 권한이 있는지 확인하세요


### 변경내용
- 20250705 모델 수정해서 마이그레이션 새로 했으니 최신화 필요
