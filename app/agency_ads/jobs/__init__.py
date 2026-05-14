"""Background jobs queued onto RQ.

Each job is a top-level function so RQ can pickle it cleanly. Avoid
closures and non-importable callables.
"""
