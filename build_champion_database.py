import argparse
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://playcontestofchampions.com"
INPUT_FILE = Path("data/champions.json")
JSON_OUTPUT = Path("data/champion_database.json")
SQLITE_OUTPUT = Path("data/champion_database.sqlite")

CLASS_NAMES = {"COSMIC", "TECH", "MUTANT", "SKILL", "SCIENCE", "MYSTIC", "SUPERIOR"}
CLASS_CORRECTIONS = {
    "Comic": "Cosmic",
    "Skilled": "Skill",
}
FOOTER_MARKERS = {
    "SUBSCRIBE FOR THE LATEST NEWS FROM KABAM",
    "THE GREATEST BATTLES IN MARVEL HISTORY ARE IN YOUR HANDS",
}
RELEASE_RE = re.compile(r"RELEASED:\s*(\d{4})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})")
RANK_RE = re.compile(r"^(\d+)-Star$", re.IGNORECASE)


@dataclass(frozen=True)
class PageData:
    url: str
    page_title: str
    source_html: str
    body_lines: list[str]


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def build_driver(*, headless: bool) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1400,1600")
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


def normalize_url(href: str, *, trailing_slash: bool = True) -> str:
    absolute = urljoin(BASE_URL, href)
    parts = urlsplit(absolute)
    path = parts.path
    if trailing_slash and not path.endswith("/"):
        path += "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def slug_from_url(url: str) -> str:
    return urlsplit(url).path.strip("/").split("/")[-1]


def load_urls(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        raw_urls = data
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        raw_urls = [item.get("url") or item.get("href") for item in data["items"]]
    else:
        raise ValueError(f"URLリストとして読めません: {path}")

    urls: list[str] = []
    seen: set[str] = set()
    for raw_url in raw_urls:
        if not isinstance(raw_url, str) or not raw_url.strip():
            continue
        url = normalize_url(raw_url)
        if url not in seen:
            urls.append(url)
            seen.add(url)
    return urls


def fetch_page(driver: webdriver.Chrome, url: str, *, wait_seconds: int, attempts: int) -> PageData:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            driver.get(url)
            try:
                WebDriverWait(driver, wait_seconds).until(
                    lambda current_driver: has_article_content(
                        current_driver.find_element(By.TAG_NAME, "body").text
                    )
                )
            except TimeoutException:
                WebDriverWait(driver, 5).until(
                    lambda current_driver: len(
                        current_driver.find_element(By.TAG_NAME, "body").text.strip()
                    )
                    > 50
                )
            body_text = driver.find_element(By.TAG_NAME, "body").text
            body_lines = [line.strip() for line in body_text.splitlines() if line.strip()]
            return PageData(
                url=url,
                page_title=driver.title,
                source_html=driver.page_source,
                body_lines=body_lines,
            )
        except (TimeoutException, WebDriverException) as exc:
            last_error = exc
            if attempt < attempts:
                sleep(2 * attempt)

    raise RuntimeError(f"ページ取得に失敗しました: {url}") from last_error


def has_article_content(body_text: str) -> bool:
    return any(
        marker in body_text
        for marker in (
            "Base Stats",
            "About ",
            "Character Class:",
            "Synergy Bonuses",
        )
    )


def meta_content(soup: BeautifulSoup, key: str) -> str | None:
    tag = soup.find("meta", property=key)
    if tag and tag.get("content"):
        return str(tag["content"]).strip()
    tag = soup.find("meta", attrs={"name": key})
    if tag and tag.get("content"):
        return str(tag["content"]).strip()
    return None


def extract_images(soup: BeautifulSoup) -> dict[str, Any]:
    og_image = meta_content(soup, "og:image")
    images: list[dict[str, str | None]] = []
    seen: set[str] = set()

    for img in soup.find_all("img"):
        raw_src = img.get("src") or img.get("data-src")
        if not raw_src or raw_src.startswith("data:"):
            continue

        src = normalize_url(str(raw_src), trailing_slash=False)
        if "/wp-content/uploads/" not in src or src in seen:
            continue

        seen.add(src)
        images.append(
            {
                "url": src,
                "alt": str(img.get("alt")).strip() if img.get("alt") else None,
            }
        )

    article_image = images[0]["url"] if images else None
    return {
        "og_image": normalize_url(og_image, trailing_slash=False) if og_image else None,
        "article_image": article_image,
        "images": images,
    }


def article_name_from_title(page_title: str, og_title: str | None, url: str) -> str:
    if page_title and " - Marvel Contest" in page_title:
        return page_title.split(" - Marvel Contest", 1)[0].strip()
    if og_title and "|" in og_title:
        return og_title.split("|", 1)[0].strip()
    if og_title:
        return og_title.strip()
    slug = slug_from_url(url).removeprefix("champion-spotlight-")
    return " ".join(word.upper() if len(word) <= 3 else word.title() for word in slug.split("-"))


def slice_content_lines(lines: list[str], name: str) -> list[str]:
    start = next((index for index, line in enumerate(lines) if line == name), None)
    if start is None:
        prev_index = next((index for index, line in enumerate(lines) if line == "PREV"), None)
        if prev_index is None and not has_article_content("\n".join(lines)):
            return []
        start = max(prev_index - 1, 0) if prev_index is not None else 0

    end = next(
        (
            index
            for index, line in enumerate(lines[start:], start=start)
            if line in FOOTER_MARKERS
        ),
        len(lines),
    )
    return lines[start:end]


def find_index(lines: list[str], value: str, start: int = 0) -> int | None:
    return next((index for index in range(start, len(lines)) if lines[index] == value), None)


def find_first_index(lines: list[str], values: set[str], start: int = 0) -> int | None:
    return next((index for index in range(start, len(lines)) if lines[index] in values), None)


def find_index_startswith(lines: list[str], prefix: str, start: int = 0) -> int | None:
    return next((index for index in range(start, len(lines)) if lines[index].startswith(prefix)), None)


def section_between(lines: list[str], start_index: int | None, end_index: int | None) -> list[str]:
    if start_index is None:
        return []
    end = end_index if end_index is not None else len(lines)
    return lines[start_index + 1 : end]


def parse_release_date(lines: list[str]) -> tuple[str | None, str | None]:
    for line in lines:
        match = RELEASE_RE.search(line)
        if match:
            year, month, day = match.groups()
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}", line
    return None, None


