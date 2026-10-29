# 課表維護系統

Django 專案：班級與教師課表查詢、我的課表、使用者登入（Email 註冊與 LINE 登入）。

## 第一次在新電腦上執行（Windows / PowerShell）

以下指令都在專案根目錄（有 `manage.py` 的那一層）的終端機執行，一次一行，等它跑完再執行下一行。

### 1. 取得程式碼

```powershell
git clone https://github.com/KyleYang09/class-schedule-system.git
cd class-schedule-system
```

用 Fork 或其他 Git 工具 clone 也可以。

### 2. 建立並啟用虛擬環境

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

啟用成功後，提示字元前面會出現 `(.venv)`。每次重新開啟終端機都要再啟用一次。

### 3. 安裝套件

```powershell
python -m pip install -r requirements.txt
```

### 4. 建立本機資料庫

```powershell
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

`seed_demo_data` 會建立示範資料與開發用管理員帳號（只在 `DEBUG` 開啟時建立）。如果找不到這個指令，請向專案負責人確認名稱。

預設使用 SQLite，`db.sqlite3` 不會被提交到 Git，所以每台電腦的資料庫都是獨立的。若要讓正式網站上的所有使用者共用帳號，需讓部署中的 Django 使用同一個 PostgreSQL 資料庫；僅修改本機資料庫設定不會把既有 SQLite 帳號搬過去。

### 5. 設定共用 PostgreSQL（部署環境）

先在 PostgreSQL 託管服務建立資料庫，再於部署平台的環境變數中設定下列值。不要把真實密碼提交到 Git：

```text
DB_ENGINE=postgresql
DB_NAME=資料庫名稱
DB_USER=資料庫使用者
DB_PASSWORD=資料庫密碼
DB_HOST=資料庫主機
DB_PORT=5432
```

`psycopg` 驅動已列在 `requirements.txt`。部署環境安裝套件後，執行 `python manage.py migrate` 建立資料表。所有網站執行個體都必須連到同一個資料庫，並使用同一個 Django `SECRET_KEY`；不要讓每個開發者的電腦連到正式帳號資料庫。

目前本機 SQLite 的使用者不會因為切換 PostgreSQL 自動搬移。正式搬移前需先備份資料，並規劃一次性匯入；不要直接把 `db.sqlite3` 當成 PostgreSQL 資料庫檔案使用。

其他網站或應用程式若也要用同一組登入身份，應透過中央登入/API（例如 OAuth / OpenID Connect）整合，不應把資料庫帳密交給每個應用程式直接讀取 Django 的使用者資料表。

### 6. 設定網站網域（每台電腦各做一次）

打開 `http://127.0.0.1:8000/admin/` → 網站，把唯一那筆紀錄的「網域名稱」與「顯示名稱」都改成 `127.0.0.1:8000`。驗證信裡的連結會用這個網域。

### 7. 測試登入

- 登入頁：`http://127.0.0.1:8000/accounts/login/`
- 註冊頁：`http://127.0.0.1:8000/accounts/signup/`

## 驗證信解碼

開發時，信件不會真的寄出，而是印在執行 `runserver` 的終端機裡。信件含中文，內容會被編碼成一長串英數字，連結藏在裡面。

1. 在終端機中，選取信件標頭（`MIME-Version`、`Subject`、`From`、`To`、`Date`、`Message-ID` 這幾行）下方、虛線之上的那一整段英數字，複製。
2. 在**另一個**終端機視窗執行：

   ```powershell
   [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String((((Get-Clipboard) -join '') -replace '\s','')))
   ```

3. 輸出的文字裡有一行 `http://127.0.0.1:8000/accounts/confirm-email/.../`，複製整行到瀏覽器開啟，按「確認」。

如果只是想跳過驗證：進 admin 的「電子郵件地址」，找到該帳號，勾選「已驗證」後儲存。這只用在開發階段。

## LINE 登入（選用）

沒有設定也可以正常使用 Email 登入，只是 LINE 按鈕點了會出現 LINE 的錯誤頁。

