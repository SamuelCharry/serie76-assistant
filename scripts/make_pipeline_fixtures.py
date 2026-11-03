"""Generate independent OCR integration fixtures, never production extraction inputs."""

from pathlib import Path
import json

import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def centered(page, text, x, y, size=9):
    width = pymupdf.get_text_length(text, fontsize=size, fontname="helv")
    page.insert_text((x - width / 2, y), text, fontsize=size, fontname="helv")


def synthetic(path: Path, shift=0):
    """New identifiers, genuine fractional seconds/amperes, new power values and three rows."""
    doc = pymupdf.open()
    p = doc.new_page(width=842 + shift, height=440 + shift)
    xs = [285, 345, 405, 465, 525, 585, 650, 725]
    p.insert_text((45 + shift, 55 + shift), "EXPLOSIONPROOF - CSA", fontsize=14)
    p.insert_text((55 + shift, 100 + shift), "24V DC Power - Modulating", fontsize=12)
    p.insert_text((50 + shift, 155 + shift), "Base Part Number", fontsize=9)
    headers = [
        ("Modulating", 315, 125),
        ("Output Torque", 315, 145),
        ("Modulating", 405, 125),
        ("Duty Cycle", 405, 145),
        ("Starts per", 465, 125),
        ("Hour", 465, 145),
        ("Operating", 525, 125),
        ("Speed", 525, 145),
        ("Full Load", 585, 125),
        ("Current (FLA)", 585, 145),
        ("Locked Rotor", 650, 125),
        ("Current (LRA)", 650, 145),
        ("Motor", 725, 125),
        ("Power", 725, 145),
    ]
    for text, x, y in headers:
        centered(p, text, x + shift, y + shift, 8)
    for text, x in zip(
        ["In-Lbs.", "Nm", "S4%", "Starts", "Sec", "Amps", "Amps", "Watts"], xs
    ):
        centered(p, text, x + shift, 180 + shift, 9)
    p.draw_line(
        (45 + shift, 110 + shift), (760 + shift, 110 + shift), color=(0.55, 0.55, 0.55)
    )
    p.draw_line(
        (45 + shift, 192 + shift), (760 + shift, 192 + shift), color=(0.55, 0.55, 0.55)
    )
    rows = [
        ("768Z99-99999999/A", ["810", "91", "37", "450", "3.2", "1.25", "3.75"]),
        ("768Z98-99999998/A", ["1,250", "141", "42", "630", "7.5", "2.5", "4.25"]),
        ("768Z97-99999997/A", ["2,020", "228", "55", "840", "12.5", "3.5", "5.25"]),
    ]
    for i, (code, values) in enumerate(rows):
        y = 210 + 35 * i + shift
        p.insert_text((50 + shift, y), code, fontsize=9)
        for value, x in zip(values, xs):
            centered(p, value, x + shift, y, 10)
    # Two rows share 17 W; the third is a new 38 W group.
    for y in (262, 297):
        p.draw_line(
            (45 + shift, y + shift), (760 + shift, y + shift), color=(0.55, 0.55, 0.55)
        )
    centered(p, "17", 725 + shift, 228 + shift, 10)
    centered(p, "38", 725 + shift, 280 + shift, 10)
    p.insert_text((45 + shift, 330 + shift), "NOTES", fontsize=10)
    p.insert_text(
        (45 + shift, 350 + shift),
        "1. Full load current (FLA) @ Max. rated load",
        fontsize=9,
    )
    doc.save(path)
    doc.close()
    return [
        dict(
            base_part_number=code,
            modulating_torque_in_lb=int(v[0].replace(",", "")),
            modulating_torque_nm=int(v[1]),
            modulating_duty_s4_percent=int(v[2]),
            starts_per_hour=int(v[3]),
            operating_time_unqualified_s=float(v[4]),
            fla_unqualified_a=float(v[5]),
            lra_unqualified_a=float(v[6]),
            motor_power_w=17 if i < 2 else 38,
        )
        for i, (code, v) in enumerate(rows)
    ]


def main():
    out = ROOT / ".cache/pipeline-fixtures"
    out.mkdir(parents=True, exist_ok=True)
    expected = synthetic(out / "unseen-values.pdf")
    synthetic(out / "unseen-shifted.pdf", shift=32)
    (out / "unseen-expected.json").write_text(
        json.dumps(expected, indent=2), encoding="utf-8"
    )
    with pymupdf.open(ROOT / "data/raw/series_76_electric_data.pdf") as source:
        reverse = pymupdf.open()
        for p in (3, 1, 0, 2):
            reverse.insert_pdf(source, from_page=p, to_page=p)
        reverse.save(out / "reordered-pages.pdf")
        reverse.close()
        scale = pymupdf.open()
        for i in range(100):
            scale.insert_pdf(source, from_page=i % len(source), to_page=i % len(source))
        scale.save(out / "hundred-pages.pdf")
        scale.close()
    unsupported = pymupdf.open()
    p = unsupported.new_page()
    p.insert_text((40, 60), "Unknown Measurement Table", fontsize=14)
    unsupported.save(out / "unsupported.pdf")
    unsupported.close()
    (out / "broken.pdf").write_bytes(b"This is not a PDF")
    print(out)


if __name__ == "__main__":
    main()
