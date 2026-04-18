import csv
import hashlib
import re

import config


def ensure_directories():
    for directory in (config.OUTPUT_DIR, config.RAW_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def build_raw_html_path(prefix, url):
    safe_prefix = re.sub(r"[^a-zA-Z0-9_-]+", "_", prefix).strip("_") or "page"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return config.RAW_DIR / f"{safe_prefix}_{digest}.html"


def save_raw_html(prefix, url, html):
    path = build_raw_html_path(prefix, url)
    path.write_text(html, encoding="utf-8")
    return path


def write_rows_to_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)
