#!/usr/bin/env python3
"""
Production CSV to GeoJSON/FlatGeobuf Converter for ChiBlo Map POI Data
with OGP Image Download Support

This script fetches CSV data from Google Sheets and converts it to:
- Full GeoJSON (for development/debugging)
- Filtered FlatGeobuf (for production use)

Additionally, this script fetches OGP images from each blog article URL,
downloads them locally, and adds the local filename as 'og_image' field.

Input: Environment variable or interactive input (secure)
Output: Fixed format optimized for production + images in output/images/
"""

import asyncio
import csv
import getpass
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse

import aiohttp


def load_env_file(env_path: Path = Path(".env")) -> None:
    """Load environment variables from .env file if it exists."""
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()


# Production configuration
FILTERED_FIELDS = [
    'title_source',      # タイトルソース
    'link_source',       # リンクソース
    'blog_source',       # ブログソース
    'date_text',         # 日付テキスト
    'date_stamp',        # 日付スタンプ
    'name_poi',          # POI名
    'address_poi',       # POI住所
    'url_link',          # リンクURL
    'url_flag',          # URLフラグ
    'og_image',          # OGP画像ファイル名（新規追加）
]

ENV_VAR_NAME = "CHIBLO_CSV_URL"
OUTPUT_PREFIX = "chiblo_poi_with_images"

# 画像ダウンロード設定
IMAGE_OUTPUT_SUBDIR = "images"
IMAGE_CONCURRENT_LIMIT = 10   # 同時ダウンロード数
IMAGE_TIMEOUT_SECONDS = 20
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}


def log_info(message: str) -> None:
    """Log information message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] INFO: {message}")


def log_error(message: str) -> None:
    """Log error message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {message}", file=sys.stderr)


def get_csv_url() -> str:
    """
    Get CSV URL from environment variable or interactive input.

    Returns:
        CSV URL string

    Raises:
        ValueError: If no valid URL is provided
    """
    url = os.getenv(ENV_VAR_NAME)
    if url:
        log_info(f"Using CSV URL from environment variable: {ENV_VAR_NAME}")
        return url.strip()

    log_info("Environment variable not set. Please enter CSV URL interactively.")
    print("Note: URL input will be hidden for security.")

    try:
        url = getpass.getpass("Enter Google Sheets CSV URL: ").strip()
        if not url:
            raise ValueError("Empty URL provided")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return url
    except KeyboardInterrupt:
        log_error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        raise ValueError(f"Failed to get valid URL: {e}")


def fetch_csv_from_url(url: str) -> List[str]:
    """
    Fetch CSV data from the given URL.

    Args:
        url: URL to fetch CSV data from

    Returns:
        List of CSV lines as strings
    """
    try:
        log_info("Fetching CSV data from Google Sheets...")
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.getcode() != 200:
                raise HTTPError(url, response.getcode(), f"HTTP {response.getcode()}", None, None)
            content = response.read().decode('utf-8')
            lines = content.strip().split('\n')
            log_info(f"Successfully fetched {len(lines)} lines of CSV data")
            return lines
    except HTTPError as e:
        log_error(f"HTTP Error {e.code}: Failed to fetch data from URL")
        raise
    except URLError as e:
        log_error(f"URL Error: {e.reason}")
        raise
    except Exception as e:
        log_error(f"Unexpected error while fetching CSV: {e}")
        raise


def parse_csv_data(csv_lines: List[str]) -> Tuple[List[str], List[Dict]]:
    """
    Parse CSV lines into header and data rows.

    Args:
        csv_lines: List of CSV lines as strings

    Returns:
        Tuple of (headers, data_rows)
    """
    if not csv_lines:
        raise ValueError("CSV data is empty")

    try:
        csv_reader = csv.reader(csv_lines)
        headers = next(csv_reader)

        data_rows = []
        for i, row in enumerate(csv_reader, start=2):
            if len(row) != len(headers):
                log_info(f"Warning: Row {i} has {len(row)} columns, expected {len(headers)}. Skipping.")
                continue
            row_dict = dict(zip(headers, row))
            data_rows.append(row_dict)

        log_info(f"Parsed {len(data_rows)} valid data rows")
        return headers, data_rows
    except Exception as e:
        raise ValueError(f"Failed to parse CSV data: {e}")


