@echo off
chcp 65001 >nul
echo ========================================
echo 디지키 파트넘버 조회 프로그램 패키징
echo ========================================
echo.
echo 이 스크립트는 PyInstaller를 사용하여 실행 파일(.exe)을 생성합니다.
echo Python 설치 없이도 프로그램을 실행할 수 있습니다.
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python을 설치한 후 다시 실행해주세요.
    echo.
    pause
    exit /b 1
)

REM PyInstaller 설치 확인
echo PyInstaller 설치 확인 중...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller가 설치되어 있지 않습니다.
    echo PyInstaller를 설치하시겠습니까? (Y/N)
    set /p install="> "
    if /i "%install%"=="Y" (
        echo PyInstaller 설치 중...
        pip install pyinstaller
        if errorlevel 1 (
            echo [오류] PyInstaller 설치에 실패했습니다.
            pause
            exit /b 1
        )
    ) else (
        echo 프로그램을 종료합니다.
        pause
        exit /b 1
    )
)

REM 필수 패키지 설치 확인
echo 필수 패키지 확인 중...
python -c "import pandas, openpyxl, digikey_api, requests" >nul 2>&1
if errorlevel 1 (
    echo 필수 패키지가 설치되어 있지 않습니다.
    echo 패키지를 설치하시겠습니까? (Y/N)
    set /p install="> "
    if /i "%install%"=="Y" (
        echo 패키지 설치 중...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo [오류] 패키지 설치에 실패했습니다.
            pause
            exit /b 1
        )
    ) else (
        echo 프로그램을 종료합니다.
        pause
        exit /b 1
    )
)

REM 기존 빌드 폴더 삭제
if exist "dist" (
    echo 기존 빌드 폴더 삭제 중...
    rmdir /s /q dist
)
if exist "build" (
    rmdir /s /q build
)
if exist "*.spec" (
    del /q *.spec
)

REM PyInstaller로 실행 파일 생성
echo.
echo 실행 파일 생성 중... (시간이 걸릴 수 있습니다)
echo.
pyinstaller --onefile ^
    --windowed ^
    --name "DigiKey_Manager_Pro" ^
    --icon=NONE ^
    --add-data "config.txt;." ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=digikey_api ^
    --hidden-import=requests ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    main.py

if errorlevel 1 (
    echo.
    echo [오류] 실행 파일 생성에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 패키징 완료!
echo ========================================
echo.
echo 실행 파일 위치: dist\DigiKey_Manager_Pro.exe
echo.
echo 실행 파일을 다른 컴퓨터에서 사용하려면:
echo 1. dist 폴더의 DigiKey_Manager_Pro.exe 파일을 복사하세요.
echo 2. config.txt 파일도 함께 복사하세요 (선택사항)
echo 3. Python 설치 없이도 실행 가능합니다!
echo.
pause
