#!/usr/bin/env python3
"""Negative controls: coverage must reject missing and aliased math symbols."""
import tempfile
from pathlib import Path
import unittest
from fontTools.ttLib import TTFont
from audit_font_coverage import DEFAULT_FONT,audit

class CoverageGuards(unittest.TestCase):
    def changed(self,character,replacement):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'mutated.ttf'
            with TTFont(DEFAULT_FONT,recalcTimestamp=False) as font:
                for table in font['cmap'].tables:
                    if table.isUnicode() and table.format!=14:
                        if replacement is None:table.cmap.pop(ord(character),None)
                        else:table.cmap[ord(character)]=font.getBestCmap()[ord(replacement)]
                font.save(path)
            return audit(path)[0]

    def test_missing_symbol_fails(self):
        result=self.changed('ℏ',None)
        self.assertEqual(result['present_count'],44)
        self.assertTrue(any('U+210F' in error for error in result['failures']))

    def test_alias_to_existing_greek_fails(self):
        result=self.changed('∑','Σ')
        self.assertEqual(result['present_count'],44)
        self.assertTrue(any('U+2211' in error for error in result['failures']))

    def test_release_has_no_failures(self):
        result,_=audit(DEFAULT_FONT)
        self.assertEqual(result['failures'],[])
        self.assertEqual(result['present_count'],45)

if __name__=='__main__':unittest.main()
