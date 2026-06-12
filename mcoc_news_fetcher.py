import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


NEWS_URL = "https://playcontestofchampions.com/news/"
CACHE_PATH = Path("data/news_cache.json")

MONTH_RE = (
    "JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|"
    "JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
)
DATE_RE = re.compile(rf"^({MONTH_RE})\s+\d{{1,2}},\s+\d{{4}}$")


@dataclass(frozen=True)
class NewsItem:
    title: str
    href: str
    date: str
    display_date: str
    category: str | None = None
    source: str = NEWS_URL


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


def normalize_url(href: str) -> str:
    absolute = urljoin(NEWS_URL, href)
    parts = urlsplit(absolute)
    path = parts.path
    if not path.endswith("/"):
        path += "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def is_article_url(href: str) -> bool:
    parts = urlsplit(href)
    path = parts.path
    if not path.endswith("/"):
        path += "/"
    if not path.startswith("/news/"):
        return False
    if path in {"/news/"}:
        return False
    if path.startswith("/news/page/"):
        return False
    if path.startswith("/news/category/"):
        return False
    return True


def parse_date(date_text: str) -> str:
    return datetime.strptime(date_text.title(), "%B %d, %Y").date().isoformat()


def parse_news_link(text: str, href: str) -> NewsItem | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    date_index = next(
        (index for index, line in enumerate(lines) if DATE_RE.match(line.upper())),
        None,
    )
    if date_index is None or date_index + 1 >= len(lines):
        return None

    display_date = lines[date_index].upper()
    title = lines[date_index + 1]
    category_lines = lines[:date_index]
    category = " / ".join(category_lines) if category_lines else None

    return NewsItem(
        title=title,
        href=normalize_url(href),
        date=parse_date(display_date),
        display_date=display_date,
        category=category,
    )


def extract_items_from_page(driver: webdriver.Chrome) -> list[NewsItem]:
    items: list[NewsItem] = []
    seen: set[str] = set()

    for link in driver.find_elements(By.CSS_SELECTOR, 'a[href*="/news/"]'):
        href = normalize_url(link.get_attribute("href") or "")
        if not is_article_url(href):
            continue

        item = parse_news_link(link.text or "", href)
        if item is None or item.href in seen:
            continue

        seen.add(item.href)
        items.append(item)

    return items


def page_url(page_number: int) -> str:
    if page_number <= 1:
        return NEWS_URL
    return f"{NEWS_URL.rstrip('/')}/page/{page_number}/"


def fetch_news(*, pages: int, headless: bool, wait_seconds: int) -> list[NewsItem]:
    driver = build_driver(headless=headless)
    try:
        all_items: list[NewsItem] = []
        seen: set[str] = set()

        for page_number in range(1, pages + 1):
            driver.get(page_url(page_number))
            try:
                WebDriverWait(driver, wait_seconds).until(
                    lambda current_driver: len(extract_items_from_page(current_driver)) > 0
                )
            except TimeoutException as exc:
                raise RuntimeError(
                    f"ニュース記事が見つかりませんでした: {page_url(page_number)}"
                ) from exc

            for item in extract_items_from_page(driver):
                if item.href not in seen:
                    seen.add(item.href)
                    all_items.append(item)

        return all_items
    finally:
        driver.quit()


def load_cache(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        print(f"警告: {path} がJSONとして読めないため、既読なしとして扱います。", file=sys.stderr)
        return []

    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        raw_items = data["items"]
    else:
        return []

    cached_items: list[dict] = []
    for item in raw_items:
        if isinstance(item, str):
            cached_items.append({"href": normalize_url(item)})
        elif isinstance(item, dict):
            cached_items.append(item)
    return cached_items


def item_key(item: object) -> str:
    if isinstance(item, NewsItem):
        return item.href
    if isinstance(item, str):
        return normalize_url(item)
    if isinstance(item, dict):
        return str(item.get("href") or item.get("url") or "")
    return ""


def find_new_items(fetched_items: Iterable[NewsItem], cached_items: Iterable[dict]) -> list[NewsItem]:
    cached_keys = {item_key(item) for item in cached_items}
    return [item for item in fetched_items if item.href not in cached_keys]


def save_cache(path: Path, fetched_items: list[NewsItem], cached_items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    merged: list[dict] = []
    seen: set[str] = set()

    for item in fetched_items:
        merged.append(asdict(item))
        seen.add(item.href)

    for item in cached_items:
        key = item_key(item)
        if key and key not in seen:
            merged.append(item)
            seen.add(key)

    payload = {
        "source": NEWS_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "items": merged,
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def print_items(items: list[NewsItem], *, label: str = "新着ニュース") -> None:
    if not items:
        print(f"{label}はありません。")
        return

    print(f"{label}: {len(items)}件")
    for item in items:
        category = f" [{item.category}]" if item.category else ""
        print(f"- {item.date}{category} {item.title}")
        print(f"  {item.href}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Marvel Contest of Champions公式ニュース一覧から新着記事を取得します。"
    )
    parser.add_argument("--pages", type=int, default=1, help="確認する一覧ページ数。初期値: 1")
    parser.add_argument("--cache", type=Path, default=CACHE_PATH, help="既読キャッシュJSONの保存先。")
    parser.add_argument("--wait", type=int, default=20, help="ページ読み込み待機秒数。初期値: 20")
    parser.add_argument("--headed", action="store_true", help="Chrome画面を表示して実行します。")
    parser.add_argument("--init", action="store_true", help="現在の一覧を既読として保存し、新着表示はしません。")
    parser.add_argument("--all", action="store_true", help="新着だけでなく、取得できた記事をすべて表示します。")
    parser.add_argument("--json", action="store_true", help="表示結果をJSONで出力します。")
    parser.add_argument("--no-cache-update", action="store_true", help="キャッシュを更新せずに確認だけ行います。")
    return parser.parse_args()


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    configure_output()
    args = parse_args()
    if args.pages < 1:
        print("--pages は1以上を指定してください。", file=sys.stderr)
        return 2

    cached_items = load_cache(args.cache)
    fetched_items = fetch_news(
        pages=args.pages,
        headless=not args.headed,
        wait_seconds=args.wait,
    )

    output_items = fetched_items if args.all else find_new_items(fetched_items, cached_items)

    if args.init:
        output_items = []
        print(f"現在のニュース {len(fetched_items)}件を既読として保存します。")
    elif args.json:
        print(json.dumps([asdict(item) for item in output_items], ensure_ascii=False, indent=2))
    else:
        print_items(output_items, label="取得ニュース" if args.all else "新着ニュース")

    if not args.no_cache_update:
        save_cache(args.cache, fetched_items, cached_items)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
