# ── ADD THESE IMPORTS at the top of views.py ──────────────────────────────────
import re

# ── ADD THESE TWO VIEWS at the bottom of views.py ─────────────────────────────

def script_generator(request):
    """Render the script-generator form page."""
    return render(request, "launcher/generator.html")


def generate_script(request):
    """
    POST handler: receives form data and writes a new scraper .py file
    into BASE_DIR, then returns JSON {ok, filename, message}.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    # ── Pull form fields ───────────────────────────────────────────────────────
    base_url    = request.POST.get("base_url", "").strip().rstrip("/")
    login_path  = request.POST.get("login_path", "/login").strip()
    username    = request.POST.get("username", "").strip()
    password    = request.POST.get("password", "").strip()
    parent_ids_raw = request.POST.get("parent_ids", "").strip()
    lead_source = request.POST.get("lead_source", "").strip()
    output_path = request.POST.get("output_path", r"C:\Users\aushr\Music\vik\data\input").strip()

    # Selenium / driver fields
    chrome_version  = request.POST.get("chrome_version", "146").strip()
    webgl_vendor    = request.POST.get("webgl_vendor", "Intel Inc.").strip()
    webgl_renderer  = request.POST.get("webgl_renderer", "Intel Iris OpenGL").strip()
    platform_val    = request.POST.get("platform", "Win32").strip()

    # XPath fields (login form elements)
    xpath_username  = request.POST.get("xpath_username", '//*[@id="root"]/div[1]/div[2]/div/form/span/div/div/input').strip()
    xpath_password  = request.POST.get("xpath_password", '//*[@id="standard-adornment-password"]').strip()
    xpath_submit    = request.POST.get("xpath_submit", '//*[@id="root"]/div[1]/div[2]/div/form/div[5]/button/span[1]').strip()
    xpath_nav       = request.POST.get("xpath_nav", '//*[@id="root"]/ion-app/div[3]/ion-toolbar/div/div/ion-header/div/a[2]/span/span[1]').strip()

    # Reporting endpoint
    report_url      = request.POST.get("report_url", "https://reporting.uvwin2024.co/reports/v2/affiliate-report/users").strip()

    # ── Parse parent IDs ──────────────────────────────────────────────────────
    raw_ids = [x.strip() for x in re.split(r"[,\n]+", parent_ids_raw) if x.strip()]
    try:
        parent_ids_list = [int(i) for i in raw_ids]
    except ValueError:
        return JsonResponse({"ok": False, "message": "Parent IDs must be integers separated by commas."}, status=400)

    # ── Derive filename from lead_source ──────────────────────────────────────
    safe_name = re.sub(r"[^\w\-]", "_", lead_source) or "script"
    filename  = f"{safe_name}.py"

    # ── Render script from template string ───────────────────────────────────
    script_body = f'''\
import os
import time
import random
import pandas as pd
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium_stealth import stealth
import requests

# ================= CONFIG =================
BASE_URL   = "{base_url}"
LOGIN_URL  = f"{{BASE_URL}}{login_path}"
USERNAME   = "{username}"
PASSWORD   = "{password}"
PARENT_IDS = {parent_ids_list}
OUTPUT_PATH = r"{output_path}"

# ================= UTIL =================
def human_delay(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def get_driver():
    ua = UserAgent()
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={{ua.random}}")
    options.add_argument("--headless=new")
    options.add_argument("--window-position=-2000,0")
    options.add_argument("--window-size=1,1")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")

    driver = uc.Chrome(version_main={chrome_version}, options=options)
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="{platform_val}",
        webgl_vendor="{webgl_vendor}",
        renderer="{webgl_renderer}",
        fix_hairline=True,
    )
    return driver

def get_jwt_from_browser(driver):
    for storage in ["localStorage", "sessionStorage"]:
        token = driver.execute_script(f"return window.{{storage}};")
        for key in token:
            if "token" in key.lower() or "auth" in key.lower():
                print(f"✅ Found token: {{key}}")
                return token[key]
    return None

def get_cookie_string(driver):
    cookies = driver.get_cookies()
    return "; ".join([f"{{c[\'name\']}}={{c[\'value\']}}" for c in cookies])

# ================= LOGIN =================
print("🚀 Starting hidden Chrome session...")
driver = get_driver()
driver.get(LOGIN_URL)
human_delay(3, 6)

driver.find_element(By.XPATH, \'{xpath_username}\').send_keys(USERNAME)
human_delay()
driver.find_element(By.XPATH, \'{xpath_password}\').send_keys(PASSWORD)
human_delay()
driver.find_element(By.XPATH, \'{xpath_submit}\').click()

wait = WebDriverWait(driver, 10)
human_delay(3, 6)
user_mgmt_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, \'{xpath_nav}\'))
)
driver.execute_script("arguments[0].click();", user_mgmt_button)
human_delay(5, 8)

jwt_token     = get_jwt_from_browser(driver)
cookie_string = get_cookie_string(driver)
print("JWT:", jwt_token[:50] + "..." if jwt_token else "None")
print("✅ Login complete, Chrome hidden")
driver.quit()

# ================= SESSION =================
session = requests.Session()
session.headers.update({{
    "Authorization": jwt_token,
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": BASE_URL,
    "Referer": BASE_URL,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Cookie": cookie_string
}})

# ================= FETCH LOOP =================
all_dataframes = []
for idx, parent_id in enumerate(PARENT_IDS):
    print(f"\\n🚀 Fetching Parent ID: {{parent_id}}")

    url     = "{report_url}"
    payload = {{
        "user": "",
        "parentId": parent_id,
        "sortOrder": "",
        "pageSize": 25
    }}

    all_users = []
    page = 1
    human_delay(3, 6)

    while True:
        response = session.post(url, json=payload)
        print(f"Parent {{parent_id}} | Page {{page}} Status:", response.status_code)
        human_delay(2, 4)

        if response.status_code == 401:
            print("❌ JWT expired")
            break
        if response.status_code != 200:
            print("❌ Error:", response.text)
            break

        data  = response.json()
        users = data.get("userDetailsList", [])
        all_users.extend(users)
        print(f"Fetched {{len(users)}} users (Total: {{len(all_users)}})")

        next_token = data.get("nextPageToken")
        if not next_token:
            break
        payload["pageToken"] = next_token
        page += 1

    df_temp = pd.DataFrame(all_users)
    all_dataframes.append(df_temp)

# ================= COMBINE & PROCESS =================
df_all = pd.concat(all_dataframes, ignore_index=True)
df_all["Aggregate"] = df_all[["availableBalance", "myPLPoints", "exposure", "lifeTimeProfit"]].sum(axis=1)
df_final = df_all[df_all["Aggregate"] == 0].copy()
df_final["language"]      = "Hindi"
df_final["Website Name"]  = ""
df_final["Account Id"]    = df_final["username"]
df_final["Lead Source 2"] = "{lead_source}"
df_final = df_final[["phoneNumber", "username", "Lead Source 2",
                      "language", "Website Name", "Account Id", "createTime"]]
df_final["username"]   = df_final["username"].str[:-4]
df_final["Account Id"] = df_final["Account Id"].str[:-4]
df_final = df_final[df_final["phoneNumber"].notnull()]

# ================= SAVE =================
os.makedirs(OUTPUT_PATH, exist_ok=True)
os.chdir(OUTPUT_PATH)
df_final.to_csv("{safe_name}.csv", index=False)
print(f"✅ File saved: {safe_name}.csv ({{len(df_final)}} records)")
'''

    # ── Write file ────────────────────────────────────────────────────────────
    SCRIPT_DIR = r"C:\Users\aushr\Music\vik"
    dest = os.path.join(SCRIPT_DIR, filename)
    try:
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(script_body)
    except Exception as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=500)

    return JsonResponse({
        "ok": True,
        "filename": filename,
        "message": f"Script '{filename}' created successfully in {SCRIPT_DIR}"
    })
