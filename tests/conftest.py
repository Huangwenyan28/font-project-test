"""Pytest fixtures and utilities for font-preview tests."""
import sys
import types
from pathlib import Path

import pytest


class FakeTTFont:
    """A reusable fake TTFont-like object for integration testing."""

    def __init__(self, path):
        class FakeNameRecord:
            def __init__(self, text):
                self._text = text
            def toStr(self):
                return self._text
            def toUnicode(self):
                return self._text
            def __str__(self):
                return self._text

        class _NameTbl:
            def getDebugName(self):
                return 'TestFont'
            def getName(self, name_id, platform, encoding, lang):
                names = {
                    0: FakeNameRecord('Copyright 2024 TestFont'),
                    1: FakeNameRecord('TestFont'),
                    2: FakeNameRecord('Regular'),
                    5: FakeNameRecord('Version 1.000'),
                    7: FakeNameRecord('TestFont is a trademark'),
                    9: FakeNameRecord('Test Designer'),
                    13: FakeNameRecord('SIL Open Font License'),
                }
                return names.get(name_id)

        class _Head:
            unitsPerEm = 1000

        class _OS2:
            sTypoAscender = 800
            sTypoDescender = -200

        self._tables = {
            'name': _NameTbl(),
            'head': _Head(),
            'OS/2': _OS2(),
        }

    def __getitem__(self, key):
        return self._tables[key]

    def __contains__(self, key):
        return key in self._tables

    def getGlyphOrder(self):
        return ['.notdef', 'a', 'b', 'c']

    def getBestCmap(self):
        return {
            0x0041: 'a', 0x0042: 'b', 0x0043: 'c',
            0x0061: 'a', 0x0062: 'b', 0x0063: 'c',
            0x0030: 'zero', 0x002E: 'period', 0x002C: 'comma', 0x0020: 'space',
            0x4E2D: 'zhong', 0x56FD: 'guo',
        }


def _inject_fake_fonttools(monkeypatch):
    """Inject fake fonttools module (both lowercase and capital T variants)."""
    for mod_name in ('fonttools', 'fontTools'):
        ft = types.ModuleType(mod_name)
        ttlib = types.ModuleType(mod_name + '.ttLib')
        ttlib.TTFont = FakeTTFont
        ft.ttLib = ttlib
        monkeypatch.setitem(sys.modules, mod_name, ft)
        monkeypatch.setitem(sys.modules, mod_name + '.ttLib', ttlib)


@pytest.fixture
def tmp_font(tmp_path):
    font_file = tmp_path / 'test_font.ttf'
    font_file.write_bytes(b'FONTDATA')
    return str(font_file)


@pytest.fixture
def fake_fonttools(monkeypatch):
    _inject_fake_fonttools(monkeypatch)
    return None


@pytest.fixture(autouse=True)
def cleanup_imports():
    yield
    modules_to_clean = [
        'font_preview.generator',
        'font_preview.cli',
        'font_preview.template',
    ]
    for mod in modules_to_clean:
        if mod in sys.modules:
            del sys.modules[mod]
