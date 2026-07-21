import importlib
import sys
import types
from pathlib import Path

from font_preview import utils


def test_embed_font_base64(tmp_path):
    f = tmp_path / 'a.ttf'
    f.write_bytes(b'abc')
    uri = utils.embed_font_base64(str(f))
    assert uri.startswith('data:font')
    assert 'YWJj' in uri  # base64 for 'abc'


def test_timestamped_output_name(tmp_path):
    f = tmp_path / 'myfont.ttf'
    out = utils.timestamped_output_name(str(f))
    # Should include original filename and end with .html
    assert 'myfont.ttf' in out
    assert out.endswith('.html')


class FakeTTFont:
    """A very small fake TTFont-like object for testing.

    Provides minimal tables via __getitem__ and a getGlyphOrder method.
    """

    def __init__(self, path):
        class _NameTbl:
            def getDebugName(self):
                return 'FakeFont'

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
        return ['.notdef', 'a', 'b']


def test_parse_font(monkeypatch):
    """Test that parse_font extracts metadata and metrics correctly."""
    # Create a fake fonttools.ttLib module and inject into sys.modules
    ft = types.ModuleType('fonttools')
    ttlib = types.ModuleType('fonttools.ttLib')
    ttlib.TTFont = FakeTTFont
    ft.ttLib = ttlib

    monkeypatch.setitem(sys.modules, 'fonttools', ft)
    monkeypatch.setitem(sys.modules, 'fonttools.ttLib', ttlib)

    # Ensure generator is imported after our fake fonttools is in place
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    generator = importlib.import_module('font_preview.generator')

    result = generator.parse_font('/fake/path/font.ttf')

    # Verify the structure
    assert isinstance(result, dict)
    assert 'name' in result
    assert 'metrics' in result
    
    # Verify name extraction
    assert result['name'] == 'FakeFont'
    
    # Verify metrics extraction
    metrics = result['metrics']
    assert metrics['unitsPerEm'] == 1000
    assert metrics['ascender'] == 800
    assert metrics['descender'] == -200
    assert metrics['glyphCount'] == 3


def test_generate_preview_writes_html(monkeypatch, tmp_path):
    # Create a fake fonttools.ttLib module and inject into sys.modules
    ft = types.ModuleType('fonttools')
    ttlib = types.ModuleType('fonttools.ttLib')
    ttlib.TTFont = FakeTTFont
    ft.ttLib = ttlib

    monkeypatch.setitem(sys.modules, 'fonttools', ft)
    monkeypatch.setitem(sys.modules, 'fonttools.ttLib', ttlib)

    # Ensure generator is imported after our fake fonttools is in place
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    generator = importlib.import_module('font_preview.generator')

    f = tmp_path / 'fake.ttf'
    f.write_bytes(b'')
    out = tmp_path / 'out.html'
    out_path = generator.generate_preview(str(f), str(out))

    assert Path(out_path).exists()
    content = Path(out_path).read_text(encoding='utf8')
    assert '@font-face' in content
    assert 'FakeFont' in content
