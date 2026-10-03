@echo off
cd /d %~dp0
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
pip install -q -r requirements.txt
if not exist .env copy .env.example .env
start http://127.0.0.1:8000
python backend\server.py
