# Naukri Profile Auto-Updater

Automatically updates your Naukri profile **3 times a day** (9 AM, 1 PM, 7 PM)
so you always appear "recently active" to recruiters.

---

## Folder structure

```
naukri_updater/
├── naukri_updater.py   ← main script
├── .env                ← your credentials (never share this file)
├── requirements.txt    ← Python dependencies
├── README.md
└── naukri_updater.log  ← auto-created when script runs
```

---

## Step-by-step setup

### 1. Install Python
Download Python 3.10+ from https://www.python.org/downloads/
Make sure to check **"Add Python to PATH"** during installation.

### 2. Install Google Chrome
Download from https://www.google.com/chrome/

### 3. Install dependencies
Open a terminal / Command Prompt in this folder and run:
```bash
pip install -r requirements.txt
```

### 4. Fill in your credentials
Open `.env` and replace the placeholder values:
```
NAUKRI_EMAIL=mdimrose0@gmail.com
NAUKRI_PASSWORD=YourActualPassword
HEADLESS=false
```
Leave HEADLESS=false the first time so you can watch it work.

### 5. Run the script
```bash
python naukri_updater.py
```
The script will:
- Run an update immediately on startup
- Then repeat at 09:00, 13:00, and 19:00 every day
- Write every action to `naukri_updater.log`

---

## Optional: Email alerts

To receive email alerts when the update succeeds or fails:

1. Enable **2-Step Verification** on your Gmail account
2. Go to: Google Account → Security → App Passwords
3. Create an app password (select "Mail" + "Windows Computer")
4. Copy the 16-character password into `.env`:
```
ALERT_EMAIL=your_gmail@gmail.com
ALERT_EMAIL_PASSWORD=abcd efgh ijkl mnop
NOTIFY_EMAIL=your_gmail@gmail.com
```

---

## Keep it running 24/7

### Option A — Leave your PC on
Just keep the terminal window open. The script runs continuously.

### Option B — Windows Task Scheduler
1. Open Task Scheduler → Create Basic Task
2. Trigger: Daily, repeat every 8 hours
3. Action: Start a program → `python` → Arguments: `C:\path\to\naukri_updater.py`

### Option C — Free cloud VM (Oracle Cloud — always free)
1. Create a free Oracle Cloud account at cloud.oracle.com
2. Spin up a free Ubuntu VM
3. Upload this folder via SCP or FileZilla
4. Run: `nohup python3 naukri_updater.py &`
5. It runs 24/7 even when your PC is off

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ChromeDriver not found` | Run `pip install webdriver-manager` and it auto-downloads |
| Login fails / stays on login page | Check credentials in `.env`; try with HEADLESS=false |
| CAPTCHA appears | Set HEADLESS=false and complete it manually once; cookies persist |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Script stops after one run | Make sure the `while True` loop at the bottom is not interrupted |

---

## Changing schedule times

Open `naukri_updater.py` and edit this line near the top:
```python
SCHEDULE_TIMES = ["09:00", "13:00", "19:00"]
```
Use 24-hour format. You can add or remove times freely.

---

## Security reminder
- Never upload `.env` to GitHub or share it with anyone
- Add `.env` to your `.gitignore` if using Git
