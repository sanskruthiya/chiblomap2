#!/usr/bin/env python3
"""
Production CSV to GeoJSON/FlatGeobuf Converter for ChiBlo Map POI Data

This script fetches CSV data from Google Sheets and converts it to:
- Full GeoJSON (for development/debugging)
- Filtered FlatGeobuf (for production use)

Input: Environment variable or interactive input (secure)
Output: Fixed format optimized for production
"""

import asyncio
import csv
import getpass
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

import aiohttp


def load_env_file(env_path: Path = Path(".env")) -> None:
    """Load environment variables from .env file if it exists."""
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already in environment
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
    'url_flag'           # URLフラグ
]

ENV_VAR_NAME = "CHIBLO_CSV_URL"
OUTPUT_PREFIX = "chiblo_poi"


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
    # Try environment variable first
    url = os.getenv(ENV_VAR_NAME)
    if url:
        log_info(f"Using CSV URL from environment variable: {ENV_VAR_NAME}")
        return url.strip()
    
    # Fallback to interactive input
    log_info("Environment variable not set. Please enter CSV URL interactively.")
    print("Note: URL input will be hidden for security.")
    
    try:
        url = getpass.getpass("Enter Google Sheets CSV URL: ").strip()
        if not url:
            raise ValueError("Empty URL provided")
        
        # Basic URL validation
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
        
    Raises:
        HTTPError: If HTTP request fails
        URLError: If URL is invalid or network error occurs
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
        
    Raises:
        ValueError: If CSV data is invalid
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
    """
    Validate URL format without making HTTP requests.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL format is valid, False otherwise
    """
    if not url or not url.strip():
        return False
    
    try:
        parsed = urlparse(url.strip())
        return all([
            parsed.scheme in ['http', 'https'],
            parsed.netloc,
            '.' in parsed.netloc  # Domain must contain at least one dot
        ])
    except Exception:
        return False


async def check_url_accessibility(url: str, session: aiohttp.ClientSession) -> tuple[bool, str]:
    """
    Check if URL is accessible via HTTP request.
    
    Args:
        url: URL to check
        session: aiohttp session for making requests
        
    Returns:
        Tuple of (is_accessible, reason) where reason explains the result
    """
    try:
        # Use realistic browser headers to avoid bot detection
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
            timeout=aiohttp.ClientTimeout(total=20),  # Increased timeout
            allow_redirects=True
        ) as response:
            # Only exclude 404 errors, treat all other status codes as valid
            if response.status == 404:
                return False, f"HTTP error (status: {response.status}) - Not Found"
            else:
                return True, f"OK (status: {response.status})"
    except asyncio.TimeoutError:
        # Timeout doesn't necessarily mean the URL is invalid
        # It could be slow response or bot protection
        log_info(f"Timeout checking URL (treating as valid): {url}")
        return True, "Timeout (treated as valid)"
    except aiohttp.ClientError as e:
        # Treat all client errors as valid URLs (including 400, 500, etc.)
        # Only 404 errors should be excluded, which are handled in the response status check above
        log_info(f"Client error checking URL (treating as valid): {url} - {e}")
        return True, f"Client error (treated as valid): {str(e)}"
    except Exception as e:
        log_info(f"Unexpected error checking URL: {url} - {e}")
        return False, f"Unexpected error: {str(e)}"


