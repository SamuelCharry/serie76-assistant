"""Behavioral checks for silent OCR data corruption, without downloading models."""
import tempfile
from pathlib import Path
import unittest

from scripts.ocr_lab import LAYOUTS, normalize, reconstruct, run_engine


class OCRIntegrityTests(unittest.TestCase):
    def test_formatting_does_not_repair_identity(self):
        self.assertEqual(normalize(" 761A00-11300000/A* ", "base_part_number"), "761A00-11300000/A")
        self.assertNotEqual(normalize("761AOO-11300000/A", "base_part_number"), "761A00-11300000/A")
        self.assertEqual(normalize("1,330", "on_off_torque_in_lb"), "1.33E+3")
        self.assertNotEqual(normalize("12", "fla_60hz_a"), normalize("1.2", "fla_60hz_a"))

    def test_no_ocr_output_means_no_invented_values(self):
        cells = reconstruct({p: [] for p in range(1, 5)}, 120)
        self.assertTrue(all(c["raw_text"] == "" for c in cells))
        self.assertEqual(sum(c["field"] == "base_part_number" for c in cells), 68)

    def test_same_number_in_neighboring_frequency_cannot_leak(self):
        # Row 1, FLA 60Hz; never use it as the 50Hz observation.
        pages = {p: [] for p in range(1, 5)}
        pages[1] = [{"bbox": [701, 334, 711, 346], "text": "1.2", "confidence": .99}]
        cells = reconstruct(pages, 120)
        row = {c["field"]: c for c in cells if c["source_table"] == "p1_t1" and c["source_row"] == 1}
        self.assertEqual(row["fla_60hz_a"]["raw_text"], "1.2")
        self.assertEqual(row["fla_50hz_a"]["raw_text"], "")

    def test_merged_power_stays_within_measured_span(self):
        pages = {p: [] for p in range(1, 5)}
        pages[1] = [{"bbox": [834, 344, 842, 355], "text": "15", "confidence": .99}]
        cells = reconstruct(pages, 120)
        power = [c for c in cells if c["source_table"] == "p1_t1" and c["field"] == "motor_power_w"]
        self.assertEqual([c["raw_text"] for c in power[:3]], ["15", "15", ""])

    def test_explicit_na_is_not_zero_or_blank(self):
        self.assertEqual(normalize("N/A", "data_status"), "source_NA")
        self.assertEqual(normalize("source_NA", "data_status"), "source_NA")
        self.assertIsNone(normalize("", "data_status"))
        self.assertNotEqual(normalize("0", "motor_power_w"), normalize("N/A", "data_status"))

    def test_page_four_power_spans_differ_between_voltages(self):
        pages = {p: [] for p in range(1, 5)}
        pages[4] = [{"bbox": [834, 434, 842, 446], "text": "90", "confidence": .99},
                    {"bbox": [834, 780, 842, 793], "text": "180", "confidence": .99}]
        cells = reconstruct(pages, 120)
        power = {(c["source_table"], c["source_row"]): c["raw_text"] for c in cells
                 if c["source_page"] == 4 and c["field"] == "motor_power_w"}
        self.assertEqual(power["p4_t1", 7], "90")
        self.assertEqual(power["p4_t2", 7], "180")

    def test_reject_overwrite_before_loading_any_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileExistsError):
                run_engine("tesseract", Path(folder))

    def test_reject_other_four_page_pdf_before_creating_output(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf = Path(folder) / "different.pdf"
            pdf.write_bytes(b"different document")
            out = Path(folder) / "evidence"
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                run_engine("tesseract", out, pdf=pdf)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
