# 20250727 데이터를 도커 MySQL로 import하는 스크립트

Write-Host "=== 20250727 데이터 import 시작 ===" -ForegroundColor Green

# 기존 데이터 삭제
Write-Host "기존 테이블 데이터 삭제 중..." -ForegroundColor Yellow
docker exec mysql mysql -u root -p1234 traffic -e "
DROP TABLE IF EXISTS traffic_traffic_incident;
DROP TABLE IF EXISTS traffic_traffic_intersection;
DROP TABLE IF EXISTS traffic_traffic_trafficvolume;
DROP TABLE IF EXISTS traffic_traffic_trafficinterpretation;
DROP TABLE IF EXISTS traffic_total_traffic_volume;
DROP TABLE IF EXISTS S_incident;
DROP TABLE IF EXISTS S_traffic_volume;
DROP TABLE IF EXISTS S_traffic_interpretation;
DROP TABLE IF EXISTS S_total_traffic_volume;
DROP TABLE IF EXISTS S_traffic_intersection;
"

Write-Host "새로운 데이터 import 중..." -ForegroundColor Green

# 각 SQL 파일을 순서대로 import
Write-Host "1. traffic_intersection 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/traffic_traffic_intersection.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "2. traffic_incident 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/traffic_traffic_incident.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "3. traffic_trafficvolume 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/traffic_traffic_trafficvolume.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "4. traffic_trafficinterpretation 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/traffic_traffic_trafficinterpretation.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "5. total_traffic_volume 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/traffic_total_traffic_volume.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "6. S_incident 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/S_incident.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "7. S_traffic_volume 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/S_traffic_volume.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "8. S_traffic_interpretation 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/S_traffic_interpretation.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "9. S_total_traffic_volume 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/S_total_traffic_volume.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "10. S_traffic_intersection 데이터 import 중..." -ForegroundColor Cyan
Get-Content "../sqldata-backup/20250727/S_traffic_intersection.sql" | docker exec -i mysql mysql -u root -p1234 traffic

Write-Host "=== 데이터 import 완료 ===" -ForegroundColor Green

# 결과 확인
Write-Host "`n=== import 결과 확인 ===" -ForegroundColor Yellow
docker exec mysql mysql -u root -p1234 traffic -e "SHOW TABLES;" 