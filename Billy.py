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
BASE_URL = "https://affiliate.winfix.fun"
LOGIN_URL = f"{BASE_URL}/login"

USERNAME = ""
PASSWORD = ""

PARENT_IDS = [17021506041, 17177263119]

OUTPUT_PATH = r'C:\Users\Akhil\Desktop\Vikrant\data\input'

# ================= UTIL =================
def human_delay(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def get_driver():
    ua = UserAgent()
    options = uc.ChromeOptions()
    
    # Core stealth options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={ua.random}")
    
    # ✅ PERFECTLY HIDDEN - PROFESSIONAL MODE
    options.add_argument("--headless=new")                    # No visible window
    options.add_argument("--window-position=-2000,0")        # Off-screen
    options.add_argument("--window-size=1,1")                # Tiny size
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    driver = uc.Chrome(version_main=146, options=options)
    
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL",
        fix_hairline=True,
    )
    return driver

def get_jwt_from_browser(driver):
    token = driver.execute_script("return window.localStorage;")
    for key in token:
        if "token" in key.lower() or "auth" in key.lower():
            print(f"✅ Found token: {key}")
            return token[key]
    
    token = driver.execute_script("return window.sessionStorage;")
    for key in token:
        if "token" in key.lower() or "auth" in key.lower():
            print(f"✅ Found token: {key}")
            return token[key]
    
    return None

def get_cookie_string(driver):
    cookies = driver.get_cookies()
    return "; ".join([f"{c['name']}={c['value']}" for c in cookies])

# ================= LOGIN =================
print("🚀 Starting hidden Chrome session...")
driver = get_driver()
driver.get(LOGIN_URL)

human_delay(3, 6)

driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div[2]/div/form/span/div/div/input').send_keys(USERNAME)
human_delay()

driver.find_element(By.XPATH, '//*[@id="standard-adornment-password"]').send_keys(PASSWORD)
human_delay()

driver.find_element(By.XPATH, '//*[@id="root"]/div[1]/div[2]/div/form/div[5]/button/span[1]').click()

wait = WebDriverWait(driver, 10)
human_delay(3, 6)

user_mgmt_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/ion-app/div[3]/ion-toolbar/div/div/ion-header/div/a[2]/span/span[1]'))
)

driver.execute_script("arguments[0].click();", user_mgmt_button)

human_delay(5, 8)

jwt_token = get_jwt_from_browser(driver)
cookie_string = get_cookie_string(driver)

print("JWT:", jwt_token[:50] + "..." if jwt_token else "None")
print("✅ Login complete, Chrome hidden")

driver.quit()

# ================= SESSION =================
session = requests.Session()
session.headers.update({
    "Authorization": jwt_token,
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": BASE_URL,
    "Referer": BASE_URL,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Cookie": cookie_string
})

# ================= FETCH LOOP =================
all_dataframes = []

for idx, parent_id in enumerate(PARENT_IDS):
    print(f"\n🚀 Fetching Parent ID: {parent_id}")
    
    url = "https://reporting.uvwin2024.co/reports/v2/affiliate-report/users"
    
    payload = {
        "user": "",
        "parentId": parent_id,
        "sortOrder": "",
        "pageSize": 25
    }
    
    all_users = []
    page = 1
    
    human_delay(3, 6)
    
    while True:
        response = session.post(url, json=payload)
        print(f"Parent {parent_id} | Page {page} Status:", response.status_code)
        
        human_delay(2, 4)
        
        if response.status_code == 401:
            print("❌ JWT expired")
            break
        
        if response.status_code != 200:
            print("❌ Error:", response.text)
            break
        
        data = response.json()
        users = data.get("userDetailsList", [])
        all_users.extend(users)
        
        print(f"Fetched {len(users)} users (Total: {len(all_users)})")
        
        next_token = data.get("nextPageToken")
        if not next_token:
            break
        
        payload["pageToken"] = next_token
        page += 1
    
    df_temp = pd.DataFrame(all_users)
    all_dataframes.append(df_temp)

# ================= COMBINE & PROCESS =================
df_all = pd.concat(all_dataframes, ignore_index=True)
df_all['Aggregate'] = df_all[['availableBalance', 'myPLPoints', 'exposure', 'lifeTimeProfit']].sum(axis=1)

df_final = df_all[df_all['Aggregate'] == 0].copy()

df_final['language'] = "Hindi"
df_final['Website Name'] = ""
df_final['Account Id'] = df_final['username']
df_final['Lead Source 2'] = ""

df_final = df_final[['phoneNumber', 'username', 'Lead Source 2',
                     'language', 'Website Name', 'Account Id', 'createTime']]

df_final['username'] = df_final['username'].str[:-4]
df_final['Account Id'] = df_final['Account Id'].str[:-4]
df_final = df_final[df_final['phoneNumber'].notnull()]

# ================= SAVE =================
os.makedirs(OUTPUT_PATH, exist_ok=True)
os.chdir(OUTPUT_PATH)
df_final.to_csv('.csv', index=False)  # Fixed filename

print(f"✅ File saved: .csv ({len(df_final)} records)")
