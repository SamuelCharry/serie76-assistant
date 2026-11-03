"""Pinned local PP-OCR adapter with checksummed content-addressed inference caches."""

from __future__ import annotations

import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import tempfile
import sqlite3

import cv2
import numpy as np

from .geometry import Token


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(
                value,
                stream,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            )
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class InferenceCache:
    """One transactional disk cache, rather than millions of tiny cell files."""

    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(root / "inference.sqlite3", timeout=30)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS inference (kind TEXT, signature TEXT, content TEXT, payload TEXT, checksum TEXT, PRIMARY KEY(kind,signature,content))"
        )
        self.hits = 0
        self.misses = 0

    def get(self, kind: str, signature: str, content: str):
        row = self.connection.execute(
            "SELECT payload,checksum FROM inference WHERE kind=? AND signature=? AND content=?",
            (kind, signature, content),
        ).fetchone()
        if row:
            try:
                if sha256_bytes(row[0].encode()) == row[1]:
                    payload = json.loads(row[0])
                    self.hits += 1
                    return payload
            except (ValueError, TypeError):
                pass
        self.misses += 1
        return None

    def put(self, kind: str, signature: str, content: str, payload):
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
        self.connection.execute(
            "INSERT OR REPLACE INTO inference VALUES (?,?,?,?,?)",
            (kind, signature, content, encoded, sha256_bytes(encoded.encode())),
        )

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.commit()
        self.connection.close()


class LocalOCR:
    def __init__(self, cache: Path, models: Path, threads: int = 2):
        if version("rapidocr") != "3.10.0":
            raise RuntimeError(
                "The batched recognizer adapter is tested with rapidocr==3.10.0"
            )
        from rapidocr import RapidOCR, OCRVersion, ModelType, LangDet, LangRec

        self.settings = dict(
            engine="rapidocr",
            package=version("rapidocr"),
            onnxruntime=version("onnxruntime"),
            model="PP-OCRv5-mobile-English",
            opencv=cv2.__version__,
            numpy=np.__version__,
            orientation=False,
            max_side=3500,
            threads=threads,
            page_batch=6,
            recognition_batch=16,
        )
        self.signature = sha256_bytes(
            json.dumps(self.settings, sort_keys=True).encode()
            + Path(__file__).read_bytes()
        )
        self.cache = InferenceCache(cache)
        self.engine = RapidOCR(
            params={
                "Global.model_root_dir": str(models),
                "Global.use_cls": False,
                "Global.max_side_len": 3500,
                "Det.limit_side_len": 3500,
                "Det.limit_type": "max",
                "Det.ocr_version": OCRVersion.PPOCRV5,
                "Det.model_type": ModelType.MOBILE,
                "Rec.ocr_version": OCRVersion.PPOCRV5,
                "Rec.model_type": ModelType.MOBILE,
                "Det.lang_type": LangDet.CH,
                "Rec.lang_type": LangRec.EN,
                "Rec.rec_batch_num": 6,
                "EngineConfig.onnxruntime.intra_op_num_threads": threads,
                "EngineConfig.onnxruntime.inter_op_num_threads": threads,
            }
        )

    def _read_cache(self, kind: str, content_hash: str):
        return self.cache.get(kind, self.signature, content_hash)

    def _write_cache(self, kind: str, content_hash: str, payload):
        self.cache.put(kind, self.signature, content_hash, payload)

    def page(self, image: np.ndarray) -> list[Token]:
        key = sha256_bytes(image.shape.__repr__().encode() + image.tobytes())
        payload = self._read_cache("pages", key)
        if payload is None:
            if self.engine.text_rec is not None:
                self.engine.text_rec.rec_batch_num = 6
            result = self.engine(image)
            payload = []
            if result.txts is not None:
                for box, text, score in zip(result.boxes, result.txts, result.scores):
                    xs, ys = zip(*box)
                    payload.append(
                        dict(
                            text=str(text),
                            bbox=[
                                float(min(xs)),
                                float(min(ys)),
                                float(max(xs)),
                                float(max(ys)),
                            ],
                            score=float(score),
                        )
                    )
            self._write_cache("pages", key, payload)
            self.cache.commit()
        return [Token(p["text"], tuple(p["bbox"]), p["score"]) for p in payload]

    def recognize(self, images: list[np.ndarray]) -> list[tuple[str, float]]:
        """Bounded line recognition batches. No detector and no orientation rotation."""
        answers = [None] * len(images)
        pending = []
        for i, image in enumerate(images):
            key = sha256_bytes(image.shape.__repr__().encode() + image.tobytes())
            cached = self._read_cache("recognition", key)
            if cached is not None:
                answers[i] = (cached["text"], cached["score"])
            else:
                pending.append((i, key, image))
        if pending:
            # Encapsulate this version-pinned stage API here; geometry/export never depend on it.
            from rapidocr.ch_ppocr_rec.typings import TextRecInput

            recognizer = self.engine._load_rec_model()
            recognizer.rec_batch_num = 16
            for start in range(0, len(pending), 32):
                batch = pending[start : start + 32]
                rgb = [cv2.cvtColor(im, cv2.COLOR_BGR2RGB) for _, _, im in batch]
                result = recognizer(TextRecInput(img=rgb))
                for (index, key, _), text, score in zip(
                    batch, result.txts, result.scores
                ):
                    answers[index] = (str(text), float(score))
                    self._write_cache(
                        "recognition", key, dict(text=str(text), score=float(score))
                    )
                self.cache.commit()
        return answers

    def close(self):
        self.cache.close()
