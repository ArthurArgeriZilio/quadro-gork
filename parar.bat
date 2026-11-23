@echo off
rem Fecha a janela do servidor do Quadro aberta pelo iniciar.bat (pelo titulo da janela).
taskkill /FI "WINDOWTITLE eq Quadro (feche esta janela para parar)*" /T /F >nul 2>nul
if errorlevel 1 (echo Nenhum Quadro rodando.) else (echo Quadro parado.)
timeout /t 2 >nul
