@echo off
title RedAnonima - EMISOR
echo ================================================
echo    RED ANONIMA E2E - EMISOR
echo ================================================
echo.
echo Abriendo ventana del emisor...
start "EMISOR" cmd /k "python red_anonima.py"

timeout /t 2 /nobreak >nul

title RedAnonima - RECEPTOR
echo ================================================
echo    RED ANONIMA E2E - RECEPTOR
echo ================================================
echo.
echo Abriendo ventana del receptor...
start "RECEPTOR" cmd /k "python red_anonima.py"

echo.
echo Ambas ventanas abiertas.
echo Emisor y Receptor pueden comunicarse.
echo.
pause