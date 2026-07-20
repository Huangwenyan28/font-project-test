from font_preview import utils
from pathlib import Path


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
