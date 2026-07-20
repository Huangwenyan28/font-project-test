# tests/test_cli.py
from click.testing import CliRunner
from font_preview import cli


def test_help_outputs():
    runner = CliRunner()
    result = runner.invoke(cli.main, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_invokes_generate_preview(monkeypatch, tmp_path):
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
