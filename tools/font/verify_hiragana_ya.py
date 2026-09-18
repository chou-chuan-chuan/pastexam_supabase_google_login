#!/usr/bin/env python3
"""Current master-sheet regression gate; supersedes the historical shape snapshot.

The original revision remains in Git history. Shared v2 checks pin reviewed
source hashes, every small/voiced derivation, all six lower-left yoon anchors,
and the exact whole-font change set against immutable Version 1.024.
"""
from verify_hiragana_master_v2 import verify_sources, verify_derivatives, verify_font_scope


def main():
    verify_sources('や')
    verify_derivatives()
    verify_font_scope()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
