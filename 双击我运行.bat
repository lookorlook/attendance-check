@echo off
chcp 65001 >nul
echo ===================================
echo   多国考勤工时工具
echo ===================================
echo.
run_attendance.exe --config config.json
echo.
echo 运行完成！按任意键退出...
pause >nul
