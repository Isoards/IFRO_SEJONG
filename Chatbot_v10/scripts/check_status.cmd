@echo off
chcp 65001 > nul
setlocal

echo ============================================
echo   Chatbot v10 상태 확인
echo ============================================
echo.

cd /d "%~dp0.."

echo [1/5] 도메인 학습 파일:
echo ----------------------------------------
if exist "data\.ingested_files" (
    findstr /B "domain:" "data\.ingested_files" 2>nul
    if errorlevel 1 echo       ^(학습된 도메인 파일 없음^)
) else (
    echo       ^(학습 기록 없음^)
)
echo.

echo [2/5] 사용자 학습 파일:
echo ----------------------------------------
if exist "data\.ingested_files" (
    findstr /B "user:" "data\.ingested_files" 2>nul
    if errorlevel 1 echo       ^(학습된 사용자 파일 없음^)
) else (
    echo       ^(학습 기록 없음^)
)
echo.

echo [3/5] 온톨로지 DB 상태:
echo ----------------------------------------
if exist "ontology.db" (
    for %%A in (ontology.db) do echo       ontology.db: %%~zA bytes
) else (
    echo       ^(DB 없음^)
)
echo.

echo [4/5] 벡터 DB 상태:
echo ----------------------------------------
if exist "chroma_db" (
    echo       chroma_db: 폴더 존재
) else (
    echo       ^(벡터 DB 없음^)
)
echo.

echo [5/5] API 상태 확인:
echo ----------------------------------------
curl -s http://localhost:8009/api/status 2>nul
if errorlevel 1 (
    echo       ^(API 연결 실패 - 컨테이너가 실행 중인지 확인하세요^)
)
echo.
echo.

pause
