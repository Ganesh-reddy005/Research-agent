"""Repository ingestion: fetch a code repository, read it, and profile the project it contains.

A provider (github.py) fetches raw files; the rest is provider-independent, so another source
(GitLab, a zip upload) only needs its own fetch function returning a FetchedRepo."""