def parse_header_class(lines: list[str]) -> str | None:
    prev_index = find_index(lines, "PREV")
    if prev_index is not None and prev_index + 1 < len(lines):
        candidate = lines[prev_index + 1].upper()
        if candidate in CLASS_NAMES:
            return candidate.title()
    return None


def parse_character_class(lines: list[str], fallback: str | None) -> str | None:
    for line in lines:
        if line.startswith("Character Class:"):
            return normalize_champion_class(line.split(":", 1)[1].strip(), fallback=fallback)
    return normalize_champion_class(fallback, fallback=None)


def normalize_champion_class(value: str | None, *, fallback: str | None) -> str | None:
    if not value:
        return fallback

    candidate = CLASS_CORRECTIONS.get(value, value)
    if candidate.upper() in CLASS_NAMES:
        return candidate
    return fallback


def parse_basic_abilities(lines: list[str]) -> list[str]:
    for line in lines:
        if line.startswith("Basic Abilities:"):
            value = line.split(":", 1)[1].strip()
            return [item.strip() for item in value.split(",") if item.strip()]
    return []


def parse_base_stats(lines: list[str]) -> list[dict[str, Any]]:
    stats: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        match = RANK_RE.match(lines[index])
        if not match:
            index += 1
            continue

        rank_label = lines[index]
        block: list[str] = []
        index += 1
        while index < len(lines) and not RANK_RE.match(lines[index]):
            block.append(lines[index])
            index += 1

        original_text = " ".join(block)
        number_text = original_text.replace(",", "")
        numbers = [int(value) for value in re.findall(r"\d+", number_text)]
        health = attack = pi = None
        if len(numbers) >= 3:
            health, attack, pi = numbers[-3:]

        rank_level_match = re.search(r"\(([^)]+)\)", original_text)
        stats.append(
            {
                "star_rank": int(match.group(1)),
                "label": rank_label,
                "rank_level": rank_level_match.group(1) if rank_level_match else None,
                "health": health,
                "attack": attack,
                "pi_max_signature": pi,
                "raw_lines": block,
            }
        )

    return stats


def find_mechanics_index(lines: list[str], start: int = 0) -> int | None:
    return next(
        (
            index
            for index in range(start, len(lines))
            if lines[index].lower().endswith("mechanics")
            and "TABLE OF CONTENTS" not in lines[index]
        ),
        None,
    )


