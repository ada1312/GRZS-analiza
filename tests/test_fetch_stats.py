import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.fetch_stats import available_years, collect, normalize_response


class AvailableYearsTests(unittest.TestCase):
    def test_reads_only_the_statistics_year_selector(self) -> None:
        html = """
        <select class="js-year-select">
          <option>2024</option><option>2006</option><option>2024</option>
        </select>
        <select><option>1999</option></select>
        """

        self.assertEqual(available_years(html), [2006, 2024])

    def test_rejects_a_page_without_years(self) -> None:
        with self.assertRaisesRegex(ValueError, "No years found"):
            available_years("<html></html>")


class NormalizeResponseTests(unittest.TestCase):
    def test_converts_sections_to_long_records(self) -> None:
        response = {
            "value": {
                "intervencije": [
                    {"enota": "BOHINJ", "zakljucene": 40, "vse": 40},
                ],
            },
        }

        self.assertEqual(
            normalize_response(2006, response),
            [
                {
                    "year": 2006,
                    "section": "intervencije",
                    "unit": "BOHINJ",
                    "metric": "zakljucene",
                    "value": 40,
                },
                {
                    "year": 2006,
                    "section": "intervencije",
                    "unit": "BOHINJ",
                    "metric": "vse",
                    "value": 40,
                },
            ],
        )

    def test_rejects_missing_statistics(self) -> None:
        with self.assertRaisesRegex(ValueError, "no statistics"):
            normalize_response(2006, {"value": None})


class CollectTests(unittest.TestCase):
    def test_partial_refresh_keeps_earlier_cached_years(self) -> None:
        response_2019 = {"value": {"intervencije": [{"enota": "BOHINJ", "vse": 10}]}}
        response_2020 = {"value": {"intervencije": [{"enota": "BOHINJ", "vse": 12}]}}
        html = """
        <select class="js-year-select">
          <option>2020</option><option>2019</option>
        </select>
        """

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            raw_dir = output_dir / "raw"
            raw_dir.mkdir()
            (raw_dir / "2019.json").write_text(json.dumps(response_2019), encoding="utf-8")

            with (
                patch("scripts.fetch_stats.fetch_page", return_value=html),
                patch("scripts.fetch_stats.fetch_year", return_value=response_2020) as fetch_year,
            ):
                collect(2020, output_dir)

            fetch_year.assert_called_once_with(2020)
            with (output_dir / "accidents.csv").open(encoding="utf-8", newline="") as csv_file:
                years = {int(row["year"]) for row in csv.DictReader(csv_file)}
            self.assertEqual(years, {2019, 2020})


if __name__ == "__main__":
    unittest.main()