def is_valid_url_format(url: str) -> bool:
    """Validate URL format without making HTTP requests."""
    if not url or not url.strip():
        return False
    try:
        parsed = urlparse(url.strip())
        return all([
            parsed.scheme in ['http', 'https'],
            parsed.netloc,
            '.' in parsed.netloc
        ])
    except Exception:
        return False


async def check_url_accessibility(url: str, session: aiohttp.ClientSession) -> tuple[bool, str]:
    """Check if URL is accessible via HTTP request."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        async with session.head(
            url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=20),
            allow_redirects=True
        ) as response:
            if response.status == 404:
                return False, f"HTTP error (status: {response.status}) - Not Found"
            else:
                return True, f"OK (status: {response.status})"
    except asyncio.TimeoutError:
        log_info(f"Timeout checking URL (treating as valid): {url}")
        return True, "Timeout (treated as valid)"
    except aiohttp.ClientError as e:
        log_info(f"Client error checking URL (treating as valid): {url} - {e}")
        return True, f"Client error (treated as valid): {str(e)}"
    except Exception as e:
        log_info(f"Unexpected error checking URL: {url} - {e}")
        return False, f"Unexpected error: {str(e)}"


async def filter_accessible_urls(data_rows: List[Dict]) -> List[Dict]:
    """Filter data rows to only include those with accessible URLs."""
    if not data_rows:
        return []

    log_info(f"Starting URL accessibility check for {len(data_rows)} URLs...")

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=20),
        timeout=aiohttp.ClientTimeout(total=20)
    ) as session:
        tasks = []
        for row in data_rows:
            url = row.get('link_source', '').strip()
            if url:
                tasks.append(check_url_accessibility(url, session))
            else:
                async def empty_url_task():
                    return False, "Empty URL"
                tasks.append(empty_url_task())

        batch_size = 50
        results = []

        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            processed = min(i + batch_size, len(tasks))
            log_info(f"URL check progress: {processed}/{len(tasks)} ({processed/len(tasks)*100:.1f}%)")
            if i + batch_size < len(tasks):
                await asyncio.sleep(1)

    accessible_rows = []
    excluded_urls = []

    for row, result in zip(data_rows, results):
        if isinstance(result, tuple) and len(result) == 2:
            is_accessible, reason = result
            if is_accessible:
                accessible_rows.append(row)
            else:
                url = row.get('link_source', '').strip()
                excluded_urls.append({
                    'url': url,
                    'reason': reason,
                    'poi_name': row.get('name_poi', 'Unknown'),
                    'title_source': row.get('title_source', 'Unknown')
                })
        elif isinstance(result, Exception):
            url = row.get('link_source', '').strip()
            excluded_urls.append({
                'url': url,
                'reason': f"Exception: {str(result)}",
                'poi_name': row.get('name_poi', 'Unknown'),
                'title_source': row.get('title_source', 'Unknown')
            })

    if excluded_urls:
        save_excluded_urls_log(excluded_urls)

    log_info(f"URL accessibility check completed: {len(accessible_rows)}/{len(data_rows)} URLs are accessible")
    log_info(f"Excluded {len(excluded_urls)} URLs - details saved to excluded_urls.tsv")
    return accessible_rows


def save_excluded_urls_log(excluded_urls: List[Dict]) -> None:
    """Save excluded URLs to a TSV file for manual review."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = output_dir / f"excluded_urls_{timestamp}.tsv"

    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("URL\tPOI_Name\tTitle_Source\tReason\tGenerated_Date\n")
            generated_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for item in excluded_urls:
                url = item['url'].replace('\t', ' ').replace('\n', ' ')
                poi_name = item['poi_name'].replace('\t', ' ').replace('\n', ' ')
                title_source = item['title_source'].replace('\t', ' ').replace('\n', ' ')
                reason = item['reason'].replace('\t', ' ').replace('\n', ' ')
                f.write(f"{url}\t{poi_name}\t{title_source}\t{reason}\t{generated_date}\n")
        log_info(f"Excluded URLs log saved: {log_path} ({len(excluded_urls)} entries)")
    except Exception as e:
        log_error(f"Failed to save excluded URLs log: {e}")


