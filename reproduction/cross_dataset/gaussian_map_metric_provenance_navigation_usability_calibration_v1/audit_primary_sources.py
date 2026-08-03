#!/usr/bin/env python3
from audit_core import primary_sources, write_primary_source_docs
if __name__ == "__main__":
    sources=primary_sources(); write_primary_source_docs(sources)
