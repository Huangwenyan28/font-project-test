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
    assert 'YWJj' in uri


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
    assert 'myfont.ttf' in out
    assert out.endswith('.html')
    assert 'T' in out and 'Z' in out


def test_parse_font(fake_fonttools):
    """Test that parse_font extracts metadata, metrics, and info correctly."""
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    generator = importlib.import_module('font_preview.generator')

    result = generator.parse_font('/fake/path/font.ttf')

    assert isinstance(result, dict)
    assert 'name' in result
    assert 'metrics' in result
    assert 'info' in result
    assert 'chars' in result

    # Name
    assert result['name'] == 'TestFont'

    # Metrics
    metrics = result['metrics']
    assert metrics['unitsPerEm'] == 1000
    assert metrics['ascender'] == 800
    assert metrics['descender'] == -200
    assert metrics['glyphCount'] == 4

    # Info metadata
    info = result['info']
    assert info['familyName'] == 'TestFont'
    assert info['style'] == 'Regular'
    assert info['version'] == 'Version 1.000'
    assert info['designer'] == 'Test Designer'
    assert 'Copyright' in info['copyright']
    assert info['license'] == 'SIL Open Font License'
    assert info['trademark'] == 'TestFont is a trademark'

    # Characters
    assert len(result['chars']) > 0
    assert any(c['codepoint'] == 'U+0041' for c in result['chars'])
    assert any(c['codepoint'] == 'U+4E2D' for c in result['chars'])


def test_generate_preview_writes_html(fake_fonttools, tmp_path):
    """Test that generate_preview creates a valid HTML file."""
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


def test_generate_preview_includes_all_sections(fake_fonttools, tmp_path):
    """Test that generated HTML includes all required sections."""
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    generator = importlib.import_module('font_preview.generator')

    f = tmp_path / 'test.ttf'
    f.write_bytes(b'fontcontent')
    out = tmp_path / 'sample.html'
    generator.generate_preview(str(f), str(out))

    content = Path(out).read_text(encoding='utf8')
    # Sample text
    assert 'quick brown fox' in content.lower()
    assert '快速' in content or 'chinese' in content.lower()
    # Font info
    assert 'TestFont' in content
    assert '设计师' in content or 'designer' in content.lower()
    # Character set
    assert 'U+0041' in content
    # Font size slider
    assert 'font-size-slider' in content
    # Theme toggle
    assert 'theme-toggle' in content or 'toggleTheme' in content


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


def test_chars_by_block_grouping(fake_fonttools):
    """Test that characters are grouped by Unicode blocks."""
    if 'font_preview.generator' in sys.modules:
        del sys.modules['font_preview.generator']
    generator = importlib.import_module('font_preview.generator')

    result = generator.parse_font('/fake/path/font.ttf')
    chars_by_block = generator._get_chars_by_block(result['chars'])

    assert len(chars_by_block) > 0
    # Should have Basic Latin and CJK blocks
    block_names = [b['name'] for b in chars_by_block]
    assert 'Basic Latin' in block_names
    assert 'CJK Unified Ideographs' in block_names
