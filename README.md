# class-schedule-system

Django 課表查詢系統

## 快速開始(Windows PowerShell)

```powershell
git clone https://github.com/KyleYang09/class-schedule-system.git
cd class-schedule-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

開啟 http://127.0.0.1:8000/admin/ 登入後台。

示範帳號(僅供本機開發):

- 使用者名稱:admin
- 密碼:demo1234

若無法啟用虛擬環境，先執行一次:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

若出現確認提示，輸入 `Y` 並按 Enter，再重新執行：

```powershell
.\.venv\Scripts\Activate.ps1
```

若不想修改 PowerShell 執行政策，也可以改用 **CMD（命令提示字元）**，執行：

```cmd
.venv\Scripts\activate.bat
```

**注意事項:**

- 在 VS Code 中，可從「終端機 → 新增終端機」開啟新的終端機。
- 每次開啟新的終端機，都需要重新啟用虛擬環境，不需要重新建立 `.venv`。
- 若出現 `running scripts is disabled on this system` 或 `PSSecurityException`，代表 PowerShell 的執行政策阻擋了啟動腳本，可參考上述處理方式。
- 執行指令前，請確認目前位於包含 `manage.py` 的專案資料夾。