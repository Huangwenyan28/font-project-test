from pathlib import Path
from typing import Dict, Any, Optional

from font_preview import utils


def parse_font(font_path: str) -> Dict[str, Any]:
    """Parse basic metadata and metrics from a font file using fonttools.

    Imports fonttools.ttLib.TTFont inside the function so tests can inject
    a fake fonttools module into sys.modules before this function is called.
    Returns a dict with 'name' and 'metrics'.
    """
    # Import locally to allow tests to mock fonttools before import
    try:
        from fonttools.ttLib import TTFont  # type: ignore
    except Exception:
        # Re-raise to make missing dependency visible to caller/tests
        raise

    tt = TTFont(font_path)

    # Extract a human-friendly name from the name table if possible.
    name = None
    try:
        name_table = tt['name']
        if hasattr(name_table, 'getDebugName'):
            # Some test fakes expose getDebugName
            name = name_table.getDebugName()
        else:
            # Try typical name record lookup (family name)
            try:
                n = getattr(name_table, 'getName', lambda *a, **k: None)(1, 3, 1, 0x409)
                if n:
                    # nameRecord objects may expose toStr()/toUnicode()
                    try:
                        name = n.toStr()
                    except Exception:
                        try:
                            name = n.toUnicode()
                        except Exception:
                            name = str(n)
            except Exception:
                # Last-resort: use the first available name in names list
                try:
                    if hasattr(name_table, 'names') and name_table.names:
                        nr = name_table.names[0]
                        try:
                            name = nr.toStr()
                        except Exception:
                            name = str(nr)
                except Exception:
                    name = None
    except Exception:
        name = None

    if not name:
        name = Path(font_path).stem

    # Metrics
    metrics = {
        'unitsPerEm': None,
        'ascender': None,
        'descender': None,
        'glyphCount': None,
    }

    try:
        head = tt['head']
        metrics['unitsPerEm'] = getattr(head, 'unitsPerEm', None)
    except Exception:
        metrics['unitsPerEm'] = None

    try:
        os2 = tt['OS/2'] if 'OS/2' in tt else None
        if os2 is not None:
            metrics['ascender'] = getattr(os2, 'sTypoAscender', None)
            metrics['descender'] = getattr(os2, 'sTypoDescender', None)
    except Exception:
        metrics['ascender'] = metrics['descender'] = None

    try:
        if hasattr(tt, 'getGlyphOrder'):
            glyphs = tt.getGlyphOrder()
            metrics['glyphCount'] = len(glyphs) if glyphs is not None else None
    except Exception:
        metrics['glyphCount'] = None

    return {'name': name, 'metrics': metrics}


def generate_preview(font_path: str, output_path: Optional[str] = None) -> str:
    """Generate a single-file HTML preview for the given font and write it.

    Returns the output path as a string.
    """
    from font_preview.template import render_template

    font_uri = utils.embed_font_base64(font_path)
    meta = parse_font(font_path)

    ctx = {
        'font_name': meta['name'],
        'metrics': meta['metrics'],
        'font_data_uri': font_uri,
        'samples': {
            'english': 'The quick brown fox jumps over the lazy dog.',
            'chinese': '快速的棕色狐狸跳过懒狗。'
        }
    }

    html = render_template(ctx)

    if output_path is None:
        output_path = utils.timestamped_output_name(font_path)

    Path(output_path).write_text(html, encoding='utf8')
    return str(output_path)
