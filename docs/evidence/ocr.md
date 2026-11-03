# OCR validation

The archived validated run passed 941/941 primary checks: 68/68 full codes, 869/869 numeric values, 4/4 source N/A and 5/5 footnote markers; context checks were 272/272. Three variants passed, failure isolation and resume passed, and forbidden reference reads and network attempts were empty.

The 100-page repetition test recorded 175 tables, 1700 rows, 100 source N/A rows, 43.39 seconds and 449396736 peak RSS bytes. This repeats the four source pages 25 times; it is not an accuracy benchmark for heterogeneous documents.

Reproduce offline: `.venv-ingest/Scripts/python.exe scripts/verify_ingestion.py`. For the optional 100-page measurement, first install `psutil==7.2.2` in the isolated verification environment and append `--scale`. Outputs are ignored run artifacts; validated extraction remains in `data/extracted/series76`. Evaluation-only helpers, `data/manual` and `data/reference` are retained; generated historical `data/reviewed/catalog-v1` exports are in the archive. The retained reviewed-catalogue tests read the manual transcription and correction fixtures, not these exports. Production extraction blocks all three reference directories.

[Exact archived summary](data/ocr-summary.json). [Original archive](https://github.com/SamuelCharry/serie76-assistant/tree/archive/pre-cleanup/reports/pipeline/verified).
