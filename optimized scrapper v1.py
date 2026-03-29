import os
import time
import random
import threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
from selenium_stealth import stealth
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ================= CONFIG =================
BASE_URL    = "https://affiliate.winfix.fun"
LOGIN_URL   = f"{BASE_URL}/login"
USERNAME    = ""
PASSWORD    = ""
PARENT_IDS  = [17021506041, 17177263119]
OUTPUT_PATH = r'C:\Users\aushr\Music\vik\data\input'

MAX_RETRIES      = 2
PAGE_SIZE        = 100
PARALLEL_WORKERS = len(PARENT_IDS)

DELAY_BETWEEN_PAGES   = (0.8, 1.6)
DELAY_BETWEEN_PARENTS = (1.2, 2.2)
DELAY_ON_RELOGIN      = 5

# ================= TERMINAL =================
LOCK = threading.Lock()

GATEWAY_NAMES = [
    "FIRST GATEWAY",  "SECOND GATEWAY", "THIRD GATEWAY",
    "FOURTH GATEWAY", "FIFTH GATEWAY",  "SIXTH GATEWAY",
]

STATUS_ICONS = {
    "breach":  "◈",
    "enter":   "▶",
    "page":    "◆",
    "done":    "✦",
    "warn":    "⚠",
    "reauth":  "⟳",
    "save":    "◉",
    "fail":    "✖",
    "lock":    "◎",
}

def log(icon_key, message, color=None):
    icon = STATUS_ICONS.get(icon_key, "·")
    colors = {
        "cyan":   "\033[96m",
        "green":  "\033[92m",
        "yellow": "\033[93m",
        "red":    "\033[91m",
        "dim":    "\033[2m",
        "reset":  "\033[0m",
        "bold":   "\033[1m",
    }
    c  = colors.get(color, "")
    rs = colors["reset"]
    ts = time.strftime("%H:%M:%S")
    with LOCK:
        print(f"  {colors['dim']}{ts}{rs}  {c}{icon}  {message}{rs}")

def log_banner(text):
    width = 54
    border = "─" * width
    with LOCK:
        print(f"\n\033[1m\033[96m  ┌{border}┐")
        print(f"  │  {text.center(width - 2)}  │")
        print(f"  └{border}┘\033[0m\n")

def log_divider():
    with LOCK:
        print(f"  \033[2m{'·' * 54}\033[0m")


# ================= HUMAN SIMULATION =================
def human_type(element, text, driver):
    """Type character by character with randomised inter-key delays."""
    element.click()
    time.sleep(random.uniform(0.15, 0.35))
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.04, 0.14))

def human_move_and_click(driver, element):
    """Move mouse to element with slight overshoot, then click."""
    actions = ActionChains(driver)
    # Offset slightly to simulate imprecise cursor movement
    actions.move_to_element_with_offset(
        element,
        random.randint(-4, 4),
        random.randint(-3, 3)
    )
    time.sleep(random.uniform(0.1, 0.25))
    actions.click()
    actions.perform()

def random_pause(lo, hi):
    time.sleep(random.uniform(lo, hi))


# ================= DRIVER =================
def get_driver():
    ua = UserAgent()
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={ua.random}")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-extensions")
    options.add_argument("--ignore-certificate-errors")
    # Realistic timezone and language headers
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument("--timezone=Asia/Kolkata")
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