def validate_coordinates(lat: str, lon: str) -> Tuple[Optional[float], Optional[float]]:
    """Validate and convert coordinate strings to floats."""
    try:
        lat_float = float(lat.strip()) if lat.strip() else None
        lon_float = float(lon.strip()) if lon.strip() else None

        if lat_float is None or lon_float is None:
            return None, None
        if not (-90 <= lat_float <= 90):
            return None, None
        if not (-180 <= lon_float <= 180):
            return None, None

        return lat_float, lon_float
    except (ValueError, AttributeError):
        return None, None


# ---- OGP画像取得・ダウンロード機能 ----------------------------------------

class OGPParser(HTMLParser):
    """HTMLからog:image URLを抽出するパーサー。"""

    def __init__(self):
        super().__init__()
        self.og_image: Optional[str] = None
        self._done = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if self._done:
            return
        if tag.lower() == 'meta':
            attr_dict = dict(attrs)
            # og:image
            if attr_dict.get('property') == 'og:image' and attr_dict.get('content'):
                self.og_image = attr_dict['content']
                self._done = True
            # twitter:image (fallback)
            elif attr_dict.get('name') == 'twitter:image' and attr_dict.get('content') and not self.og_image:
                self.og_image = attr_dict['content']


def make_image_filename(article_url: str, image_url: str) -> str:
    """
    記事URLのMD5ハッシュをベース、画像URLの拡張子を付与したファイル名を生成する。

    Args:
        article_url: 記事のURL（ハッシュの素材）
        image_url: 画像のURL（拡張子の取得に使用）

    Returns:
        例: "a1b2c3d4e5f6....jpg"
    """
    hash_str = hashlib.md5(article_url.encode('utf-8')).hexdigest()

    parsed = urlparse(image_url)
    path = parsed.path.split('?')[0]  # クエリパラメータを除去
    ext = Path(path).suffix.lower()

    if ext not in SUPPORTED_IMAGE_EXTENSIONS:
        ext = '.jpg'  # 不明な拡張子はjpgとして扱う

    return f"{hash_str}{ext}"


