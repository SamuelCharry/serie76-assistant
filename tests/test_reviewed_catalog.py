"""Reject silent column inversions, OCR characters, and unreviewed data repair."""
import copy
import tempfile
from pathlib import Path
import unittest

from scripts.extract_reviewed_catalog import (
    TRANSCRIPTION, CORRECTIONS, compile_transcription, read_json, write_json,
    verify_ocr, export, PDF, numeric,
)


class ReviewedCatalogTests(unittest.TestCase):
    def setUp(self):
        self.source = read_json(TRANSCRIPTION)
        self.approvals = read_json(CORRECTIONS)
        self.rows, self.cells = compile_transcription(self.source)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "ocr"
        self.folder.mkdir()
        self.predictions = [dict(source_table=c["source_table"], source_row=c["source_row"],
                                 field=c["field"], raw_text="" if c["status"] == "source_NA" else c["raw_text"])
                            for c in self.cells]
        self.predictions += [dict(source_table="p2_t1", source_row=n, field="data_status", raw_text="N/A")
                             for n in range(1, 5)]
        for correction in self.approvals["corrections"]:
            self.prediction(correction["table"], correction["row"], correction["field"])["raw_text"] = correction["ocr_text"]
        write_json(self.folder / "manifest.json", dict(
            status="ocr_completed_unvalidated", source_sha256=self.source["source_sha256"],
            pages=[dict(page=p) for p in range(1, 5)]))

    def prediction(self, table, row, field):
        return next(c for c in self.predictions
                    if (c["source_table"], c["source_row"], c["field"]) == (table, row, field))

    def verify(self):
        write_json(self.folder / "cells.json", self.predictions)
        return verify_ocr(self.source, self.cells, self.folder, self.approvals)

    def test_only_six_exact_reviewed_changes_are_accepted(self):
        result = self.verify()
        self.assertEqual((result["primary_cells_checked"], result["corrections_applied"]), (941, 6))
        self.assertEqual(result["unreviewed_discrepancies"], 0)

    def test_unit_column_inversion_is_rejected(self):
        self.prediction("p1_t1", 9, "on_off_torque_in_lb")["raw_text"] = "1,100"
        self.prediction("p1_t1", 9, "on_off_torque_nm")["raw_text"] = "9,700"
        with self.assertRaisesRegex(ValueError, "Unreviewed OCR mismatch"):
            self.verify()

    def test_BOO_is_not_silently_converted_to_800(self):
        self.prediction("p4_t1", 7, "on_off_torque_nm")["raw_text"] = "BOO"
        with self.assertRaisesRegex(ValueError, "Unreviewed OCR mismatch"):
            self.verify()
        with self.assertRaises(ValueError):
            numeric("BOO")

    def test_approved_correction_cannot_be_generalized_to_other_punctuation(self):
        self.prediction("p1_t2", 1, "on_off_torque_nm")["raw_text"] = "8.0"
        with self.assertRaisesRegex(ValueError, "Unreviewed OCR mismatch"):
            self.verify()

    def test_missing_cell_is_not_hidden_by_manual_reference(self):
        self.predictions.pop()
        with self.assertRaisesRegex(ValueError, "Missing or extra OCR grid"):
            self.verify()

    def test_four_na_power_cells_are_intentional_not_ffill_omissions(self):
        empty = [r for r in self.rows if r["motor_power_w"] is None]
        self.assertEqual(len(empty), 4)
        self.assertTrue(all(r["source_table"] == "p2_t1" and r["data_status"] == "source_NA" for r in empty))
        for row in self.rows:
            if row["data_status"] == "reported":
                self.assertIsNotNone(row["motor_power_w"])
        first = [r for r in self.rows if r["source_table"] == "p1_t1"]
        self.assertEqual([r["motor_power_w"] for r in first[:6]], [15, 15, 40, 40, 40, 90])

    def test_shared_and_24v_measurements_are_not_fabricated(self):
        shared = next(r for r in self.rows if r["source_table"] == "p2_t1" and r["source_row"] == 5)
        self.assertEqual(shared["shared_torque_nm"], 300)
        self.assertIsNone(shared["on_off_torque_nm"])
        self.assertEqual(shared["field_status"]["on_off_torque_nm"], "not_in_layout")
        single = next(r for r in self.rows if r["base_part_number"] == "761X30-11380000/A")
        self.assertEqual(single["on_off_torque_nm"], 70)
        self.assertIsNone(single["modulating_torque_nm"])
        self.assertEqual(single["fla_unqualified_a"], 5.0)
        self.assertIsNone(single["fla_50hz_a"])

    def test_already_correct_ocr_needs_no_override(self):
        for change in self.approvals["corrections"]:
            self.prediction(change["table"], change["row"], change["field"])["raw_text"] = change["source_text"]
        self.assertEqual(self.verify()["corrections_applied"], 0)

    def test_failed_review_creates_no_export(self):
        self.prediction("p4_t1", 7, "on_off_torque_nm")["raw_text"] = "BOO"
        write_json(self.folder / "cells.json", self.predictions)
        out = Path(self.temp.name) / "export"
        with self.assertRaises(ValueError):
            export(PDF, self.folder, out)
        self.assertFalse(out.exists())

    def test_different_pdf_is_rejected(self):
        wrong = Path(self.temp.name) / "wrong.pdf"
        wrong.write_bytes(b"different source")
        with self.assertRaisesRegex(ValueError, "another PDF"):
            export(wrong, self.folder, Path(self.temp.name) / "out")


if __name__ == "__main__":
    unittest.main()
