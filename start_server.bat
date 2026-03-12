@echo off
cd /d %~dp0
echo Iniciando servidor de Guardias en http://localhost:5050
echo Presione Ctrl+C para detener
python app.py
