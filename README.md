# 課表維護系統

以 Django 製作的班級與教師課表系統,可查詢班級課表、教師課表,並用「我的課表」自選課程組成個人課表。

## 功能

- **班級課表**:選擇班級,顯示一週七天的課表。
- **教師課表**:選擇或搜尋教師,顯示授課安排。
- **我的課表**:跨班級挑選課程,自動偵測衝突;資料只存在自己的瀏覽器,不需要登入。
- **資料管理**:使用 Django 後台新增與修改班級、教師、教室、節次、課程與上課時段。同一班級、教師、教室在同一時段不能重複,由資料庫保證。

## 環境需求

| 項目 | 版本 |
|---|---|
| Python | 3.12 以上 |
| Git | 任何近期版本 |
| 作業系統 | 以下指令以 Windows PowerShell 為準 |

確認版本:

```powershell
python --version
git --version
```

## 第一次執行(新電腦)

在 VS Code 開啟專案資料夾後,按 `` Ctrl + ` `` 開啟終端機,確認是 PowerShell,且目前位置在專案根目錄(有 `manage.py` 的那一層)。

**1. 取得專案**(如果已經 pull 下來可跳過)

```powershell
git clone https://github.com/KyleYang09/class-schedule-system.git
cd class-schedule-system
code .
```

**2. 建立並啟用虛擬環境**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

成功後提示符最前面會出現 `(.venv)`。

如果出現「因為這個系統上已停用指令碼執行」的錯誤,先執行一次下面這行,再重新啟用:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**3. 安裝套件**

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**4. 建立資料庫並載入示範資料**

```powershell
python manage.py migrate
python manage.py seed_demo_data
```

`seed_demo_data` 會建立節次、示範課表,以及一組開發用管理員帳號。可以重複執行,不會產生重複資料。

**5. 啟動網站**

```powershell
python manage.py runserver
```

開啟瀏覽器:

| 網址 | 內容 |
|---|---|
| http://127.0.0.1:8000/ | 課表首頁 |
| http://127.0.0.1:8000/admin/ | 資料管理後台 |

**示範帳號(僅供本機開發)**

- 使用者名稱:`admin`
- 密碼:`demo1234`

要停止網站,在終端機按 `Ctrl + C`。

## 之後每次重新開啟專案(關機後再執行)

資料庫、虛擬環境和套件都已經存在,不需要重新建立。每次只要三步:

```powershell
cd 專案所在位置\class-schedule-system
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

在 VS Code 開啟資料夾後,終端機通常已經在專案根目錄,可以省略第一行。

### 讓 VS Code 自動啟用虛擬環境(建議設定一次)

1. 按 `Ctrl + Shift + P`,輸入 `Python: Select Interpreter`。
2. 選擇 `.venv` 底下的 Python(路徑含 `.venv\Scripts\python.exe`)。
3. 之後新開的終端機會自動啟用虛擬環境,直接執行 `python manage.py runserver` 即可。

## 同步組員的更新之後

每次 `git pull` 之後,先確認有沒有新的套件或資料表變更,再啟動:

```powershell
git pull
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

這幾行都可以安全地重複執行,沒有更新時會顯示 `Requirement already satisfied` 與 `No migrations to apply`。

## 常用指令

| 目的 | 指令 |
|---|---|
| 啟動網站 | `python manage.py runserver` |
| 指定其他連接埠 | `python manage.py runserver 8001` |
| 重新載入示範資料 | `python manage.py seed_demo_data` |
| 建立自己的管理員帳號 | `python manage.py createsuperuser` |
| 修改 Model 後產生 migration | `python manage.py makemigrations schedule` |
| 套用 migration | `python manage.py migrate` |
| 檢查專案設定 | `python manage.py check` |

### 從頭重建資料庫

停止網站後執行:

```powershell
Remove-Item db.sqlite3
python manage.py migrate
python manage.py seed_demo_data
```

這只會刪除本機的 `db.sqlite3`,不影響程式碼與 GitHub。

## 常見問題

**終端機提示符前面沒有 `(.venv)`**
虛擬環境沒有啟用。執行 `.\.venv\Scripts\Activate.ps1`;若出現指令碼執行錯誤,見上方 `Set-ExecutionPolicy` 步驟。

**出現 `ModuleNotFoundError: No module named 'django'`**
通常是沒有啟用虛擬環境,或還沒執行 `pip install -r requirements.txt`。

**出現 `You have N unapplied migration(s)`**
執行 `python manage.py migrate`。

**頁面樣式看起來是舊的**
按 `Ctrl + F5` 強制重新整理。

**`Error: That port is already in use`**
先前的伺服器還在執行。到原本的終端機按 `Ctrl + C`,或改用其他連接埠:`python manage.py runserver 8001`。

**在後台看到 `no such table`**
資料庫還沒建立或已過期,執行 `python manage.py migrate`。

## 專案結構

```
class-schedule-system/
├── config/                      專案設定(settings、總路由)
├── schedule/                    課表應用程式
│   ├── migrations/              資料表變更紀錄(需提交到 Git)
│   ├── management/commands/     seed_demo_data 示範資料指令
│   ├── static/schedule/         樣式(css)與腳本(js)
│   ├── templates/               頁面樣板
│   ├── templatetags/            樣式檔自動更新版本號
│   ├── models.py                資料模型與時段衝突約束
│   ├── views.py                 查詢與課表組裝
│   ├── urls.py                  網址路由
│   └── admin.py                 後台設定
├── manage.py                    Django 管理指令入口
├── requirements.txt             套件清單
└── README.md
```

`db.sqlite3`、`.venv/`、`.env` 不會被提交到 Git,每位組員在自己的電腦上各自建立。

## 設定

| 環境變數 | 用途 | 預設 |
|---|---|---|
| `DJANGO_SECRET_KEY` | 加密金鑰 | 開發用金鑰 |
| `DJANGO_DEBUG` | `1` 為開發模式 | `1` |
| `DJANGO_ALLOWED_HOSTS` | 允許的主機名稱,逗號分隔 | 空 |

開發時不需要設定任何環境變數。正式部署前必須設定新的 `DJANGO_SECRET_KEY`、將 `DJANGO_DEBUG` 設為 `0`,並刪除示範管理員帳號 `admin`。
