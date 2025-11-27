@echo off
chcp 65001
rem ===== 切换到脚本所在目录 =====
cd /d %~dp0


echo. 当前目录是：%cd%



rem ===== 激活虚拟环境 =====
call .venv\Scripts\activate.bat


rem ===== 运行 app.py =====
python app.py


rem ===== 如果想看输出后不立即关闭窗口，可以加一行 pause =====
pause