"""LaTeX templating and the sample report's gas-dynamics relations, without compiling LaTeX."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "reports" / "latex"))
import jinja2
from latex_report import Raw, environment, log_errors, tex_escape
import naca_lewis_16in_ramjet as sample


class TemplateTests(unittest.TestCase):
    def render(self, source, **context):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "t.tex").write_text(source, encoding="utf-8")
            return environment(folder).get_template("t.tex").render(**context)

    def test_special_characters_escaped(self):
        self.assertEqual(tex_escape("50% of A_c & {x} #1 $ ~ ^ \\"),
                         r"50\% of A\_c \& \{x\} \#1 \$ \textasciitilde{} \textasciicircum{} \textbackslash{}")
        self.assertEqual(tex_escape(tex_escape("a_b")), r"a\_b")

    def test_values_escaped_unless_raw(self):
        self.assertEqual(self.render(r"\VAR{name} \VAR{maths|raw} \VAR{'%.2f'|format(x)}",
                                     name="profile_builder", maths=r"$A_c$", x=1.2345),
                         r"profile\_builder $A_c$ 1.23")
        self.assertEqual(Raw(r"\alpha"), tex_escape(Raw(r"\alpha")))

    def test_blocks_and_latex_braces(self):
        source = "\\BLOCK{for row in rows}\n\\textbf{\\VAR{row}} \\\\\n\\BLOCK{endfor}\n"
        self.assertEqual(self.render(source, rows=["a", "b"]), "\\textbf{a} \\\\\n\\textbf{b} \\\\\n")

    def test_missing_value_rejected(self):
        with self.assertRaises(jinja2.UndefinedError):
            self.render(r"\VAR{absent}")

    def test_log_errors_keep_context(self):
        log = "noise\n./report.tex:12: Undefined control sequence.\nl.12 \\quadNACA\n\nmore noise\n"
        self.assertEqual(log_errors(log), "./report.tex:12: Undefined control sequence.\nl.12 \\quadNACA\n")

    def test_sample_template_parses(self):
        environment().get_template("naca_lewis_16in_ramjet.tex")


class GasDynamicsTests(unittest.TestCase):
    def test_normal_shock_and_area_ratio_at_mach_2(self):
        self.assertAlmostEqual(sample.shock_recovery(2.0), 0.7209, places=4)
        self.assertAlmostEqual(sample.mach_after_normal_shock(2.0), 0.5774, places=4)
        self.assertAlmostEqual(sample.area_ratio(2.0), 1.6875, places=4)
        self.assertAlmostEqual(sample.subsonic_mach(sample.area_ratio(0.4)), 0.4, places=6)

    def test_cone_shock_matches_published_tables(self):
        # Published cone-flow tables: Mach 2, 20 degree half-angle cone -> 37.8 degree shock
        self.assertAlmostEqual(sample.cone_shock(2.0, 20.0)[0], 37.8, delta=0.1)
        self.assertIsNone(sample.cone_shock(1.1, 23.0))


if __name__ == "__main__":
    unittest.main()