def clean_section_lines(lines: list[str], *prefixes_to_remove: str) -> list[str]:
    return [
        line
        for line in lines
        if not any(line.startswith(prefix) for prefix in prefixes_to_remove)
    ]


def parse_champion_summary(lines: list[str]) -> dict[str, Any]:
    attacker_index = find_index(lines, "Attacker Summary")
    defender_index = find_index(lines, "Defender Summary")
    rating_index = find_index_startswith(lines, "The following Stats and Abilities")

    attacker = section_between(lines, attacker_index, defender_index)
    defender = section_between(lines, defender_index, rating_index)
    rating_context = lines[rating_index] if rating_index is not None else None

    return {
        "attacker": attacker,
        "defender": defender,
        "rating_context": rating_context,
        "raw_lines": lines,
    }


def is_block_heading(line: str) -> bool:
    if not line or len(line) > 95:
        return False
    if line.endswith((".", ",", ";", ":")):
        return False
    if line.startswith(("With ", "All Champions", "Synergy Champions:")):
        return False
    if " – " in line:
        return True
    if line in {
        "Always Active",
        "Dev Notes",
        "Masteries",
        "Offensive Stat Focus",
        "Defensive Stat Focus",
        "Recommended Battlecast/Relic",
    }:
        return True
    return bool(re.match(r"^[A-Z0-9#][A-Za-z0-9#’'().+\- ]+$", line))


