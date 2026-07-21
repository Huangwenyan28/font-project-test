# tests/test_cli.py
import importlib
import sys
import types
from pathlib import Path

from click.testing import CliRunner
from font_preview import cli


def test_help_outputs():
    """Test that --help option displays usage information."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_invokes_generate_preview(monkeypatch, tmp_path):
    """Test that CLI invokes generator when called with font file."""
    called = {}
    def fake_generate(font_path, output_path):
        called['args'] = (font_path, output_path)
    monkeypatch.setattr('font_preview.generator.generate_preview', fake_generate)
    runner = CliRunner()
    font_file = str(tmp_path / 'dummy.ttf')
    (tmp_path / 'dummy.ttf').write_bytes(b'')
    result = runner.invoke(cli.main, [font_file, '-o', str(tmp_path / 'out.html')])
    assert result.exit_code == 0
    assert 'args' in called


class FakeTTFont:
    """A minimal fake TTFont-like object for integration testing."""

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


def test_cli_integration_creates_html(monkeypatch, tmp_path):
    """Integration test: CLI runs and creates HTML with expected markers."""
    # Set up fake fonttools module before importing generator
    ft = types.ModuleType('fonttools')
    ttlib = types.ModuleType('fonttools.ttLib')
    ttlib.TTFont = FakeTTFont
    ft.ttLib = ttlib

    monkeypatch.setitem(sys.modules, 'fonttools', ft)
    monkeypatch.setitem(sys.modules, 'fonttools.ttLib', ttlib)

    # Reload generator module with fake fonttools in place
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    if 'font_preview.cli' in sys.modules:
        del sys.modules['font_preview.cli']

    # Re-import cli after fonttools is mocked
    from font_preview import cli as cli_reloaded

    runner = CliRunner()
    font_file = str(tmp_path / 'test.ttf')
    output_file = str(tmp_path / 'output.html')
    (tmp_path / 'test.ttf').write_bytes(b'')

    result = runner.invoke(cli_reloaded.main, [font_file, '-o', output_file])

    assert result.exit_code == 0, f"CLI failed with: {result.output}"
    
    # Verify output file was created
    assert Path(output_file).exists(), f"Output HTML not created at {output_file}"
    
    # Verify HTML contains expected markers
    html_content = Path(output_file).read_text(encoding='utf8')
    assert '@font-face' in html_content, "HTML missing @font-face rule"
    assert 'TestFont' in html_content, "HTML missing font name"
    assert 'The quick brown fox' in html_content, "HTML missing sample text"
    assert 'data:font' in html_content, "HTML missing embedded font data URI"
