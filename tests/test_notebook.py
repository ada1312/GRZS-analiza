import contextlib
import io
import json
import math
import statistics
import unittest
from pathlib import Path
from unittest.mock import patch


NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "grzs_analiza.ipynb"


class NotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import matplotlib
        except ModuleNotFoundError as error:
            if error.name != "matplotlib":
                raise
            raise unittest.SkipTest("Install requirements-notebook.txt to test charts.") from error
        matplotlib.use("Agg")

    def test_charts_and_age_grouping(self):
        import matplotlib.pyplot as plt

        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        namespace = {}
        figures = []

        def capture_figure():
            figure = plt.gcf()
            figure.canvas.draw()
            figures.append(figure)
            plt.close(figure)

        try:
            with (
                patch.object(plt, "show", side_effect=capture_figure),
                contextlib.redirect_stdout(io.StringIO()),
                plt.rc_context(),
            ):
                for cell in notebook["cells"]:
                    if cell["cell_type"] == "code":
                        exec(compile("".join(cell["source"]), str(NOTEBOOK), "exec"), namespace)

            self.assertEqual(len(figures), 11)
            groups = namespace["age_groups"]
            metrics = [metric for group in groups.values() for metric in group]
            self.assertEqual(len(metrics), len(set(metrics)))
            self.assertEqual(set(metrics), namespace["age_metrics"])
            self.assertEqual([len(group) for group in groups.values()], [2, 1, 2, 1])
            self.assertIn("osebe18do55Let", metrics)
            self.assertNotIn("otroci18do55Let", metrics)

            for index, year in enumerate(namespace["years"]):
                source_total = sum(
                    row["value"] for row in namespace["rows"]
                    if row["year"] == year and row["section"] == "poskodovanecStarost"
                )
                grouped_total = sum(values[index] for values in namespace["age_values"].values())
                self.assertEqual(grouped_total, source_total)

            reference_year = namespace["reference_year"]
            expected_counts = [
                sum(
                    row["value"] for row in namespace["rows"]
                    if row["year"] == reference_year
                    and row["section"] == "poskodovanecStarost"
                    and row["metric"] in group
                )
                for group in (groups[label] for label in namespace["age_order"])
            ]
            self.assertEqual(namespace["reference_age_counts"], expected_counts)
            self.assertEqual(namespace["reference_age_total"], sum(expected_counts))
            self.assertEqual(expected_counts, sorted(expected_counts, reverse=True))
            age_bars = figures[4].axes[0]
            self.assertEqual([bar.get_width() for bar in age_bars.patches], expected_counts)
            self.assertEqual(
                [text.get_text() for text in age_bars.texts],
                [
                    f"{count:,.0f}  ({count / sum(expected_counts):.1%})"
                    for count in expected_counts
                ],
            )
            for figure in (figures[1], figures[5]):
                reference_values = []
                for ax in figure.axes:
                    if ax.get_visible():
                        self.assertEqual(ax.get_ylim()[0], 0)
                        self.assertEqual(len(ax.patches), 1)
                        reference_values.append(
                            ax.lines[0].get_ydata()[namespace["years"].index(reference_year)]
                        )
                self.assertEqual(reference_values, sorted(reference_values, reverse=True))
            action_ax, rescuer_ax = figures[2].axes
            action_order = namespace["action_order"]
            self.assertNotIn("resevalcev", action_order)
            self.assertEqual(len(action_ax.lines), len(namespace["action_metrics"]) - 1)
            action_counts = []
            for line, metric in zip(action_ax.lines, action_order):
                expected_values = [
                    namespace["totals"][(year, "akcijaTip", metric)]
                    for year in namespace["years"]
                ]
                self.assertEqual(list(line.get_ydata()), expected_values)
                action_counts.append(expected_values[namespace["years"].index(reference_year)])
            self.assertEqual(action_counts, sorted(action_counts, reverse=True))
            self.assertEqual(
                [text.get_text() for text in action_ax.get_legend().get_texts()],
                [namespace["action_labels"][metric] for metric in action_order],
            )
            self.assertEqual(
                [bar.get_height() for bar in rescuer_ax.containers[0]],
                [namespace["totals"][(year, "akcijaTip", "resevalcev")]
                 for year in namespace["years"]],
            )
            self.assertFalse(action_ax.get_shared_y_axes().joined(action_ax, rescuer_ax))
            for ax in (action_ax, rescuer_ax):
                self.assertEqual(ax.get_ylim()[0], 0)
            for figure in (figures[3], figures[4], figures[6]):
                ax = figure.axes[0]
                widths = [bar.get_width() for bar in ax.patches]
                self.assertTrue(ax.yaxis_inverted())
                self.assertEqual(widths, sorted(widths, reverse=True))
            legend_counts = [
                namespace["totals"][(reference_year, "intervencije", item[1])]
                for item in namespace["intervention_series"]
            ]
            self.assertEqual(legend_counts, sorted(legend_counts, reverse=True))
            self.assertEqual(
                [text.get_text() for text in figures[0].axes[0].get_legend().get_texts()],
                [item[0] for item in namespace["intervention_series"]],
            )
            calculate_cagr = namespace["calculate_cagr"]
            self.assertAlmostEqual(calculate_cagr(100, 121, 2000, 2002), 0.1)
            self.assertAlmostEqual(calculate_cagr(100, 81, 2000, 2002), -0.1)
            self.assertEqual(calculate_cagr(100, 0, 2000, 2002), -1)
            for args in ((0, 100, 2000, 2002), (100, -1, 2000, 2002),
                         (100, 121, 2002, 2002), (100, 121, 2003, 2002),
                         (float("nan"), 100, 2000, 2002),
                         (100, float("inf"), 2000, 2002)):
                with self.assertRaises(ValueError):
                    calculate_cagr(*args)
            self.assertLess(namespace["cagr_end_year"], namespace["latest_year"])
            self.assertEqual(
                namespace["cagr_years"],
                [year for year in namespace["years"]
                 if year < namespace["latest_year"] and year != 2007],
            )
            growth_line = figures[7].axes[0].lines[0]
            for year, value in zip(growth_line.get_xdata(), growth_line.get_ydata()):
                if year == 2007:
                    self.assertTrue(math.isnan(value))
                else:
                    self.assertEqual(value, namespace["totals"][(year, "intervencije", "zakljucene")])
            self.assertAlmostEqual(
                namespace["intervention_cagr"],
                calculate_cagr(
                    namespace["cagr_counts"][0], namespace["cagr_counts"][-1],
                    namespace["cagr_start_year"], namespace["cagr_end_year"],
                ),
            )
            self.assertAlmostEqual(namespace["cagr_curve"][0], namespace["cagr_counts"][0])
            self.assertAlmostEqual(namespace["cagr_curve"][-1], namespace["cagr_counts"][-1])
            report_years = namespace["report_years"]
            self.assertNotIn(namespace["latest_year"], report_years)
            self.assertEqual(report_years[-1], reference_year)
            self.assertEqual(len(figures[8].axes), 2)
            death_axes = figures[8].axes
            self.assertEqual(death_axes[0].get_ylim(), death_axes[1].get_ylim())
            for ax, metric in zip(death_axes, namespace["death_metrics"]):
                expected = [
                    sum(row["value"] for row in namespace["rows"]
                        if row["year"] == year and row["section"] == "poskodbaVrsta"
                        and row["metric"] == metric)
                    for year in report_years
                ]
                self.assertEqual(list(ax.lines[0].get_ydata()), expected)
                self.assertEqual(namespace["death_summary"][metric]["count"], expected[-1])
                self.assertEqual(namespace["death_summary"][metric]["change"], expected[-1] - expected[-2])
            pearson_r = namespace["pearson_r"]
            self.assertAlmostEqual(pearson_r([1, 2, 3], [2, 4, 6]), 1)
            self.assertAlmostEqual(pearson_r([1, 2, 3], [6, 4, 2]), -1)
            for x, y in (([1, 1, 1], [1, 2, 3]), ([1, 2], [1, 2]),
                         ([1, 2, 3], [1, 2]), ([1, 2, float("nan")], [1, 2, 3])):
                with self.assertRaises(ValueError):
                    pearson_r(x, y)
            annual_values = namespace["annual_values"]
            with self.assertRaisesRegex(ValueError, "Missing"):
                annual_values("poskodbaVrsta", "smrtGorska", [1900])
            pairs_for = namespace["correlation_pairs"]
            self.assertEqual(
                pairs_for([2006, 2007, 2008, 2009, 2010], [1, 2, 4, 7, 11],
                          [1, 3, 5, 7, 9], changes=True, excluded_years=(2007,)),
                [(2009, 3, 2), (2010, 4, 2)],
            )
            self.assertEqual(
                pairs_for([2006, 2008, 2009], [1, 4, 7], [1, 5, 7], changes=True),
                [(2009, 3, 2)],
            )
            injury_axes = figures[9].axes
            self.assertEqual(len(injury_axes), 2)
            self.assertEqual(injury_axes[0].get_ylim(), injury_axes[1].get_ylim())
            self.assertEqual(
                namespace["injury_metrics"],
                ("tezjePoskodovanGorska", "tezjePoskodovanDrugo"),
            )
            for ax, metric in zip(injury_axes, namespace["injury_metrics"]):
                expected = [
                    sum(row["value"] for row in namespace["rows"]
                        if row["year"] == year and row["section"] == "poskodbaVrsta"
                        and row["metric"] == metric)
                    for year in namespace["years"]
                ]
                self.assertEqual(list(ax.lines[0].get_xdata()), namespace["years"])
                self.assertEqual(list(ax.lines[0].get_ydata()), expected)
                self.assertEqual(len(ax.patches), 2)
            for ax, result in zip(figures[10].axes, namespace["correlation_results"]):
                for key, r_key in (("pairs", "r"), ("sensitivity_pairs", "sensitivity_r")):
                    pairs = result[key]
                    self.assertAlmostEqual(
                        result[r_key], statistics.correlation(
                            [pair[1] for pair in pairs], [pair[2] for pair in pairs]
                        ),
                    )
                    self.assertNotIn(namespace["latest_year"], [pair[0] for pair in pairs])
                self.assertNotIn(2007, [pair[0] for pair in result["sensitivity_pairs"]])
                if result["changes"]:
                    self.assertNotIn(2008, [pair[0] for pair in result["sensitivity_pairs"]])
                self.assertEqual(len(ax.collections[0].get_offsets()), len(result["pairs"]))
        finally:
            for figure in figures:
                plt.close(figure)


if __name__ == "__main__":
    unittest.main()
