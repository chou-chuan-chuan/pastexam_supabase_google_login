#!/usr/bin/env python3
"""Verify fidelity against the latest authoritative full sheet.

Older per-glyph photos remain historical provenance only. Use the current
accepted-shape preservation and immutable base-main whole-font diff gate.
"""
from verify_hiragana_master_v2 import verify_sources, verify_fidelity, verify_font_scope


def main():
    verify_sources()
    verify_fidelity()
    verify_font_scope()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
