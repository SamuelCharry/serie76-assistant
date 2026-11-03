"""Safety/state tests with an OCR boundary fake. Real OCR is tested separately."""

import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import importlib.util
if any(importlib.util.find_spec(name) is None for name in ("numpy", "cv2", "pymupdf")):
    raise unittest.SkipTest("Optional OCR tests require requirements-ingest.lock.txt")

import pymupdf

from catalog_ingest.geometry import Token
from catalog_ingest.metadata import (
    clean_technical_notation,
    page_metadata,
    table_footnotes,
)
from catalog_ingest.ocr import InferenceCache, atomic_json
from catalog_ingest.pipeline import Config, process_pdf, verified_result
from catalog_ingest.processing import choose_reading


def word(text, x, y, score=0.999):
    return Token(text, (x - 12, y - 10, x + 12, y + 10), score)


class FakeOCR:
    settings = {"engine": "test-boundary-fake"}
    signature = "test-fake-signature"

    def __init__(self, mode="good"):
        self.cache = SimpleNamespace(hits=0, misses=0)
        self.calls = 0
        self.mode = mode

    def page(self, image):
        self.calls += 1
        tokens = [
            word("EXPLOSIONPROOF - CSA", 400, 80),
            word("24V DC Power - Modulating", 400, 160),
            word("Base Part Number", 200, 290),
            word("Modulating", 500, 220),
            word("Modulating", 700, 220),
            word("Starts per Hour", 850, 220),
            word("Operating", 1000, 220),
            word("Full Load", 1150, 220),
            word("Locked Rotor", 1300, 220),
            word("Motor", 1450, 220),
        ]
        units = [
            ("In-Lbs.", 450),
            ("Nm", 550),
            ("S4%", 700),
            ("Starts", 850),
            ("Sec", 1000),
            ("Amps", 1150),
            ("Amps", 1300),
            ("Watts", 1450),
        ]
        tokens += [
            word(t, x, 340)
            for t, x in units
            if not (self.mode == "unknown_header" and t == "Nm")
        ]
        for i, y in enumerate((400, 460, 520)):
            code = f"768A0{i}-99887766/A"
            if self.mode == "unreadable_identifier" and i == 2:
                code = "768A02-99887766/4"
            tokens.append(word(code, 200, y))
            values = ["790", "90", "40", "450", "3.2", "1.25", "3.75"]
            if self.mode == "conflict" and self.calls == 2 and i == 0:
                values[1] = "91"
            for value, x in zip(values, (450, 550, 700, 850, 1000, 1150, 1300)):
                tokens.append(
                    word(value, x, y, score=0.5 if self.mode == "uncertain" else 0.999)
                )
        tokens += [word("17", 1450, 430), word("38", 1450, 520)]
        if self.mode == "na_first_two":
            tokens = [t for t in tokens if not (t.y in {400, 430, 460} and t.x > 400)]
            tokens.append(word("N/A", 950, 430))
        return tokens

    def recognize(self, images):
        return [("", 0.0)] * len(images)


