"""Generator module tests for font-preview."""
import importlib
import sys
from pathlib import Path

from font_preview import utils


def test_embed_font_base64(tmp_path):
    """Test that embed_font_base64 creates valid data URIs."""
    f = tmp_path / 'a.ttf'
    f.write_bytes(b'abc')
    uri = utils.embed_font_base64(str(f))
    assert uri.startswith('data:font')
    assert 'YWJj' in uri  # base64 for 'abc'


def test_embed_font_base64_otf(tmp_path):
    """Test that embed_font_base64 handles .otf files with correct MIME type."""
    f = tmp_path / 'font.otf'
    f.write_bytes(b'otf_data')
    uri = utils.embed_font_base64(str(f))
    assert uri.startswith('data:font/otf')
    assert 'base64' in uri


def test_timestamped_output_name(tmp_path):
    """Test that timestamped_output_name generates proper filenames."""
    f = tmp_path / 'myfont.ttf'
    out = utils.timestamped_output_name(str(f))
    # Should include original filename and end with .html
    assert 'myfont.ttf' in out
    assert out.endswith('.html')
    # Should have timestamp pattern
    assert 'T' in out and 'Z' in out


def test_parse_font(fake_fonttools):
    """Test that parse_font extracts metadata and metrics correctly."""
    # fake_fonttools fixture injects mocked fonttools
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    generator = importlib.import_module('font_preview.generator')

    result = generator.parse_font('/fake/path/font.ttf')

    # Verify the structure
    assert isinstance(result, dict)
    assert 'name' in result
    assert 'metrics' in result
    
    # Verify name extraction
    assert result['name'] == 'TestFont'
    
    # Verify metrics extraction
    metrics = result['metrics']
    assert metrics['unitsPerEm'] == 1000
    assert metrics['ascender'] == 800
    assert metrics['descender'] == -200
    assert metrics['glyphCount'] == 4  # ['.notdef', 'a', 'b', 'c']


def test_generate_preview_writes_html(fake_fonttools, tmp_path):
    """Test that generate_preview creates a valid HTML file."""
    # fake_fonttools fixture injects mocked fonttools
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
    assert 'TestFont' in content
    assert 'metrics' in content.lower()


def test_generate_preview_includes_sample_text(fake_fonttools, tmp_path):
    """Test that generated HTML includes sample text in multiple languages."""
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    generator = importlib.import_module('font_preview.generator')

    f = tmp_path / 'test.ttf'
    f.write_bytes(b'fontcontent')
    out = tmp_path / 'sample.html'
    generator.generate_preview(str(f), str(out))

    content = Path(out).read_text(encoding='utf8')
    # Should include English sample
    assert 'quick brown fox' in content.lower()
    # Should include Chinese sample
    assert '快速' in content or 'chinese' in content.lower()


def test_generate_preview_returns_output_path(fake_fonttools, tmp_path):
    """Test that generate_preview returns the output path as a string."""
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    generator = importlib.import_module('font_preview.generator')

    f = tmp_path / 'test.ttf'
    f.write_bytes(b'')
    out = tmp_path / 'result.html'
    result = generator.generate_preview(str(f), str(out))

    assert isinstance(result, str)
    assert result == str(out)
    assert Path(result).exists()
