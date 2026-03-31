@echo off
chcp 65001 >nul 2>&1
mode con cols=72 lines=35
title Cuenta Regresiva Retro
python "%~dp0cuenta_regresiva.py" %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [ERROR] Verifica que Python este instalado y en el PATH.
    echo  Descarga Python desde: https://www.python.org/downloads/
    echo.
    pause
)
