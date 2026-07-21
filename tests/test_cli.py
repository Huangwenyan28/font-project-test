# tests/test_cli.py
"""CLI integration tests for font-preview."""
import importlib
import sys
from pathlib import Path

from click.testing import CliRunner
from font_preview import cli


def test_help_outputs():
    """Test that --help option displays usage information."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_help_shows_font_path_argument():
    """Test that help text includes the FONT_PATH argument."""
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    assert result.exit_code == 0
    assert "FONT_PATH" in result.output or "font_path" in result.output.lower()


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


def test_output_path_default(monkeypatch, tmp_path):
    """Test that default output path uses .html extension if no -o provided."""
    called = {}
    def fake_generate(font_path, output_path):
        called['output_path'] = output_path
    monkeypatch.setattr('font_preview.generator.generate_preview', fake_generate)
    runner = CliRunner()
    font_file = str(tmp_path / 'dummy.ttf')
    (tmp_path / 'dummy.ttf').write_bytes(b'')
    result = runner.invoke(cli.main, [font_file])
    assert result.exit_code == 0
    assert called['output_path'] == f"{font_file}.html"


def test_cli_integration_creates_html(fake_fonttools, tmp_path):
    """Integration test: CLI runs and creates HTML with expected markers."""
    # fake_fonttools fixture injects mocked fonttools into sys.modules
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


def test_cli_integration_with_custom_output(fake_fonttools, tmp_path):
    """Integration test: CLI creates HTML at specified output path."""
    # fake_fonttools fixture injects mocked fonttools
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    if 'font_preview.cli' in sys.modules:
        del sys.modules['font_preview.cli']

    from font_preview import cli as cli_reloaded

    runner = CliRunner()
    font_file = str(tmp_path / 'myfont.ttf')
    custom_output = str(tmp_path / 'custom_output.html')
    (tmp_path / 'myfont.ttf').write_bytes(b'fontdata')

    result = runner.invoke(cli_reloaded.main, [font_file, '-o', custom_output])

    assert result.exit_code == 0
    assert Path(custom_output).exists()
    html_content = Path(custom_output).read_text(encoding='utf8')
    assert '@font-face' in html_content
    assert 'data:font' in html_content