async def fetch_ogp_image_url(
    article_url: str,
    session: aiohttp.ClientSession
) -> Optional[str]:
    """
    記事URLからog:image URLを取得する。

    Args:
        article_url: ブログ記事のURL
        session: aiohttp セッション

    Returns:
        og:image の絶対URL、取得できない場合はNone
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ChibloBot/1.0)',
            'Accept': 'text/html',
            'Accept-Language': 'ja,en;q=0.5',
        }
        async with session.get(
            article_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=IMAGE_TIMEOUT_SECONDS),
            allow_redirects=True
        ) as response:
            if response.status != 200:
                return None

            # HTMLの先頭部分のみを取得（<head>だけ読めば十分）
            content_bytes = await response.content.read(32768)  # 32KB
            try:
                content = content_bytes.decode('utf-8', errors='replace')
            except Exception:
                return None

            parser = OGPParser()
            parser.feed(content)

            if not parser.og_image:
                return None

            # 相対URLを絶対URLに変換
            abs_url = urljoin(article_url, parser.og_image)
            return abs_url

    except Exception:
        return None


async def download_image(
    image_url: str,
    dest_path: Path,
    session: aiohttp.ClientSession
) -> bool:
    """
    画像URLからファイルをダウンロードして保存する。
    すでにファイルが存在する場合はスキップ（キャッシュ扱い）。

    Args:
        image_url: 画像のURL
        dest_path: 保存先のファイルパス
        session: aiohttp セッション

    Returns:
        成功した場合True
    """
    if dest_path.exists():
        return True  # キャッシュヒット

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ChibloBot/1.0)',
        }
        async with session.get(
            image_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=IMAGE_TIMEOUT_SECONDS),
            allow_redirects=True
        ) as response:
            if response.status != 200:
                return False

            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return False

            image_data = await response.read()
            if len(image_data) < 100:  # 極端に小さいファイルは除外
                return False

            dest_path.write_bytes(image_data)
            return True

    except Exception:
        return False


async def fetch_and_download_images(
    data_rows: List[Dict],
    image_output_dir: Path
) -> List[Dict]:
    """
    全POIのブログ記事URLからOGP画像を取得・ダウンロードし、
    各rowに 'og_image' フィールドを追加して返す。

    Args:
        data_rows: POIデータの行リスト
        image_output_dir: 画像の保存先ディレクトリ

    Returns:
        og_image フィールドが追加されたデータ行リスト
    """
    image_output_dir.mkdir(parents=True, exist_ok=True)

    total = len(data_rows)
    log_info(f"Starting OGP image fetch for {total} POIs...")

    semaphore = asyncio.Semaphore(IMAGE_CONCURRENT_LIMIT)
    success_count = 0
    skip_count = 0
    fail_count = 0

    async def process_row(row: Dict, index: int) -> Dict:
        nonlocal success_count, skip_count, fail_count

        article_url = row.get('link_source', '').strip()
        row = dict(row)  # コピーして元データを変更しない
        row['og_image'] = ''

        if not article_url or not is_valid_url_format(article_url):
            fail_count += 1
            return row

        async with semaphore:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Step 1: OGP画像URLを取得
                image_url = await fetch_ogp_image_url(article_url, session)
                if not image_url:
                    fail_count += 1
                    if (index + 1) % 100 == 0:
                        log_info(f"Image fetch progress: {index + 1}/{total}")
                    return row

                # Step 2: ファイル名を決定してダウンロード
                filename = make_image_filename(article_url, image_url)
                dest_path = image_output_dir / filename

                cached = dest_path.exists()
                ok = await download_image(image_url, dest_path, session)

                if ok:
                    row['og_image'] = filename
                    if cached:
                        skip_count += 1
                    else:
                        success_count += 1
                else:
                    fail_count += 1

        if (index + 1) % 100 == 0:
            log_info(f"Image fetch progress: {index + 1}/{total} (downloaded={success_count}, cached={skip_count}, failed={fail_count})")

        return row

    tasks = [process_row(row, i) for i, row in enumerate(data_rows)]
    updated_rows = await asyncio.gather(*tasks)

    log_info(
        f"Image fetch completed: downloaded={success_count}, "
        f"cached={skip_count}, failed={fail_count}, total={total}"
    )
    return list(updated_rows)


# ---- GeoJSON変換 -----------------------------------------------------------

def convert_to_geojson_with_url_validation(headers: List[str], data_rows: List[Dict]) -> Dict:
    """Convert CSV data to GeoJSON format with URL validation, filtering, and OGP image download."""
    log_info("Starting filtered GeoJSON conversion with URL validation and image download...")

    # Step 1: Filter expired data
    active_rows = [
        row for row in data_rows
        if row.get('_flag_expired', '').strip() == '0'
    ]
    log_info(f"Active records (_flag_expired=0): {len(active_rows)} rows")

    # Step 2: URL format validation
    format_valid_rows = [
        row for row in active_rows
        if is_valid_url_format(row.get('link_source', ''))
    ]
    log_info(f"Valid URL format: {len(format_valid_rows)} rows")

    # Step 3: HTTP accessibility check
    accessible_rows = asyncio.run(filter_accessible_urls(format_valid_rows))
    log_info(f"Accessible URLs: {len(accessible_rows)} rows")

    # Step 4: OGP画像ダウンロード
    image_output_dir = Path("output") / IMAGE_OUTPUT_SUBDIR
    rows_with_images = asyncio.run(fetch_and_download_images(accessible_rows, image_output_dir))
    image_count = sum(1 for r in rows_with_images if r.get('og_image'))
    log_info(f"OGP images acquired: {image_count}/{len(rows_with_images)} POIs")

    # Step 5: Convert to GeoJSON with filtered fields
    return convert_to_geojson(headers, rows_with_images, FILTERED_FIELDS, filter_expired=False)


def convert_to_geojson(
    headers: List[str],
    data_rows: List[Dict],
    filtered_fields: Optional[List[str]] = None,
    filter_expired: bool = False
) -> Dict:
    """Convert CSV data to GeoJSON format."""
    features = []
    skipped_count = 0

    for i, row in enumerate(data_rows):
        if filter_expired:
            flag_expired = row.get('_flag_expired', '').strip()
            if flag_expired != '0':
                skipped_count += 1
                continue

        lat_str = row.get('y', '')
        lon_str = row.get('x', '')
        lat, lon = validate_coordinates(lat_str, lon_str)

        if lat is None or lon is None:
            skipped_count += 1
            continue

        fid = len(features) + 1
        properties: Dict = {"fid": fid}

        for key, value in row.items():
            if key == '_latlng':
                continue
            if filtered_fields is not None and key not in filtered_fields:
                continue
            if key == 'date_stamp' and value.strip():
                try:
                    properties[key] = int(value)
                except ValueError:
                    properties[key] = value
            else:
                properties[key] = value

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": properties
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    filter_info = f" (filtered to {len(filtered_fields)} fields)" if filtered_fields else " (all fields)"
    expired_info = " (_flag_expired=0 only)" if filter_expired else ""
    log_info(f"Created GeoJSON with {len(features)} features{filter_info}{expired_info} ({skipped_count} rows skipped)")

    return geojson


def save_geojson(geojson: Dict, output_path: Path) -> None:
    """Save GeoJSON data to file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        log_info(f"GeoJSON saved: {output_path}")
    except Exception as e:
        raise IOError(f"Failed to save GeoJSON: {e}")