專案已安裝 `django-allauth` 的 LINE provider。到 LINE Developers Console 建立 Provider 和「LINE Login」Channel，確認 Channel 的 App type 包含 Web app，並在 LINE Login 設定頁加入 callback URL：

```text
http://127.0.0.1:8000/accounts/line/login/callback/
```

本機開發時，於啟動 Django 的 PowerShell 視窗設定環境變數（每個新終端機都要重新設定）：

   ```powershell
   $env:LINE_CHANNEL_ID = "你的 Channel ID"
   $env:LINE_CHANNEL_SECRET = "你的 Channel secret"
   python manage.py runserver
   ```

正式環境要把 callback URL 換成部署網站的 HTTPS 網址，例如 `https://你的網域/accounts/line/login/callback/`，並在部署平台設定相同的兩個環境變數。Channel secret 不要貼到聊天、程式碼或 Git。LINE 登入目前要求 `profile` 與 `openid`，未要求 Email 權限，因此不可假設每個 LINE 帳號都會提供 Email。Email 相同也不會自動合併既有帳號；安全的帳號綁定流程應要求使用者先登入原帳號，再從帳號設定連結 LINE。

## 更新程式碼之後

每次 pull 了別人的變更，在 `runserver` 前先執行：

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
```

新增了套件的人，請記得更新 `requirements.txt` 並提交：

```powershell
python -m pip freeze > requirements.txt
```

## 疑難排解

| 症狀 | 原因 | 解法 |
|---|---|---|
| 終端機出現 `不支援關鍵字 'from'` | 把 Python 程式碼貼進了 PowerShell | 程式碼只能貼在 VS Code 的檔案裡；終端機只輸入指令 |
| `ModuleNotFoundError: No module named 'allauth'`（或其他套件） | 這台電腦還沒安裝套件，或沒有啟用 `.venv` | 確認提示字元有 `(.venv)`，再執行 `python -m pip install -r requirements.txt` |
| `Activate.ps1` 無法執行，顯示被系統停用 | PowerShell 執行原則 | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` |
| 安裝套件時卡住或出現 `KeyboardInterrupt` | 被中斷，或防毒軟體掃描拖慢 | 一次只執行一行並等它跑完；仍失敗就刪除 `.venv` 後重建（步驟 2、3） |
| `/accounts/login/` 或 `/accounts/signup/` 出現 404，路由清單裡沒有 `accounts/` | `config/urls.py` 是舊版 | 確認 `config/urls.py` 含 `path('accounts/', include('allauth.urls'))`，且放在 `path('', include('schedule.urls'))` 之前 |
| 同樣的 404，且 `settings.py` 也沒有 allauth 設定 | `config/` 被還原成舊版（切換分支、pull、捨棄變更） | 還原正確的 `config/urls.py` 與 `config/settings.py`，並確認所在的 Git 分支 |
| `no such table: account_emailaddress` 或其他 `no such table` | 還沒執行遷移 | `python manage.py migrate` |
| `Site matching query does not exist` | 新資料庫沒有 Site，或 `SITE_ID` 對不上 | 先 `migrate`；到 admin 的「網站」確認有 ID 為 1 的紀錄 |
| 驗證信連結打開後是 404 | 複製到多餘的字元（例如結尾的 `HTTP/1.1`），或連結被換行拆開 | 只複製 `http` 開頭到結尾 `/` 為止的整行；見上方「驗證信解碼」 |
| 驗證信裡的網址是 `example.com` | 沒有修改 Site 網域 | 見步驟 5 |
| 驗證前就能登入，或一直被導回「請驗證信箱」 | 這是預期行為：未驗證的信箱無法登入 | 完成驗證，或在 admin 勾選「已驗證」 |
| 登入頁沒有樣式、版面是預設的 | 缺少 `auth.css` 或 `auth.js`，或瀏覽器快取 | 確認 `schedule/static/schedule/css/auth.css`、`js/auth.js` 存在，重新整理（Ctrl+F5） |
| 登入太多次被擋 | 登入嘗試頻率限制（5 分鐘內失敗 5 次） | 等待幾分鐘再試 |
