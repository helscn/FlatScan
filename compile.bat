@echo off
SETLOCAL ENABLEEXTENSIONS

REM ´ò°üµÄ³ÌĞòÎÄ¼şÃû£¬²»°üÀ¨ .py ºó×º
SET compile_name=FlatScan

REM ¶îÍâĞèÒª½øĞĞ´ò°üµÄÎÄ¼ş¼Ğ¼°ÎÄ¼ş
REM SET add_data=--add-data "ui\*.*;.\ui" --add-data ".\changelog.md;."
SET add_data=--add-data ".\config.json:.\config.json"

REM ´ò°üÄ£Ê½£¬--onefile ´ò°üÎªµ¥ÎÄ¼ş£¬--onedir ´ò°üÎªµ¥ÎÄ¼ş¼Ğ
SET compile_mode=--onedir

REM ³ÌĞòÔËĞĞÊ±ÊÇ·ñÏÔÊ¾¿ØÖÆÌ¨ĞÅÏ¢£¬--console ÏÔÊ¾¿ØÖÆÌ¨£¬--noconsole ²»ÏÔÊ¾¿ØÖÆÌ¨
REM SET show_console=--console
SET show_console=--noconsole

REM ´ò°üÂ·¾¶Ä¬ÈÏÎªµ±Ç°½Å±¾³ÌĞòËùÔÚÎÄ¼ş¼Ğ
SET compile_path=%~dp0
SET env_path=%~dp0
SET compile_file=%compile_path%%compile_name%.py

REM Èç¹û´ò°üÂ·¾¶ÖĞ°üÀ¨ icon.ico Í¼±êÊ±£¬½«»á×öÎª³ÌĞòÍ¼±ê´ò°ü
IF EXIST "%compile_path%icon.ico" (
	SET package_icon=--icon "%compile_path%icon.ico"
) ELSE (
	SET package_icon= 
)

REM Èç¹û´ò°üÂ·¾¶ÖĞ°üÀ¨ file_version_info.txt µÄ³ÌĞò°æ±¾ĞÅÏ¢Ê±£¬½«»áĞ´Èë³ÌĞò°æ±¾ĞÅÏ¢
IF EXIST "%compile_path%\file_version_info.txt" (
	SET version_file=--version-file "%compile_path\%file_version_info.txt"
) ELSE (
	SET version_file= 
)

REM ´ò°üÂ·¾¶º¬ÓĞ .env »ò .venv µÄĞéÄâÔËĞĞ»·¾³£¬»áÏÈ¼¤»î Python ĞéÄâÔËĞĞ»·¾³
ECHO.
IF EXIST "%compile_path%\.env\Scripts\activate.bat" (
	ECHO [32mÕıÔÚ¼¤»î½Å±¾ÔËĞĞµÄ Python ĞéÄâ»·¾³...[0m
	SET env_path=%compile_path%\.env
	CALL "%compile_path%\.env\Scripts\activate.bat"
)
IF EXIST %compile_path%\.venv\Scripts\activate.bat (
	ECHO [32mÕıÔÚ¼¤»î½Å±¾ÔËĞĞµÄ Python ĞéÄâ»·¾³...[0m
	SET env_path=%compile_path%\.venv
	CALL "%compile_path%\.venv\Scripts\activate.bat"
)

ECHO.
ECHO [31mPyInstaller %compile_mode% %show_console% %version_file% %package_icon% %add_data% --name %compile_name% "%compile_file%"
ECHO [90m
pyinstaller %compile_mode% %show_console% %version_file% %package_icon% %add_data% --name %compile_name% "%compile_file%"
IF ERRORLEVEL 1 (
	ECHO.
	ECHO [31m´ò°ü Python ½Å±¾Ê±³öÏÖ´íÎó! [0m
) ELSE (
	ECHO.
	ECHO [32m½Å±¾ %compile_file% ´ò°üÍê³É¡£[0m
)

IF EXIST "%compile_path%\.env\Scripts\deactivate.bat" (
	ECHO.
	ECHO [32mÕıÔÚÍË³ö½Å±¾ÔËĞĞµÄ Python ĞéÄâ»·¾³...[0m
	CALL "%compile_path%\.env\Scripts\deactivate.bat"
)
IF EXIST "%compile_path%\.venv\Scripts\deactivate.bat" (
	ECHO.
	ECHO [32mÕıÔÚÍË³ö½Å±¾ÔËĞĞµÄ Python ĞéÄâ»·¾³...[0m
	CALL "%compile_path%\.venv\Scripts\deactivate.bat"
)
ECHO.
PAUSE