def convert_to_flatgeobuf(geojson_path: Path, output_path: Path) -> None:
    """Convert GeoJSON to FlatGeobuf format using geopandas."""
    try:
        import geopandas as gpd

        log_info("Converting GeoJSON to FlatGeobuf...")
        gdf = gpd.read_file(geojson_path)
        gdf.to_file(output_path, driver='FlatGeobuf')
        log_info(f"FlatGeobuf saved: {output_path}")
    except ImportError:
        raise ImportError("geopandas not available. Install with: uv add geopandas")
    except Exception as e:
        raise IOError(f"Failed to convert to FlatGeobuf: {e}")


# ---- メイン ----------------------------------------------------------------

def main():
    """Main function for production converter with image download."""
    load_env_file()

    log_info("Starting ChiBlo Map POI data conversion (with OGP Image Download)")

    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        geojson_full_path = output_dir / f"{OUTPUT_PREFIX}_full_{timestamp}.geojson"
        fgb_filtered_path = output_dir / f"{OUTPUT_PREFIX}_filtered_{timestamp}.fgb"

        # Step 1: Get CSV URL
        csv_url = get_csv_url()

        # Step 2: Fetch CSV data
        csv_lines = fetch_csv_from_url(csv_url)

        # Step 3: Parse CSV data
        headers, data_rows = parse_csv_data(csv_lines)

        # Step 4: Convert to full GeoJSON (画像なし)
        log_info("Creating full version GeoJSON...")
        geojson_full = convert_to_geojson(headers, data_rows)
        save_geojson(geojson_full, geojson_full_path)

        # Step 5: Convert to filtered FlatGeobuf with URL validation + image download
        log_info(f"Creating filtered version FlatGeobuf with image download...")
        geojson_filtered = convert_to_geojson_with_url_validation(headers, data_rows)

        temp_geojson_path = output_dir / f"temp_filtered_{timestamp}.geojson"
        save_geojson(geojson_filtered, temp_geojson_path)
        convert_to_flatgeobuf(temp_geojson_path, fgb_filtered_path)
        temp_geojson_path.unlink()

        # Summary
        image_output_dir = output_dir / IMAGE_OUTPUT_SUBDIR
        image_count = len(list(image_output_dir.glob('*'))) if image_output_dir.exists() else 0

        log_info("Conversion completed successfully!")
        log_info("Output files:")
        log_info(f"  - Full GeoJSON:        {geojson_full_path}")
        log_info(f"  - Filtered FlatGeobuf: {fgb_filtered_path}")
        log_info(f"  - Images directory:    {image_output_dir}/ ({image_count} files)")
        log_info(f"Next step: copy {image_output_dir}/ to static/images/ for deployment")

        full_size = geojson_full_path.stat().st_size / (1024 * 1024)
        filtered_size = fgb_filtered_path.stat().st_size / (1024 * 1024)
        log_info(f"File sizes: Full={full_size:.1f}MB, Filtered={filtered_size:.1f}MB")

    except KeyboardInterrupt:
        log_error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