# ================= LOGIN =================
def do_login():
    log("breach", "Initiating stealth infiltration sequence...", "cyan")
    driver = get_driver()

    try:
        driver.get(LOGIN_URL)

        # ── Wait for the page to actually render ──────────────────────
        # Wait for the username input to be present — not just the URL
        wait = WebDriverWait(driver, 30)
        try:
            username_field = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//*[@id="root"]/div[1]/div[2]/div/form/span/div/div/input'
                ))
            )
        except Exception:
            with open("login_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise RuntimeError(
                "Login form did not render within 30s — "
                "check login_debug.html"
            )

        log("lock", "Login perimeter located — commencing credential injection", "cyan")

        # Human pause before touching the form
        random_pause(1.2, 2.4)

        # ── Username ──────────────────────────────────────────────────
        username_field = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*[@id="root"]/div[1]/div[2]/div/form/span/div/div/input'
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", username_field)
        random_pause(0.3, 0.7)
        human_move_and_click(driver, username_field)
        random_pause(0.2, 0.5)
        human_type(username_field, USERNAME, driver)

        log("lock", "Primary credential sequence injected", "cyan")
        random_pause(0.6, 1.2)

        # ── Password ──────────────────────────────────────────────────
        password_field = wait.until(
            EC.element_to_be_clickable((
                By.XPATH, '//*[@id="standard-adornment-password"]'
            ))
        )
        human_move_and_click(driver, password_field)
        random_pause(0.2, 0.4)
        human_type(password_field, PASSWORD, driver)

        log("lock", "Secondary credential sequence injected", "cyan")
        random_pause(0.8, 1.6)

        # ── Submit ────────────────────────────────────────────────────
        submit_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*[@id="root"]/div[1]/div[2]/div/form/div[5]/button/span[1]'
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
        random_pause(0.3, 0.6)
        human_move_and_click(driver, submit_btn)

        log("lock", "Authentication signal dispatched — awaiting clearance...", "cyan")

        # ── Wait for redirect ─────────────────────────────────────────
        try:
            WebDriverWait(driver, 25).until(
                lambda d: d.current_url != LOGIN_URL
            )
        except Exception:
            with open("login_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise RuntimeError(
                "No redirect after login — credentials may be wrong, "
                "or a CAPTCHA appeared. Check login_debug.html"
            )

        log("breach", "Perimeter cleared — advancing to inner sanctum", "cyan")
        random_pause(3.5, 6.0)   # let post-login SPA fully settle

        # ── Nav button ────────────────────────────────────────────────
        nav_xpath_candidates = [
            '//*[@id="root"]/ion-app/div[3]/ion-toolbar/div/div/ion-header/div/a[2]/span/span[1]',
            '//*[@id="root"]/ion-app/div[3]/ion-toolbar/div/div/ion-header/div/a[2]',
            '//ion-header//a[2]',
            '//ion-toolbar//a[2]',
        ]

        nav_btn = None
        for xpath in nav_xpath_candidates:
            try:
                nav_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                break
            except Exception:
                continue

        if nav_btn is None:
            # Last resort — try finding any clickable link in the header
            try:
                nav_btn = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "ion-header a"))
                )
            except Exception:
                pass

        if nav_btn is None:
            with open("login_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise RuntimeError(
                "Inner sanctum nav element not found on any selector. "
                "Check login_debug.html — XPath may have shifted."
            )

        random_pause(0.4, 0.8)
        driver.execute_script("arguments[0].click();", nav_btn)

        log("breach", "Inner sanctum accessed — harvesting authorization token", "cyan")
        random_pause(5.0, 8.0)   # wait for post-nav page to fully load

        # ── Extract JWT ───────────────────────────────────────────────
        jwt_token = None
        for storage in ["localStorage", "sessionStorage"]:
            try:
                data = driver.execute_script(f"return window.{storage};")
                if data:
                    for key in data:
                        if "token" in key.lower() or "auth" in key.lower():
                            jwt_token = data[key]
                            break
            except Exception:
                pass
            if jwt_token:
                break

        # Fallback: cookies
        if not jwt_token:
            for cookie in driver.get_cookies():
                name = cookie.get("name", "").lower()
                if "token" in name or "auth" in name or "jwt" in name:
                    jwt_token = cookie["value"]
                    log("breach", "Authorization recovered from secure cookie vault", "cyan")
                    break

        if not jwt_token:
            with open("login_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise RuntimeError(
                "Breach successful but authorization token not located. "
                "Check login_debug.html — token key name may have rotated."
            )

        cookies       = driver.get_cookies()
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        log("breach", "GATEWAY BREACHED  —  authorization token secured", "green")
        return jwt_token, cookie_string

    finally:
        try:
            driver.quit()
        except Exception:
            pass


# ================= SESSION =================
class AuthSession:
    def __init__(self):
        self.jwt_token = None
        self.session   = self._build_session()
        self._lock     = threading.Lock()

    def _build_session(self):
        s = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(
                total=3,
                backoff_factor=0.4,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["POST"],
            ),
        )
        s.mount("https://", adapter)
        s.mount("http://",  adapter)
        return s

    def refresh(self):
        with self._lock:
            jwt, cookies = do_login()
            self.jwt_token = jwt
            self.session.headers.update({
                "Authorization": jwt,
                "Content-Type":  "application/json;charset=UTF-8",
                "Origin":        BASE_URL,
                "Referer":       BASE_URL,
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/146.0.0.0 Safari/537.36"
                ),
                "Cookie": cookies,
            })