async def filter_accessible_urls(data_rows: List[Dict]) -> List[Dict]:
    """
    Filter data rows to only include those with accessible URLs.
    
    Args:
        data_rows: List of data row dictionaries
        
    Returns:
        List of data rows with accessible URLs
    """
    if not data_rows:
        return []
    
    log_info(f"Starting URL accessibility check for {len(data_rows)} URLs...")
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=20),  # Reduced concurrent connections
        timeout=aiohttp.ClientTimeout(total=20)   # Increased timeout
    ) as session:
        tasks = []
        for row in data_rows:
            url = row.get('link_source', '').strip()
            if url:
                tasks.append(check_url_accessibility(url, session))
            else:
                # Create a completed task that returns False for empty URLs
                async def empty_url_task():
                    return False, "Empty URL"
                tasks.append(empty_url_task())
        
        # Process in batches to show progress and add delays
        batch_size = 50  # Smaller batches
        results = []
        
        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Log progress
            processed = min(i + batch_size, len(tasks))
            log_info(f"URL check progress: {processed}/{len(tasks)} ({processed/len(tasks)*100:.1f}%)")
            
            # Add delay between batches to be respectful to servers
            if i + batch_size < len(tasks):
                await asyncio.sleep(1)  # 1 second delay between batches
    
    # Filter rows based on results and log excluded URLs
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
    
    # Save excluded URLs to log file
    if excluded_urls:
        save_excluded_urls_log(excluded_urls)
    
    log_info(f"URL accessibility check completed: {len(accessible_rows)}/{len(data_rows)} URLs are accessible")
    log_info(f"Excluded {len(excluded_urls)} URLs - details saved to excluded_urls.tsv")
    return accessible_rows


def save_excluded_urls_log(excluded_urls: List[Dict]) -> None:
    """
    Save excluded URLs to a TSV file for manual review.
    
    Args:
        excluded_urls: List of dictionaries containing URL exclusion details
    """
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = output_dir / f"excluded_urls_{timestamp}.tsv"
    
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("URL\tPOI_Name\tTitle_Source\tReason\tGenerated_Date\n")
            
            # Write data rows
            generated_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for item in excluded_urls:
                # Escape tabs and newlines in data
                url = item['url'].replace('\t', ' ').replace('\n', ' ')
                poi_name = item['poi_name'].replace('\t', ' ').replace('\n', ' ')
                title_source = item['title_source'].replace('\t', ' ').replace('\n', ' ')
                reason = item['reason'].replace('\t', ' ').replace('\n', ' ')
                
                f.write(f"{url}\t{poi_name}\t{title_source}\t{reason}\t{generated_date}\n")
        
        log_info(f"Excluded URLs log saved: {log_path} ({len(excluded_urls)} entries)")
        
    except Exception as e:
        log_error(f"Failed to save excluded URLs log: {e}")


