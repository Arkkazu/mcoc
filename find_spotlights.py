import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://playcontestofchampions.com"
CATEGORY_URL = f"{BASE_URL}/news/category/champion-spotlights/"
OUT_FILE = Path("data/champions.json")

MONTH_RE = (
    "JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|"
    "JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
)
DATE_RE = re.compile(rf"^({MONTH_RE})\s+\d{{1,2}},\s+\d{{4}}$")


@dataclass(frozen=True)
class ChampionSpotlight:
    title: str
    url: str
    date: str | None = None
    display_date: str | None = None
    source: str = CATEGORY_URL


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def build_driver(*, headless: bool) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,1200")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)


def category_page_url(page_number: int) -> str:
    if page_number <= 1:
        return CATEGORY_URL
    return f"{CATEGORY_URL.rstrip('/')}/page/{page_number}/"


def normalize_url(href: str) -> str:
    absolute = urljoin(BASE_URL, href)
    parts = urlsplit(absolute)
    path = parts.path
    if not path.endswith("/"):
        path += "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def is_champion_spotlight_url(href: str) -> bool:
    path = urlsplit(href).path
    if not path.endswith("/"):
        path += "/"
    return path.startswith("/news/champion-spotlight-")


def parse_date(date_text: str) -> str:
    return datetime.strptime(date_text.title(), "%B %d, %Y").date().isoformat()


def title_from_url(url: str) -> str:
    slug = urlsplit(url).path.rstrip("/").split("/")[-1]
    slug = slug.removeprefix("champion-spotlight-")
    return " ".join(word.upper() if len(word) <= 3 else word.title() for word in slug.split("-"))


def parse_spotlight_link(text: str, href: str) -> ChampionSpotlight:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    date_index = next(
        (index for index, line in enumerate(lines) if DATE_RE.match(line.upper())),
        None,
    )

    display_date = None
    date = None
    title = None

    if date_index is not None:
        display_date = lines[date_index].upper()
        date = parse_date(display_date)
        if date_index + 1 < len(lines):
            title = lines[date_index + 1]

    if not title:
        title = lines[-1] if lines else title_from_url(href)

    return ChampionSpotlight(
        title=title,
        url=normalize_url(href),
        date=date,
        display_date=display_date,
    )


def extract_spotlights_from_page(driver: webdriver.Chrome) -> list[ChampionSpotlight]:
    items: list[ChampionSpotlight] = []
    seen: set[str] = set()

    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/news/champion-spotlight-"]')
    for link in links:
        href = normalize_url(link.get_attribute("href") or "")
        if not is_champion_spotlight_url(href) or href in seen:
            continue

        items.append(parse_spotlight_link(link.text or "", href))
        seen.add(href)

    return items


def has_next_page(driver: webdriver.Chrome, next_page_number: int) -> bool:
    expected = category_page_url(next_page_number)
    for link in driver.find_elements(By.CSS_SELECTOR, 'a[href*="/news/category/champion-spotlights/page/"]'):
        if normalize_url(link.get_attribute("href") or "") == expected:
            return True
    return False


def fetch_spotlights(*, max_pages: int | None, headless: bool, wait_seconds: int) -> list[ChampionSpotlight]:
    driver = build_driver(headless=headless)
    try:
        results: list[ChampionSpotlight] = []
        seen_urls: set[str] = set()
        page_number = 1

        while max_pages is None or page_number <= max_pages:
            url = category_page_url(page_number)
            driver.get(url)

            if "404" in driver.title or "Page not found" in driver.title:
                break

            try:
                WebDriverWait(driver, wait_seconds).until(
                    lambda current_driver: len(extract_spotlights_from_page(current_driver)) > 0
                )
            except TimeoutException:
                break

            page_items = extract_spotlights_from_page(driver)
            new_count = 0
            for item in page_items:
                if item.url in seen_urls:
                    continue
                seen_urls.add(item.url)
                results.append(item)
                new_count += 1

            print(f"page {page_number}: {new_count} 件")

            if new_count == 0 or not has_next_page(driver, page_number + 1):
                break
            page_number += 1

        return results
    finally:
        driver.quit()


def save_results(path: Path, items: list[ChampionSpotlight], *, details: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if details:
        payload = {
            "source": CATEGORY_URL,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "items": [asdict(item) for item in items],
        }
    else:
        payload = [item.url for item in items]

    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MCOC公式サイトのChampion Spotlights記事URLを収集します。"
    )
    parser.add_argument("--output", type=Path, default=OUT_FILE, help="保存先JSON。初期値: data/champions.json")
    parser.add_argument("--max-pages", type=int, default=None, help="確認する最大ページ数。未指定なら最後まで確認します。")
    parser.add_argument("--wait", type=int, default=20, help="ページ読み込み待機秒数。初期値: 20")
    parser.add_argument("--headed", action="store_true", help="Chrome画面を表示して実行します。")
    parser.add_argument("--details", action="store_true", help="URLだけでなくタイトル・日付もJSONに保存します。")
    parser.add_argument("--no-save", action="store_true", help="ファイル保存せず取得件数だけ確認します。")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()

    if args.max_pages is not None and args.max_pages < 1:
        print("--max-pages は1以上を指定してください。", file=sys.stderr)
        return 2

    items = fetch_spotlights(
        max_pages=args.max_pages,
        headless=not args.headed,
        wait_seconds=args.wait,
    )

    if not items:
        print("Champion Spotlight記事が見つかりませんでした。", file=sys.stderr)
        return 1

    if not args.no_save:
        save_results(args.output, items, details=args.details)
        print(f"\n合計 {len(items)} 件 -> {args.output} に保存しました")
    else:
        print(f"\n合計 {len(items)} 件")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
