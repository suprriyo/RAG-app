import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.shl.com"
CATALOG_BASE = "https://www.shl.com/solutions/products/product-catalog/?start={}&type=2"

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

assessment_urls = set()


for start in range(0, 300, 12):  
    page_url = CATALOG_BASE.format(start)
    driver.get(page_url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = soup.find_all("a", href=True)

    for link in links:
        href = link["href"]
        if "/product-catalog/view/" in href:
            full_url = urljoin(BASE_URL, href)
            assessment_urls.add(full_url)

print(f"🔗 Found {len(assessment_urls)} assessment links")


assessments = []

for idx, url in enumerate(assessment_urls, start=1):
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    name = soup.find("h1")
    name = name.get_text(strip=True) if name else "Unknown"

    duration = None
    for h4 in soup.find_all("h4"):
        if "Assessment length" in h4.text:
            dur_text = h4.find_next_sibling(string=True)
            if dur_text:
                duration = dur_text.strip().replace("Approximate Completion Time in minutes = ", "") + " minutes"
            break

    test_type = "Unknown"
    for h4 in soup.find_all("h4"):
        if "Test Type" in h4.text:
            type_text = h4.find_next_sibling(string=True)
            if type_text:
                test_type = type_text.strip()
            break

    remote = any("Remote Testing" in h4.text for h4 in soup.find_all("h4"))
    adaptive = any("Adaptive/IRT" in h4.text for h4 in soup.find_all("h4"))

    assessments.append({
        "name": name,
        "url": url,
        "duration": duration,
        "test_type": test_type,
        "remote": remote,
        "adaptive": adaptive
    })

    print(f"✅ [{idx}/{len(assessment_urls)}] Scraped: {name}")

driver.quit()


with open("assessments.json", "w", encoding="utf-8") as f:
    json.dump(assessments, f, indent=4, ensure_ascii=False)

print("✅ All assessments saved to 'assessments.json'")