# ================= API WRAPPER =================
def api_post(auth: AuthSession, url: str, payload: dict) -> dict:
    for attempt in range(MAX_RETRIES + 1):
        response = auth.session.post(url, json=payload, timeout=20)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 401:
            if attempt < MAX_RETRIES:
                log("reauth",
                    f"Countermeasure detected — re-establishing secure channel "
                    f"(attempt {attempt + 1}/{MAX_RETRIES})", "yellow")
                time.sleep(DELAY_ON_RELOGIN)
                auth.refresh()
                continue
            raise RuntimeError(
                f"Channel re-establishment failed after {MAX_RETRIES} attempts"
            )

        if response.status_code == 429:
            wait_s = int(response.headers.get("Retry-After", 15))
            log("warn",
                f"Rate-limit countermeasure — standing by for {wait_s}s", "yellow")
            time.sleep(wait_s)
            continue

        raise RuntimeError(
            f"Unexpected signal [{response.status_code}] — "
            f"{response.text[:120]}"
        )


# ================= FETCH ONE PARENT =================
def fetch_parent(auth: AuthSession, parent_id: int, index: int) -> list:
    gateway    = GATEWAY_NAMES[index] if index < len(GATEWAY_NAMES) else f"GATEWAY {index + 1}"
    report_url = "https://reporting.uvwin2024.co/reports/v2/affiliate-report/users"

    log("enter", f"Entering {gateway}  [{parent_id}]", "cyan")

    payload = {
        "user":      "",
        "parentId":  parent_id,
        "sortOrder": "",
        "pageSize":  PAGE_SIZE,
    }

    all_users = []
    page      = 1

    while True:
        data  = api_post(auth, report_url, payload)
        users = data.get("userDetailsList", [])
        all_users.extend(users)

        log("page",
            f"{gateway}  ·  sector {page:02d}  ·  "
            f"{len(users):>3} records extracted  "
            f"[running total: {len(all_users)}]", "dim")

        next_token = data.get("nextPageToken")
        if not next_token:
            break

        payload["pageToken"] = next_token
        page += 1
        time.sleep(random.uniform(*DELAY_BETWEEN_PAGES))

    log("done",
        f"{gateway} CLEARED  —  {len(all_users)} records harvested", "green")
    log_divider()
    return all_users


# ================= PARALLEL FETCH =================
def fetch_all(auth: AuthSession) -> list:
    all_records = []

    if PARALLEL_WORKERS > 1 and len(PARENT_IDS) > 1:
        log("enter",
            f"Deploying {PARALLEL_WORKERS} parallel extraction threads", "cyan")
        log_divider()
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as ex:
            futures = {
                ex.submit(fetch_parent, auth, pid, i): pid
                for i, pid in enumerate(PARENT_IDS)
            }
            for future in as_completed(futures):
                pid = futures[future]
                try:
                    all_records.extend(future.result())
                except Exception as e:
                    log("fail",
                        f"Gateway [{pid}] extraction failed — {e}", "red")
    else:
        for i, pid in enumerate(PARENT_IDS):
            all_records.extend(fetch_parent(auth, pid, i))
            if i < len(PARENT_IDS) - 1:
                time.sleep(random.uniform(*DELAY_BETWEEN_PARENTS))

    return all_records


# ================= PROCESS =================
def process(records: list) -> pd.DataFrame:
    df = pd.DataFrame(records)

    df['Aggregate'] = df[
        ['availableBalance', 'myPLPoints', 'exposure', 'lifeTimeProfit']
    ].sum(axis=1)

    df = df[df['Aggregate'] == 0].copy()
    df['language']      = "Hindi"
    df['Website Name']  = ""
    df['Account Id']    = df['username']
    df['Lead Source 2'] = ""

    df = df[[
        'phoneNumber', 'username', 'Lead Source 2',
        'language', 'Website Name', 'Account Id', 'createTime'
    ]]
    df['username']   = df['username'].str[:-4]
    df['Account Id'] = df['Account Id'].str[:-4]
    df = df[df['phoneNumber'].notnull()]
    return df


# ================= MAIN =================
if __name__ == "__main__":
    log_banner("VIKRANT EXTRACTION SYSTEM  //  ONLINE")

    t_start = time.time()

    auth = AuthSession()
    auth.refresh()
    log_divider()

    records = fetch_all(auth)

    if not records:
        log("fail",
            "Zero records extracted across all gateways — mission aborted", "red")
        exit(1)

    log("save", f"Processing {len(records)} raw intercepts...", "cyan")
    df = process(records)

    os.makedirs(OUTPUT_PATH, exist_ok=True)
    out_file = os.path.join(OUTPUT_PATH, ".csv")
    df.to_csv(out_file, index=False)

    elapsed = time.time() - t_start
    log_banner(
        f"MISSION COMPLETE  ·  {len(df)} records  ·  {elapsed:.1f}s"
    )