"""scanner.scripts — standalone calibration / utility CLIs.

These are NOT part of the regular scanner CLI subcommand surface. They are
one-shot diagnostics invoked directly via ``python -m scanner.scripts.<name>``
and write results to ``scanner/output/`` for traceability.

Plan 02-08 introduces the package with one entry: ``calibrate_opus_bbox``
which probes the Opus 4.7 vision pipeline to determine which coordinate
space its returned bboxes live in.
"""
