@echo off
chcp 65001 >nul
title Quadro (feche esta janela para parar)
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale o Python 3 ou ajuste o PATH.
  pause
  exit /b 1
)
start "" http://127.0.0.1:8765
python servidor.py
echo.
echo Servidor parado.
pause
