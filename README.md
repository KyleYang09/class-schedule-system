# 課表維護系統

Django 專案：班級與教師課表查詢、我的課表、使用者登入（Email 註冊與 LINE 登入）。

## 先搞清楚：什麼會跟著 Git 走，什麼不會

| 會跟著 Git 走 | 每台電腦要自己做 |
|---|---|
| 程式碼、模板、CSS、`settings.py` | 建立 `.venv` 並安裝套件 |
| `requirements.txt` | 建立資料庫（`migrate`）、示範資料、管理員帳號 |
| | 修改 admin 的「網站」網域 |
| | 寄信與 LINE 的金鑰（環境變數，見下方） |

金鑰與密碼**絕對不要**寫進程式碼或提交到 Git。每個人請各自申請自己的 Gmail 應用程式密碼，不要共用。

## 換電腦（或新隊友）檢查清單

以下指令都在專案根目錄（有 `manage.py` 的那一層）的終端機執行，**一次一行，等它跑完再執行下一行**。程式碼只能貼在 VS Code 的檔案裡，終端機只輸入指令。

- [ ] 1. 取得程式碼
- [ ] 2. 建立並啟用虛擬環境
- [ ] 3. 安裝套件
- [ ] 4. 建立資料庫、示範資料、管理員帳號
- [ ] 5. 設定網站網域
- [ ] 6. 設定寄信（`setx`）並**重開終端機**
- [ ] 7. 測試寄信與登入

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

啟用成功後，提示字元前面會出現 `(.venv)`。**每次重新開啟終端機都要再啟用一次。**

### 3. 安裝套件

```powershell
python -m pip install -r requirements.txt
```

安裝完成後確認：

```powershell
python -c "import allauth; print(allauth.__version__)"
```

有印出版本號才繼續。

### 4. 建立資料庫、示範資料、管理員帳號

```powershell
python manage.py migrate
python manage.py seed_demo_data
python manage.py createsuperuser
```

- `db.sqlite3` 不會被提交到 Git，每台電腦的資料庫都是獨立的，所以另一台電腦註冊過的帳號，在這台**不存在**。
- `seed_demo_data` 會建立示範資料與開發用管理員帳號（只在 `DEBUG` 開啟時建立）。如果找不到這個指令，請向專案負責人確認名稱。
- `createsuperuser` 會問使用者名稱、**電子郵件**、密碼。登入頁用的是電子郵件，所以信箱不要留空。

建立完管理員後，把這台電腦上所有有信箱的帳號標記為「已驗證」，這樣就能直接用電子郵件登入（只在開發階段使用）：

```powershell
python manage.py shell -c "from allauth.account.models import EmailAddress; from django.contrib.auth import get_user_model; [EmailAddress.objects.update_or_create(user=u, email=u.email, defaults={'verified': True, 'primary': True}) for u in get_user_model().objects.exclude(email='')]"
```

### 5. 設定網站網域

```powershell
python manage.py runserver
```

打開 `http://127.0.0.1:8000/admin/` → 網站，把唯一那筆紀錄改成：

- 網域名稱：`127.0.0.1:8000`
- 顯示名稱：`課表維護系統`（驗證信的主旨會顯示成 `[課表維護系統]`）

驗證信裡的連結會使用這個網域。

### 6. 設定寄信（方法 A：`setx`）

Django 預設只把信印在終端機。設定了 `EMAIL_HOST` 之後，才會用 SMTP 真的寄出。