def validate_coordinates(lat: str, lon: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Validate and convert coordinate strings to floats.
    
    Args:
        lat: Latitude string
        lon: Longitude string
        
    Returns:
        Tuple of (latitude, longitude) as floats, or (None, None) if invalid
    """
    try:
        lat_float = float(lat.strip()) if lat.strip() else None
        lon_float = float(lon.strip()) if lon.strip() else None
        
        if lat_float is None or lon_float is None:
            return None, None
        
        # Basic coordinate validation
        if not (-90 <= lat_float <= 90):
            return None, None
        
        if not (-180 <= lon_float <= 180):
            return None, None
        
        return lat_float, lon_float
        
    except (ValueError, AttributeError):
        return None, None


def convert_to_geojson_with_url_validation(headers: List[str], data_rows: List[Dict]) -> Dict:
    """
    Convert CSV data to GeoJSON format with URL validation and filtering.
    
    Args:
        headers: List of column headers
        data_rows: List of data row dictionaries
        
    Returns:
        GeoJSON dictionary with filtered and validated data
    """
    log_info("Starting filtered GeoJSON conversion with URL validation...")
    
    # Step 1: Filter expired data first (_flag_expired=0 only)
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
    
    # Step 4: Convert to GeoJSON with filtered fields
    return convert_to_geojson(headers, accessible_rows, FILTERED_FIELDS, filter_expired=False)


def convert_to_geojson(headers: List[str], data_rows: List[Dict], 
                      filtered_fields: Optional[List[str]] = None, 
                      filter_expired: bool = False) -> Dict:
    """
    Convert CSV data to GeoJSON format.
    
    Args:
        headers: List of column headers
        data_rows: List of data row dictionaries
        filtered_fields: Optional list of field names to include
        filter_expired: If True, exclude rows where _flag_expired != '0'
        
    Returns:
        GeoJSON dictionary
    """
    features = []
    skipped_count = 0
    
    for i, row in enumerate(data_rows):
        # Filter expired data if requested
        if filter_expired:
            flag_expired = row.get('_flag_expired', '').strip()
            if flag_expired != '0':
                skipped_count += 1
                continue
        
        # Extract coordinates
        lat_str = row.get('y', '')
        lon_str = row.get('x', '')
        
        lat, lon = validate_coordinates(lat_str, lon_str)
        
        if lat is None or lon is None:
            skipped_count += 1
            continue
        
        # Add sequential ID (fid) starting from 1
        fid = len(features) + 1
        
        # Create properties dictionary
        properties = {"fid": fid}
        
        for key, value in row.items():
            # Skip _latlng (derived field)
            if key == '_latlng':
                continue
                
            # If filtered_fields is specified, only include those fields
            if filtered_fields is not None and key not in filtered_fields:
                continue
            
            # Convert numeric strings to appropriate types
            if key == 'date_stamp' and value.strip():
                try:
                    properties[key] = int(value)
                except ValueError:
                    properties[key] = value
            else:
                properties[key] = value
        
        # Create GeoJSON feature
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
    """
    Save GeoJSON data to file.
    
    Args:
        geojson: GeoJSON dictionary
        output_path: Path to save the GeoJSON file
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        log_info(f"GeoJSON saved: {output_path}")
    except Exception as e:
        raise IOError(f"Failed to save GeoJSON: {e}")


def convert_to_flatgeobuf(geojson_path: Path, output_path: Path) -> None:
    """
    Convert GeoJSON to FlatGeobuf format using geopandas.
    
    Args:
        geojson_path: Path to input GeoJSON file
        output_path: Path to save the FlatGeobuf file
        
    Raises:
        ImportError: If geopandas is not available
        IOError: If conversion fails
    """
    try:
        import geopandas as gpd
        
        log_info("Converting GeoJSON to FlatGeobuf...")
        
        # Read GeoJSON
        gdf = gpd.read_file(geojson_path)
        
        # Save as FlatGeobuf
        gdf.to_file(output_path, driver='FlatGeobuf')
        
        log_info(f"FlatGeobuf saved: {output_path}")
        
    except ImportError:
        raise ImportError("geopandas not available. Install with: uv add geopandas")
    except Exception as e:
        raise IOError(f"Failed to convert to FlatGeobuf: {e}")


def main():
    """Main function for production converter."""
    # Load .env file if it exists
    load_env_file()
    
    log_info("Starting ChiBlo Map POI data conversion (Production Mode)")
    
    try:
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate output filenames with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        geojson_full_path = output_dir / f"{OUTPUT_PREFIX}_full_{timestamp}.geojson"
        fgb_filtered_path = output_dir / f"{OUTPUT_PREFIX}_filtered_{timestamp}.fgb"
        
        # Step 1: Get CSV URL
        csv_url = get_csv_url()
        
        # Step 2: Fetch CSV data
        csv_lines = fetch_csv_from_url(csv_url)
        
        # Step 3: Parse CSV data
        headers, data_rows = parse_csv_data(csv_lines)
        
        # Step 4: Convert to full GeoJSON
        log_info("Creating full version GeoJSON...")
        geojson_full = convert_to_geojson(headers, data_rows)
        save_geojson(geojson_full, geojson_full_path)
        
        # Step 5: Convert to filtered FlatGeobuf with URL validation
        log_info(f"Creating filtered version FlatGeobuf (fields: {len(FILTERED_FIELDS)}, with URL validation)...")
        geojson_filtered = convert_to_geojson_with_url_validation(headers, data_rows)
        
        # Save filtered as temporary GeoJSON for conversion
        temp_geojson_path = output_dir / f"temp_filtered_{timestamp}.geojson"
        save_geojson(geojson_filtered, temp_geojson_path)
        
        # Convert to FlatGeobuf
        convert_to_flatgeobuf(temp_geojson_path, fgb_filtered_path)
        
        # Clean up temporary file
        temp_geojson_path.unlink()
        
        # Summary
        log_info("Conversion completed successfully!")
        log_info("Output files:")
        log_info(f"  - Full GeoJSON: {geojson_full_path}")
        log_info(f"  - Filtered FlatGeobuf: {fgb_filtered_path}")
        
        # File size information
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