def split_blocks(lines: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in lines:
        if is_block_heading(line):
            current = {"heading": line, "lines": []}
            blocks.append(current)
        elif current is None:
            current = {"heading": None, "lines": [line]}
            blocks.append(current)
        else:
            current["lines"].append(line)

    for block in blocks:
        block["text"] = "\n".join(block["lines"])
    return blocks


def parse_record(page: PageData) -> dict[str, Any]:
    soup = BeautifulSoup(page.source_html, "html.parser")
    og_title = meta_content(soup, "og:title")
    name = article_name_from_title(page.page_title, og_title, page.url)
    content_lines = slice_content_lines(page.body_lines, name)

    about_index = find_index_startswith(content_lines, "About ")
    base_index = find_first_index(
        content_lines,
        {"Base Stats and Abilities", "Base Stats & Abilities"},
        about_index or 0,
    )
    stats_header_index = find_index_startswith(content_lines, "Health Attack PI", about_index or 0)
    stats_start_index = base_index if base_index is not None else stats_header_index
    attributes_index = find_index(content_lines, "Champion Attributes", stats_start_index or 0)
    mechanics_index = find_mechanics_index(content_lines, attributes_index or 0)
    summary_index = find_first_index(
        content_lines,
        {"Champion Summary", "Strengths and Weaknesses"},
        mechanics_index or 0,
    )
    abilities_index = find_index(content_lines, "Abilities", summary_index or 0)
    synergy_index = find_index(content_lines, "Synergy Bonuses", abilities_index or 0)
    recommended_index = next(
        (
            index
            for index, line in enumerate(content_lines)
            if index > (synergy_index or 0)
            and line.startswith("Recommended")
        ),
        None,
    )

    release_date, release_date_raw = parse_release_date(content_lines)
    header_class = parse_header_class(content_lines)

    about_end_index = base_index if base_index is not None else stats_header_index
    about_lines = section_between(content_lines, about_index, about_end_index)
    if base_index is not None:
        base_lines = section_between(content_lines, base_index, attributes_index)
    elif stats_header_index is not None:
        base_lines = content_lines[stats_header_index : attributes_index or len(content_lines)]
    else:
        base_lines = []
    attributes_lines = section_between(content_lines, attributes_index, mechanics_index)
    mechanics_lines = section_between(content_lines, mechanics_index, summary_index)
    summary_lines = section_between(content_lines, summary_index, abilities_index)
    abilities_lines = section_between(content_lines, abilities_index, synergy_index)
    synergy_lines = section_between(content_lines, synergy_index, recommended_index)
    recommended_lines = section_between(content_lines, recommended_index, None)

    mechanics_body = clean_section_lines(
        mechanics_lines,
        "Character Class:",
        "Basic Abilities:",
    )

    sections = {
        "about": about_lines,
        "base_stats_and_abilities": base_lines,
        "champion_attributes": attributes_lines,
        "mechanics": mechanics_lines,
        "champion_summary": summary_lines,
        "abilities": abilities_lines,
        "synergy_bonuses": synergy_lines,
        "recommended_masteries_stat_focus_relics": recommended_lines,
    }

    meta = {
        "title": og_title,
        "description": meta_content(soup, "og:description") or meta_content(soup, "description"),
        "canonical": normalize_url(
            soup.find("link", rel="canonical").get("href")
            if soup.find("link", rel="canonical")
            else page.url
        ),
    }

    return {
        "slug": slug_from_url(page.url),
        "name": name,
        "url": page.url,
        "page_title": page.page_title,
        "content_available": bool(
            about_index is not None or base_index is not None or stats_header_index is not None
        ),
        "champion_class": parse_character_class(content_lines, header_class),
        "release_date": release_date,
        "release_date_raw": release_date_raw,
        "basic_abilities": parse_basic_abilities(content_lines),
        "about": "\n".join(about_lines),
        "base_stats": parse_base_stats(base_lines),
        "champion_attributes": attributes_lines,
        "mechanics": {
            "heading": content_lines[mechanics_index] if mechanics_index is not None else None,
            "summary": "\n".join(mechanics_body),
            "raw_lines": mechanics_lines,
        },
        "champion_summary": parse_champion_summary(summary_lines),
        "summary_heading": content_lines[summary_index] if summary_index is not None else None,
        "abilities": {
            "raw_lines": abilities_lines,
            "blocks": split_blocks(abilities_lines),
        },
        "synergy_bonuses": {
            "raw_lines": synergy_lines,
            "blocks": split_blocks(synergy_lines),
        },
        "recommendations": {
            "raw_lines": recommended_lines,
            "blocks": split_blocks(recommended_lines),
        },
        "sections": sections,
        "meta": meta,
        "images": extract_images(soup),
        "content_lines": content_lines,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def load_existing_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        records = data["items"]
    elif isinstance(data, list):
        records = data
    else:
        return []

    for record in records:
        if isinstance(record, dict):
            record.setdefault("content_available", bool(record.get("base_stats") or record.get("about")))
            record.setdefault("summary_heading", None)
            record["champion_class"] = normalize_champion_class(
                record.get("champion_class"),
                fallback=parse_header_class(record.get("content_lines", [])),
            )
    return records


def save_json_database(path: Path, urls: list[str], records: list[dict[str, Any]], errors: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": str(INPUT_FILE),
        "source_count": len(urls),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(records),
        "error_count": len(errors),
        "errors": errors,
        "items": records,
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def save_sqlite_database(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("DROP TABLE IF EXISTS champion_sections")
        connection.execute("DROP TABLE IF EXISTS champion_base_stats")
        connection.execute("DROP TABLE IF EXISTS champions")
        connection.execute(
            """
            CREATE TABLE champions (
                slug TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                champion_class TEXT,
                release_date TEXT,
                basic_abilities_json TEXT NOT NULL,
                about TEXT,
                mechanics_summary TEXT,
                article_image TEXT,
                og_image TEXT,
                record_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE champion_base_stats (
                champion_slug TEXT NOT NULL,
                stat_index INTEGER NOT NULL,
                star_rank INTEGER NOT NULL,
                rank_level TEXT,
                health INTEGER,
                attack INTEGER,
                pi_max_signature INTEGER,
                raw_lines_json TEXT NOT NULL,
                PRIMARY KEY (champion_slug, stat_index),
                FOREIGN KEY (champion_slug) REFERENCES champions(slug)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE champion_sections (
                champion_slug TEXT NOT NULL,
                section_name TEXT NOT NULL,
                line_count INTEGER NOT NULL,
                text TEXT NOT NULL,
                lines_json TEXT NOT NULL,
                PRIMARY KEY (champion_slug, section_name),
                FOREIGN KEY (champion_slug) REFERENCES champions(slug)
            )
            """
        )

        for record in records:
            connection.execute(
                """
                INSERT INTO champions (
                    slug, name, url, champion_class, release_date,
                    basic_abilities_json, about, mechanics_summary,
                    article_image, og_image, record_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["slug"],
                    record["name"],
                    record["url"],
                    record.get("champion_class"),
                    record.get("release_date"),
                    json.dumps(record.get("basic_abilities", []), ensure_ascii=False),
                    record.get("about"),
                    record.get("mechanics", {}).get("summary"),
                    record.get("images", {}).get("article_image"),
                    record.get("images", {}).get("og_image"),
                    json.dumps(record, ensure_ascii=False),
                ),
            )
            for stat_index, stat in enumerate(record.get("base_stats", []), start=1):
                if stat.get("star_rank") is None:
                    continue
                connection.execute(
                    """
                    INSERT INTO champion_base_stats (
                        champion_slug, stat_index, star_rank, rank_level, health, attack,
                        pi_max_signature, raw_lines_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["slug"],
                        stat_index,
                        stat.get("star_rank"),
                        stat.get("rank_level"),
                        stat.get("health"),
                        stat.get("attack"),
                        stat.get("pi_max_signature"),
                        json.dumps(stat.get("raw_lines", []), ensure_ascii=False),
                    ),
                )
            for section_name, lines in record.get("sections", {}).items():
                connection.execute(
                    """
                    INSERT INTO champion_sections (
                        champion_slug, section_name, line_count, text, lines_json
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        record["slug"],
                        section_name,
                        len(lines),
                        "\n".join(lines),
                        json.dumps(lines, ensure_ascii=False),
                    ),
                )

        connection.commit()
    finally:
        connection.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="data/champions.json のChampion Spotlight URLからチャンピオンDBを作成します。"
    )
    parser.add_argument("--input", type=Path, default=INPUT_FILE, help="Champion Spotlight URLリスト。")
    parser.add_argument("--output", type=Path, default=JSON_OUTPUT, help="JSON DBの保存先。")
    parser.add_argument("--sqlite", type=Path, default=SQLITE_OUTPUT, help="SQLite DBの保存先。")
    parser.add_argument("--no-sqlite", action="store_true", help="SQLite DBを作成しません。")
    parser.add_argument("--limit", type=int, default=None, help="先頭から指定件数だけ取得します。検証用。")
    parser.add_argument("--resume", action="store_true", help="既存JSON DBにあるURLはスキップします。")
    parser.add_argument("--checkpoint-every", type=int, default=10, help="何件ごとにJSONを途中保存するか。")
    parser.add_argument("--wait", type=int, default=20, help="ページ読み込み待機秒数。")
    parser.add_argument("--attempts", type=int, default=2, help="ページごとの再試行回数。")
    parser.add_argument("--delay", type=float, default=0.25, help="ページ間の待機秒数。")
    parser.add_argument("--headed", action="store_true", help="Chrome画面を表示して実行します。")
    return parser.parse_args()


def main() -> int:
    configure_output()
    args = parse_args()

    urls = load_urls(args.input)
    if args.limit is not None:
        if args.limit < 1:
            print("--limit は1以上を指定してください。", file=sys.stderr)
            return 2
        urls = urls[: args.limit]

    existing_records = load_existing_records(args.output) if args.resume else []
    records_by_url: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for record in existing_records:
        if not record.get("url"):
            continue
        if not record.get("base_stats"):
            continue
        url = normalize_url(record["url"])
        records_by_url[url] = record
        records.append(record)
    errors: list[dict[str, str]] = []

    driver = build_driver(headless=not args.headed)
    try:
        for index, url in enumerate(urls, start=1):
            if url in records_by_url:
                print(f"[{index}/{len(urls)}] skip {url}")
                continue

            print(f"[{index}/{len(urls)}] fetch {url}")
            try:
                page = fetch_page(
                    driver,
                    url,
                    wait_seconds=args.wait,
                    attempts=args.attempts,
                )
                record = parse_record(page)
                records.append(record)
                records_by_url[url] = record
                print(
                    f"  -> {record['name']} / {record.get('champion_class') or '-'} / "
                    f"{record.get('release_date') or '-'}"
                )
            except Exception as exc:  # Keep the crawl moving and report all failures together.
                message = f"{type(exc).__name__}: {exc}"
                print(f"  !! {message}", file=sys.stderr)
                errors.append({"url": url, "error": message})

            if args.checkpoint_every > 0 and (len(records) % args.checkpoint_every == 0):
                save_json_database(args.output, urls, records, errors)

            if args.delay > 0:
                sleep(args.delay)
    finally:
        driver.quit()

    save_json_database(args.output, urls, records, errors)
    if not args.no_sqlite:
        save_sqlite_database(args.sqlite, records)

    print(f"\nJSON: {args.output} ({len(records)}件)")
    if not args.no_sqlite:
        print(f"SQLite: {args.sqlite}")
    if errors:
        print(f"失敗: {len(errors)}件", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
