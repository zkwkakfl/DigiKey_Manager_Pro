@echo off
REM 간단한 테스트 실행 스크립트
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ========================================
echo 간단한 실행 테스트
echo ========================================
echo.

echo Python 버전 확인:
python --version
echo.

echo 현재 디렉토리: %CD%
echo.

echo 필수 파일 확인:
if exist "main.py" (echo [OK] main.py) else (echo [X] main.py 없음)
if exist "excel_handler.py" (echo [OK] excel_handler.py) else (echo [X] excel_handler.py 없음)
if exist "digikey_api.py" (echo [OK] digikey_api.py) else (echo [X] digikey_api.py 없음)
if exist "database.py" (echo [OK] database.py) else (echo [X] database.py 없음)
echo.

echo Python import 테스트:
python -c "import sys; print('Python 경로:'); [print(p) for p in sys.path]"
echo.

echo 로컬 모듈 import 테스트:
python -c "import excel_handler; print('[OK] excel_handler import 성공')" 2>&1
python -c "import digikey_api; print('[OK] digikey_api import 성공')" 2>&1
python -c "import database; print('[OK] database import 성공')" 2>&1
echo.

echo main.py 직접 실행 테스트:
echo (Ctrl+C를 눌러 중단할 수 있습니다)
echo.
python main.py
echo.

pause
