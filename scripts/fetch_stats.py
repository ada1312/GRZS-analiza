#!/usr/bin/env python3
"""Download GRZS yearly aggregate statistics and write an analysis-friendly CSV."""

import argparse
import csv
import json
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


PAGE_URL = "https://www.grzs.si/resevanje/statistika-nesrec/"
API_URL = "https://www.grzs.si/.netlify/functions/get-stats"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CSV_FIELDS = ("year", "section", "unit", "metric", "value")


class _YearSelectParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_year_select = False
        self._in_option = False
        self._option_text: list[str] = []
        self.years: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "select":
            self._in_year_select = "js-year-select" in (attributes.get("class") or "").split()
        elif tag == "option" and self._in_year_select:
            self._in_option = True
            self._option_text = []

    def handle_data(self, data: str) -> None:
        if self._in_option:
            self._option_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "option" and self._in_option:
            text = "".join(self._option_text).strip()
            if text.isdecimal():
                self.years.append(int(text))
            self._in_option = False
        elif tag == "select":
            self._in_year_select = False


def available_years(page_html: str) -> list[int]:
    parser = _YearSelectParser()
    parser.feed(page_html)
    if not parser.years:
        raise ValueError("No years found in the GRZS year selector.")
    return sorted(set(parser.years))


def normalize_response(year: int, response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("value")
    if not isinstance(data, dict) or not data:
        raise ValueError(f"GRZS returned no statistics for {year}.")

    records: list[dict[str, Any]] = []
    for section, units in data.items():
        if not isinstance(units, list):
            raise ValueError(f"Unexpected data for section {section!r} in {year}.")
        for unit_data in units:
            if not isinstance(unit_data, dict) or not isinstance(unit_data.get("enota"), str):
                raise ValueError(f"Unexpected unit row in section {section!r} for {year}.")
            for metric, value in unit_data.items():
                if metric == "enota":
                    continue
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise ValueError(
                        f"Unexpected value for {section}.{metric} in {year}: {value!r}"
                    )
                records.append(
                    {
                        "year": year,
                        "section": section,
                        "unit": unit_data["enota"],
                        "metric": metric,
                        "value": value,
                    }
                )
    return records


def _read_url(request: Request) -> bytes:
    with urlopen(request, timeout=30) as response:
        return response.read()


def fetch_page() -> str:
    request = Request(PAGE_URL, headers={"User-Agent": "GRZS-analiza data collection"})
    return _read_url(request).decode("utf-8")


def fetch_year(year: int) -> dict[str, Any]:
    body = json.dumps({"year": str(year)}).encode("utf-8")
    request = Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "GRZS-analiza data collection",
        },
        method="POST",
    )
    response = json.loads(_read_url(request))
    if not isinstance(response, dict):
        raise ValueError(f"Unexpected response from GRZS for {year}.")
    return response


def collect(start_year: int, output_dir: Path = DATA_DIR) -> int:
    available = available_years(fetch_page())
    downloaded_years = [year for year in available if year >= start_year]
    if not downloaded_years:
        raise ValueError(f"No GRZS years found from {start_year} onward.")

    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    years = [
        year
        for year in available
        if year >= start_year or (raw_dir / f"{year}.json").exists()
    ]
    records: list[dict[str, Any]] = []

    downloaded_count = 0
    for year in years:
        raw_path = raw_dir / f"{year}.json"
        if year < start_year:
            response = json.loads(raw_path.read_text(encoding="utf-8"))
        else:
            if downloaded_count:
                time.sleep(0.25)
            response = fetch_year(year)
            downloaded_count += 1
        year_records = normalize_response(year, response)
        if year >= start_year:
            raw_path.write_text(
                json.dumps(response, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        records.extend(year_records)
        action = "Updated" if year in downloaded_years else "Reused"
        print(f"{action} {year}: {len(year_records)} metric values")

    csv_path = output_dir / "accidents.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} rows to {csv_path}")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--start-year",
        type=int,
        default=2006,
        help="first year to download (default: 2006)",
    )
    args = parser.parse_args()
    if args.start_year < 2006:
        parser.error("--start-year must be 2006 or later")
    collect(args.start_year)


if __name__ == "__main__":
    main()
