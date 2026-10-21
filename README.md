# class-schedule-system
Django 課表查詢系統

## 快速開始(Windows PowerShell)

git clone https://github.com/KyleYang09/class-schedule-system.git
cd class-schedule-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver

開啟 http://127.0.0.1:8000/admin/ 登入後台。

示範帳號(僅供本機開發):

- 使用者名稱:admin
- 密碼:demo1234

若無法啟用虛擬環境,先執行一次:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

py party