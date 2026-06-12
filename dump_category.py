import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get("https://playcontestofchampions.com/news/category/champion-spotlights/")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # /news/champion-spotlight- を含む全リンク
    print("=== champion-spotlight を含むリンク ===")
    for a in soup.find_all("a", href=True):
        if "champion-spotlight" in a["href"]:
            print(f"  {a.get_text(strip=True)[:50]:50s}  {a['href']}")

    # クラス名サンプル
    print("\n=== クラス名サンプル (50件) ===")
    seen = set()
    for tag in soup.find_all(True):
        cls = " ".join(tag.get("class", []))
        key = (tag.name, cls)
        if cls and key not in seen:
            seen.add(key)
            print(f"  <{tag.name} class='{cls}'>")
        if len(seen) >= 50:
            break
finally:
    driver.quit()
