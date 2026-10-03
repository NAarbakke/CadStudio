"""Specification and unit checks independent of expensive CAD builds."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import yaml
from engineering_report import UniqueLoader, component_rows, point, scalar


class ReportDataTests(unittest.TestCase):
    def test_duplicate_yaml_dimension_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            yaml.load("diameter: 16\ndiameter: 19\n", Loader=UniqueLoader)

    def test_inches_and_metres_convert_to_mm(self):
        model = SimpleNamespace(WALL=0.1875, LENGTH=2)
        self.assertAlmostEqual(scalar({"parameter": "WALL", "unit": "in"}, model), 4.7625)
        self.assertEqual(scalar({"parameter": "LENGTH", "unit": "m"}, model), 2000)
        self.assertEqual(point([0, 10, 20], model), (0, 10, 20))

    def test_invalid_coordinate_and_unit_rejected(self):
        for value in (True, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                scalar(value, SimpleNamespace())
        with self.assertRaises(ValueError):
            scalar({"parameter": "X", "unit": "inch"}, SimpleNamespace(X=1))

    def test_material_density_mass_conversion(self):
        part = SimpleNamespace(label="test", volume=1_000_000,
                               bounding_box=lambda: SimpleNamespace(size=SimpleNamespace(X=100)))
        cfg = {"part_materials": {"test": "steel"},
               "materials": {"steel": {"name": "Test steel", "density_kg_m3": 7800}}}
        self.assertEqual(component_rows(cfg, [part])[1][-1], "7.800")
        self.assertEqual(component_rows({}, [part])[1][-1], "Unknown")

    def test_missing_material_and_component_rejected(self):
        part = SimpleNamespace(label="test")
        for cfg in ({"part_materials": {"missing": "steel"}},
                    {"part_materials": {"test": "missing"}}):
            with self.assertRaises(ValueError):
                component_rows(cfg, [part])


if __name__ == "__main__":
    unittest.main()