先到 Google 帳戶開啟「兩步驟驗證」，再到「應用程式密碼」建立一組 16 碼密碼（不是你平常登入 Google 的密碼）。依 [Gmail SMTP 限制說明](https://serversmtp.com/limits-of-gmail-smtp-server/)，一般 Gmail 帳號每天上限為 500 位收件人。

在 PowerShell 執行一次（密碼請去掉空格）：

```powershell
setx EMAIL_HOST "smtp.gmail.com"
setx EMAIL_HOST_USER "你的帳號@gmail.com"
setx EMAIL_HOST_PASSWORD "16碼應用程式密碼"
```

**重要：`setx` 只對「之後新開」的終端機生效，目前已開的終端機和 VS Code 都不會有。**
請把 VS Code 整個關掉（所有視窗）再重開，或另外開一個新的 PowerShell 視窗，然後確認設定有生效：

```powershell
Get-ChildItem Env:EMAIL*
```

應該會列出 `EMAIL_HOST`、`EMAIL_HOST_USER`、`EMAIL_HOST_PASSWORD`。

**改回「只印在終端機」（不寄信）：**

```powershell
setx EMAIL_HOST ""
```

重開終端機後生效。完全刪除一個變數：

```powershell
reg delete HKCU\Environment /v EMAIL_HOST /f
```

**注意：** `setx` 把值存在這台電腦的使用者設定裡，只有你的 Windows 帳號看得到。不要在共用電腦上這樣做，離開前請刪除。

### 7. 測試寄信與登入

先單獨測試寄信，不用走完註冊流程：

```powershell
python manage.py sendtestemail 你要收信的信箱@example.com
```

沒有出現錯誤、收件匣（或垃圾郵件匣）收到信，就代表設定正確。

再用瀏覽器測試：

- 登入頁：`http://127.0.0.1:8000/accounts/login/`
- 註冊頁：`http://127.0.0.1:8000/accounts/signup/`

**驗證信裡的連結網域是 `127.0.0.1:8000`，只有這台電腦能開。** 用手機點信裡的連結會打不開，請在同一台電腦開信件並點連結。要讓手機也能用，必須先部署到公開網址。

## 登入後的流程（引導頁）

第一次登入（Email 或 LINE）後，會先進入 `/welcome/` 選擇身分：

- **學生**：選擇班級，或選「我不在列表中」（外校或其他）。
- **老師**：從清單選擇自己的姓名；找不到可以自己新增，新增的姓名要管理員在 admin 的「教師」頁面勾選後按「核准選取的教師」，才會出現在公開的教師課表。

設定完成後使用者無法自行修改，管理員可以在 admin 的「使用者資料」修改。管理員（staff）帳號會略過這一頁。

### 我的課表與加退選

「我的課表」需要登入學生帳號；未完成身分設定的帳號會先進入 `/welcome/`，教師帳號則會前往自己的教師課表。登入後，學生班級中的課程預設加入個人課表，選課異動會儲存在帳號中，可跨裝置查看。

課程在 admin 預設標記為必修。必修會自動加入且不能退選；管理員可在「課程」清單取消「必修」，將課程設為可退選。學生也能加選其他班級的課程。加退選以個人異動（`CourseOverride`）保存，儲存前會檢查所有已選課程的星期與節次；有衝突時必須先調整才能儲存。

從舊版升級時，如果這個瀏覽器曾有 `localStorage` 課表，頁面會先保留並提示匯入；打開「編輯課表」並儲存後會將選課寫入登入帳號。

要測試這個流程，請用**一般帳號**註冊並驗證信箱（不要用 `createsuperuser` 建立的管理員）。

資料表有異動時，記得執行：

```powershell
python manage.py makemigrations schedule
python manage.py migrate
```

遷移檔請由**一個人**產生並提交到 Git，其他人 pull 之後只要 `migrate`。

## 沒有設定寄信時：驗證信解碼

沒有設定 `EMAIL_HOST` 時，信件不會真的寄出，而是印在執行 `runserver` 的終端機裡。信件含中文，內容會被編碼成一長串英數字，連結藏在裡面。

1. 在終端機中，選取信件標頭（`MIME-Version`、`Subject`、`From`、`To`、`Date`、`Message-ID` 這幾行）下方、虛線之上的那一整段英數字，複製。
2. 在**另一個**終端機視窗執行：

   ```powershell
   [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String((((Get-Clipboard) -join '') -replace '\s','')))
   ```

3. 輸出的文字裡有一行 `http://127.0.0.1:8000/accounts/confirm-email/.../`，複製整行到瀏覽器開啟，按「確認」。

不想這麼麻煩：進 admin 的「電子郵件地址」，找到該帳號，勾選「已驗證」後儲存（只在開發階段使用）。

## LINE 登入（選用）

沒有設定也可以正常使用 Email 登入，只是 LINE 按鈕點了會出現 LINE 的錯誤頁。

1. 到 LINE Developers Console 建立 Provider 與「LINE Login」Channel。
2. Callback URL 填：`http://127.0.0.1:8000/accounts/line/login/callback/`
3. 在 PowerShell 執行一次，然後重開終端機與 VS Code：

   ```powershell
   setx LINE_CHANNEL_ID "你的 Channel ID"
   setx LINE_CHANNEL_SECRET "你的 Channel secret"
   ```

LINE 預設不提供使用者信箱，所以用 LINE 登入的人，與用 Email 註冊的人是不同的帳號。

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

### 環境與安裝

| 症狀 | 原因 | 解法 |
|---|---|---|
| 終端機出現 `不支援關鍵字 'from'` | 把 Python 程式碼貼進了 PowerShell | 程式碼只能貼在 VS Code 的檔案裡；終端機只輸入指令 |
| `IndentationError: unexpected indent`，指向檔案第一行 | 貼進檔案的程式碼前面多了空白（從有縮排的清單複製） | 在該行開頭按 Backspace，讓 `from` 或 `import` 貼齊最左邊；或全選刪除後重貼 |
| `ModuleNotFoundError: No module named 'allauth'`（或其他套件） | 這台電腦還沒安裝套件，或沒有啟用 `.venv` | 確認提示字元有 `(.venv)`，再執行 `python -m pip install -r requirements.txt` |
| 安裝完 `requirements.txt` 仍找不到 `allauth` | `requirements.txt` 是安裝 allauth 之前產生的舊版 | 在檔案加一行 `django-allauth[socialaccount]==65.21.0`，重新安裝，並提交 |
| `Activate.ps1` 無法執行，顯示被系統停用 | PowerShell 執行原則 | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` |
| 安裝套件時卡住或出現 `KeyboardInterrupt` | 被中斷，或防毒軟體掃描拖慢 | 一次只執行一行並等它跑完；仍失敗就刪除 `.venv` 後重建（步驟 2、3） |
| 安裝某個套件時編譯失敗 | 這台電腦的 Python 版本和別人不同（例如 3.13 與 3.14） | 把完整錯誤訊息貼給專案負責人；或改用與其他人相同的 Python 版本 |
| `python` 或 `pip` 找不到指令 | 沒有安裝 Python，或安裝時沒有勾選加入 PATH | 重新安裝 Python 並勾選「Add python.exe to PATH」 |

### 設定被還原或不一致

| 症狀 | 原因 | 解法 |
|---|---|---|
| `/accounts/login/` 或 `/accounts/signup/` 出現 404，路由清單裡沒有 `accounts/` | `config/urls.py` 是舊版 | 確認 `config/urls.py` 含 `path('accounts/', include('allauth.urls'))`，且放在 `path('', include('schedule.urls'))` 之前 |
| `Model class allauth.account.models.EmailAddress doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS` | `config/settings.py` 是舊版，沒有註冊 allauth | 還原正確的 `settings.py`：`INSTALLED_APPS` 要有 `django.contrib.sites`、`allauth`、`allauth.account`、`allauth.socialaccount`、`allauth.socialaccount.providers.line` |
| 以上兩種 404 / 錯誤同時出現，或改好的檔案又不見了 | `config/` 被還原成舊版（切換分支、pull、在 Fork 捨棄變更） | 確認所在的 Git 分支與是否有未提交的變更；還原正確的檔案後記得提交 |
| 登入頁沒有樣式、版面是預設的 | 缺少 `auth.css` 或 `auth.js`，或瀏覽器快取 | 確認 `schedule/static/schedule/css/auth.css`、`js/auth.js` 存在，重新整理（Ctrl+F5） |
| `TemplateDoesNotExist: account/...` | `schedule/templates/account/` 的模板沒有放到正確位置 | 確認資料夾是 `schedule/templates/account/`，不是 `schedule/templates/schedule/account/` |

### 資料庫

| 症狀 | 原因 | 解法 |
|---|---|---|
| `no such table: account_emailaddress` 或其他 `no such table` | 還沒執行遷移 | `python manage.py migrate` |
| `schedule` 的資料表不存在，且 `migrate` 沒有任何動作 | `schedule/migrations/` 沒有提交到 Git | 請**一個人**執行 `python manage.py makemigrations schedule` 並提交，其他人 pull 後再 `migrate`；不要每個人各自產生，否則會衝突 |
| `Site matching query does not exist` | 新資料庫沒有 Site，或 `SITE_ID` 對不上 | 先 `migrate`；到 admin 的「網站」確認有 ID 為 1 的紀錄 |
| 用另一台電腦註冊的帳號，在這台登入失敗 | 每台電腦的 `db.sqlite3` 是獨立的 | 在這台重新建立帳號（步驟 4） |

### 寄信

| 症狀 | 原因 | 解法 |
|---|---|---|
| 設定了 `setx` 卻還是只印在終端機 | `setx` 只對新開的終端機生效 | 關閉所有 VS Code 視窗再重開，用 `Get-ChildItem Env:EMAIL*` 確認有值 |
| `SMTPAuthenticationError`，訊息含 `Username and Password not accepted` 或 `Application-specific password required` | 用了平常的 Google 密碼，或沒開兩步驟驗證 | 開啟兩步驟驗證，建立「應用程式密碼」，用它重新 `setx EMAIL_HOST_PASSWORD`（去掉空格） |
| `SMTPSenderRefused` 或 `Authentication Required` | 設了 `EMAIL_HOST`，但沒有設帳號或密碼 | 三個變數要一起設定：`EMAIL_HOST`、`EMAIL_HOST_USER`、`EMAIL_HOST_PASSWORD`；或把 `EMAIL_HOST` 清空改回印出模式 |
| `ConnectionRefusedError`、`TimeoutError` 或連線被拒 | 網路擋住了連接埠 587（常見於學校或公司網路） | 換一個網路（例如手機熱點）再試 |
| `socket.gaierror` / 找不到主機 | `EMAIL_HOST` 打錯，或沒有網路 | 確認是 `smtp.gmail.com`，並檢查網路連線 |
| 寄信成功但收不到 | 進了垃圾郵件匣，或信箱打錯 | 檢查垃圾郵件匣；確認註冊時的信箱沒有打錯 |
| 手機點驗證連結打不開 | 連結網域是 `127.0.0.1:8000`，只有這台電腦能開 | 在同一台電腦開信件並點連結；要讓手機可用，需先部署到公開網址 |
| 驗證信主旨是 `[example.com]` 或 `[127.0.0.1:8000]` | admin 的「網站」顯示名稱沒改 | 見步驟 5 |
| 驗證信連結打開後是 404 | 複製到多餘的字元（例如結尾的 `HTTP/1.1`），或連結被換行拆開 | 只複製 `http` 開頭到結尾 `/` 為止的整行；終端機模式請見「驗證信解碼」 |
| 驗證信裡的網址是 `example.com` | 沒有修改 Site 網域 | 見步驟 5 |
| 沒收到驗證信，重新登入也沒再寄 | 短時間內只會重寄一封 | 等待幾分鐘後，用同一組信箱與密碼再登入一次 |
| 驗證前就想登入，一直被導回「請驗證信箱」 | 這是預期行為：未驗證的信箱無法登入 | 完成驗證，或在 admin 勾選「已驗證」 |
| 登入太多次被擋 | 登入嘗試頻率限制（5 分鐘內失敗 5 次） | 等待幾分鐘再試 |

### LINE 登入

| 症狀 | 原因 | 解法 |
|---|---|---|
| 點 LINE 按鈕出現 LINE 的錯誤頁 | 沒有設定 `LINE_CHANNEL_ID` 或 `LINE_CHANNEL_SECRET`，或設定後沒有重開終端機 | 見「LINE 登入」；重開 VS Code 後用 `Get-ChildItem Env:LINE*` 確認 |
| LINE 回報 redirect_uri 不符 | Callback URL 與 LINE Developers Console 填的不一致 | 完全一致：`http://127.0.0.1:8000/accounts/line/login/callback/`（網址、連接埠、結尾斜線都要相同） |