class PipelineSafetyTests(unittest.TestCase):
    def test_enclosure_and_certification_follow_each_table_heading(self):
        import numpy as np

        first = SimpleNamespace(title_bbox=(0, 200, 100, 220), y_bounds=[250, 400])
        second = SimpleNamespace(title_bbox=(0, 600, 100, 620), y_bounds=[650, 800])
        tokens = [
            word("WEATHERPROOF - CE", 400, 80),
            word("EXPLOSIONPROOF - CSA", 400, 500),
        ]
        metadata = page_metadata(
            tokens,
            [first, second],
            np.zeros((1000, 1000, 3), dtype=np.uint8),
            FakeOCR(),
        )
        self.assertEqual(
            [c["enclosure"] for c in metadata["table_contexts"]],
            ["weatherproof", "explosionproof"],
        )
        self.assertNotIn(
            "CSA", metadata["table_contexts"][0]["certification_header_raw"]
        )
        notes = [
            dict(kind="footnote", bbox=[0, 440, 100, 460], text="* first"),
            dict(kind="footnote", bbox=[0, 840, 100, 860], text="* second"),
        ]
        self.assertEqual(
            table_footnotes(notes, first, [first, second])[0]["text"], "* first"
        )
        self.assertEqual(
            table_footnotes(notes, second, [first, second])[0]["text"], "* second"
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pdf = self.root / "input.pdf"
        self.make_pdf(self.pdf)

    def make_pdf(self, path, pages=1):
        with pymupdf.open() as document:
            for _ in range(pages):
                page = document.new_page(width=960, height=600)
                for y in (370, 490, 550):
                    page.draw_line(
                        (150 / 1.6666666667, y / 1.6666666667),
                        (1550 / 1.6666666667, y / 1.6666666667),
                        color=(0.4, 0.4, 0.4),
                    )
            document.save(path)

    def process(self, ocr=None, config=None):
        return process_pdf(
            self.pdf,
            self.root / "out",
            ocr or FakeOCR(),
            config or Config(dpi=120, keep_images=False),
        )

    def test_valid_output_and_verified_resume(self):
        ocr = FakeOCR()
        folder, result = self.process(ocr)
        self.assertEqual(result["status"], "ready")
        data = json.loads((folder / "catalog.json").read_text())
        self.assertEqual([r["motor_power_w"] for r in data["rows"]], [17, 17, 38])
        self.assertEqual(data["rows"][0]["operating_time_unqualified_s"], 3.2)
        _, resumed = self.process(ocr)
        self.assertTrue(resumed["reused"])
        self.assertEqual(ocr.calls, 1)

    def test_corrupt_export_cannot_be_reused(self):
        folder, result = self.process()
        (folder / "catalog.csv").write_text("corrupted")
        with self.assertRaisesRegex(ValueError, "integrity"):
            self.process()

    def test_unknown_header_quarantines_document(self):
        folder, result = self.process(FakeOCR("unknown_header"))
        self.assertEqual(result["status"], "needs_review")
        self.assertFalse((folder / "catalog.csv").exists())
        self.assertIn(
            "unsupported_or_ambiguous_layout",
            (folder / "review_queue.jsonl").read_text(),
        )

    def test_uncertainty_never_exports_a_valid_catalog(self):
        folder, result = self.process(FakeOCR("uncertain"))
        self.assertEqual(result["status"], "needs_review")
        self.assertFalse((folder / "catalog.json").exists())

    def test_unreadable_last_identifier_is_not_silently_dropped(self):
        folder, result = self.process(FakeOCR("unreadable_identifier"))
        self.assertEqual(result["status"], "needs_review")
        self.assertFalse((folder / "catalog.csv").exists())

    def test_page_and_pixel_limits_apply_before_ocr(self):
        ocr = FakeOCR()
        _, result = self.process(ocr, Config(dpi=120, max_pixels=100))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(ocr.calls, 0)
        other = self.root / "two-pages.pdf"
        self.make_pdf(other, pages=2)
        _, result = process_pdf(
            other, self.root / "other", ocr, Config(dpi=120, max_pages=1)
        )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(ocr.calls, 0)

    def test_identical_duplicates_preserve_each_occurrence(self):
        other = self.root / "two-pages.pdf"
        self.make_pdf(other, pages=2)
        _, result = process_pdf(
            other, self.root / "out", FakeOCR(), Config(dpi=120, keep_images=False)
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual((result["rows"], result["identical_duplicate_rows"]), (6, 3))

    def test_conflicting_same_identity_is_not_merged(self):
        other = self.root / "two-pages.pdf"
        self.make_pdf(other, pages=2)
        folder, result = process_pdf(
            other,
            self.root / "out",
            FakeOCR("conflict"),
            Config(dpi=120, keep_images=False),
        )
        self.assertEqual(result["status"], "needs_review")
        self.assertIn(
            "conflicting_duplicate_identity",
            (folder / "review_queue.jsonl").read_text(),
        )

    def test_na_block_size_is_detected_not_hardcoded_to_four(self):
        folder, result = self.process(FakeOCR("na_first_two"))
        self.assertEqual((result["status"], result["source_na_rows"]), ("ready", 2))
        rows = json.loads((folder / "catalog.json").read_text())["rows"]
        self.assertEqual([r["motor_power_w"] for r in rows], [None, None, 38])

    def test_all_numeric_nulls_have_an_explicit_state(self):
        folder, _ = self.process(FakeOCR("na_first_two"))
        for row in json.loads((folder / "catalog.json").read_text())["rows"]:
            for field, state in row["field_status"].items():
                self.assertEqual(row[field] is None, state != "reported")

    def test_unsafe_manifest_path_is_rejected(self):
        folder, result = self.process()
        result["artifact_sha256"] = {"../outside": "fake"}
        atomic_json(folder / "manifest.json", result)
        with self.assertRaisesRegex(ValueError, "Unsafe artifact"):
            verified_result(
                folder, result["source_sha256"], result["pipeline_signature"]
            )

    def test_cache_checksum_detects_tampering(self):
        cache = InferenceCache(self.root / "cache")
        self.addCleanup(cache.close)
        cache.put("cell", "engine", "image", {"text": "3.2"})
        cache.commit()
        self.assertEqual(cache.get("cell", "engine", "image"), {"text": "3.2"})
        cache.connection.execute("UPDATE inference SET payload=?", ('{"text":"32"}',))
        cache.commit()
        self.assertIsNone(cache.get("cell", "engine", "image"))
        self.assertIsNone(cache.get("cell", "other-engine", "image"))

    def test_atomic_write_preserves_previous_result_on_failure(self):
        path = self.root / "record.json"
        atomic_json(path, {"complete": True})
        with self.assertRaises(TypeError):
            atomic_json(path, object())
        self.assertEqual(json.loads(path.read_text()), {"complete": True})

    def test_technical_cleanup_is_context_limited(self):
        cleaned, changes = clean_technical_notation(
            "IEC 6oo34-1; Ex d lIB T4 Gb; current 3.2 A; code BOO"
        )
        self.assertEqual(
            cleaned, "IEC 60034-1; Ex d IIB T4 Gb; current 3.2 A; code BOO"
        )
        self.assertEqual(len(changes), 2)

    def test_detector_context_can_reject_crop_induced_identifier_changes(self):
        readings = [
            dict(method="page_ocr", text="768A00-99887766/A", confidence=0.99),
            dict(method="cell_original", text="768A00-9988776O/A", confidence=0.98),
            dict(method="cell_contrast", text="768A00-9988776O/A", confidence=0.98),
            dict(method="detected_box", text="768A00-99887766/A", confidence=0.99),
        ]
        value, problem = choose_reading("base_part_number", readings)
        self.assertEqual(value, "768A00-99887766/A")
        self.assertIsNone(problem)

    def test_two_conflicting_strong_detected_regions_require_review(self):
        readings = [
            dict(method=m, text=t, confidence=0.999)
            for m, t in [
                ("page_ocr", "3.2"),
                ("detected_box", "3.2"),
                ("detected_box_scale", "32"),
                ("detected_box", "32"),
            ]
        ]
        self.assertIsNotNone(
            choose_reading("operating_time_unqualified_s", readings)[1]
        )


if __name__ == "__main__":
    unittest.main()
