# AI-Powered Industrial Quality Inspection System

## Overview

This project is an AI-powered real-time industrial quality inspection system using YOLOv8 for detecting surface defects in manufactured products.

## Features

- Real-time defect detection
- Live webcam inspection
- FastAPI backend
- Streamlit dashboard
- SQLite database
- Inspection history
- PDF reports
- Arduino/PLC integration
- Analytics dashboard

## Tech Stack

- Python
- YOLOv8
- OpenCV
- FastAPI
- Streamlit
- SQLite
- Plotly

## Backend configuration

The API requires environment variables; credentials are never stored in source code.
Set a long random `JWT_SECRET`, plus `APP_USERNAME` and `APP_PASSWORD`, before
starting the backend. On startup, the configured operator is inserted into the
SQLite `users` table with a PBKDF2 password hash. Changing the password requires
provisioning a new user or updating the stored hash; do not commit a `.env` file.

PowerShell example:

```powershell
$env:JWT_SECRET = [guid]::NewGuid().ToString('N')
$env:APP_USERNAME = 'operator'
$env:APP_PASSWORD = '<set-a-local-password>'
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```