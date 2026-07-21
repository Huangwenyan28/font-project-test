"""Pytest fixtures and utilities for font-preview tests."""
import sys
import types
from pathlib import Path

import pytest


class FakeTTFont:
    """A reusable fake TTFont-like object for integration testing.

    Provides minimal tables via __getitem__ and a getGlyphOrder method.
    This class can be used with monkeypatch to inject into sys.modules.
    """

    def __init__(self, path):
        class _NameTbl:
            def getDebugName(self):
                return 'TestFont'

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


@pytest.fixture
def tmp_font(tmp_path):
    """Create a temporary TTF file for testing.

    Returns the path to a dummy TTF file that can be used in tests.
    """
    font_file = tmp_path / 'test_font.ttf'
    # Write minimal TTF-like content (in reality, a TTF has specific binary format,
    # but for testing with mocked fonttools, any content works)
    font_file.write_bytes(b'FONTDATA')
    return str(font_file)


@pytest.fixture
def fake_fonttools(monkeypatch):
    """Inject a fake fonttools module into sys.modules for testing.

    This fixture sets up fonttools.ttLib.TTFont with the FakeTTFont class,
    allowing tests to work without requiring real fonttools imports.

    Returns: tuple of (fonttools_module, ttlib_module) for reference if needed
    """
    ft = types.ModuleType('fonttools')
    ttlib = types.ModuleType('fonttools.ttLib')
    ttlib.TTFont = FakeTTFont
    ft.ttLib = ttlib

    monkeypatch.setitem(sys.modules, 'fonttools', ft)
    monkeypatch.setitem(sys.modules, 'fonttools.ttLib', ttlib)

    return ft, ttlib


@pytest.fixture(autouse=True)
def cleanup_imports():
    """Clean up imported modules between tests to avoid import caching issues.

    This ensures each test can re-import modules with fresh mocks.
    """
    yield
    # After each test, remove font_preview modules so they're reimported fresh
    modules_to_clean = [
        'font_preview.generator',
        'font_preview.cli',
        'font_preview.template',
    ]
    for mod in modules_to_clean:
        if mod in sys.modules:
            del sys.modules[mod]
