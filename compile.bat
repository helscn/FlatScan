@echo off
SETLOCAL ENABLEEXTENSIONS

REM 打包的程序文件名，不包括 .py 后缀
SET compile_name=FlatScan

REM 额外需要进行打包的文件夹及文件
REM SET add_data=--add-data "ui\*.*;.\ui" --add-data ".\changelog.md;."
SET add_data=--add-data ".\config.json:."

REM 打包模式，--onefile 打包为单文件，--onedir 打包为单文件夹
SET compile_mode=--onedir

REM 程序运行时是否显示控制台信息，--console 显示控制台，--noconsole 不显示控制台
REM SET show_console=--console
SET show_console=--noconsole

REM 打包路径默认为当前脚本程序所在文件夹
SET compile_path=%~dp0
SET env_path=%~dp0
SET compile_file=%compile_path%%compile_name%.py

REM 如果打包路径中包括 icon.ico 图标时，将会做为程序图标打包
IF EXIST "%compile_path%icon.ico" (
	SET package_icon=--icon "%compile_path%icon.ico"
) ELSE (
	SET package_icon= 
)

REM 如果打包路径中包括 file_version_info.txt 的程序版本信息时，将会写入程序版本信息
IF EXIST "%compile_path%\file_version_info.txt" (
	SET version_file=--version-file "%compile_path\%file_version_info.txt"
) ELSE (
	SET version_file= 
)

REM 打包路径含有 .env 或 .venv 的虚拟运行环境，会先激活 Python 虚拟运行环境
ECHO.
IF EXIST "%compile_path%\.env\Scripts\activate.bat" (
	ECHO [32m正在激活脚本运行的 Python 虚拟环境...[0m
	SET env_path=%compile_path%\.env
	CALL "%compile_path%\.env\Scripts\activate.bat"
)
IF EXIST %compile_path%\.venv\Scripts\activate.bat (
	ECHO [32m正在激活脚本运行的 Python 虚拟环境...[0m
	SET env_path=%compile_path%\.venv
	CALL "%compile_path%\.venv\Scripts\activate.bat"
)

ECHO.
ECHO [31mPyInstaller %compile_mode% %show_console% %version_file% %package_icon% %add_data% --name %compile_name% "%compile_file%"
ECHO [90m
pyinstaller %compile_mode% %show_console% %version_file% %package_icon% %add_data% --name %compile_name% "%compile_file%"
IF ERRORLEVEL 1 (
	ECHO.
	ECHO [31m打包 Python 脚本时出现错误! [0m
) ELSE (
	ECHO.
	ECHO [32m脚本 %compile_file% 打包完成。[0m
)

IF EXIST "%compile_path%\.env\Scripts\deactivate.bat" (
	ECHO.
	ECHO [32m正在退出脚本运行的 Python 虚拟环境...[0m
	CALL "%compile_path%\.env\Scripts\deactivate.bat"
)
IF EXIST "%compile_path%\.venv\Scripts\deactivate.bat" (
	ECHO.
	ECHO [32m正在退出脚本运行的 Python 虚拟环境...[0m
	CALL "%compile_path%\.venv\Scripts\deactivate.bat"
)
ECHO.
PAUSE
