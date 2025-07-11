@echo off
setlocal

REM 检查是否安装了conda
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: conda is not installed. Please install Anaconda or Miniconda first.
    exit /b 1
)

REM 设置环境名称
set ENV_NAME=minioshare

REM 停用当前环境
echo Deactivating current conda environment...
call conda deactivate

REM 检查环境是否存在
conda env list | findstr /B /C:"%ENV_NAME%" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Creating new conda environment: %ENV_NAME%
    conda create -n %ENV_NAME% python=3.9 -y
)

REM 激活环境
echo Activating conda environment: %ENV_NAME%
call conda activate %ENV_NAME%

REM 安装依赖
echo Installing dependencies...
pip install -r requirements.txt

REM 运行应用
echo Starting Flask application...
python app.py

endlocal 