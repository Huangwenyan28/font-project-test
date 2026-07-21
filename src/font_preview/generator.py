from pathlib import Path
from typing import Dict, Any, Optional
from collections import OrderedDict

from font_preview import utils


def _unicode_block_name(cp: int) -> str:
    blocks = [
        (0x0000, 0x007F, 'Basic Latin'),
        (0x0080, 0x00FF, 'Latin-1 Supplement'),
        (0x0100, 0x017F, 'Latin Extended-A'),
        (0x0180, 0x024F, 'Latin Extended-B'),
        (0x0250, 0x02AF, 'IPA Extensions'),
        (0x02B0, 0x02FF, 'Spacing Modifier Letters'),
        (0x0300, 0x036F, 'Combining Diacritical Marks'),
        (0x0370, 0x03FF, 'Greek and Coptic'),
        (0x0400, 0x04FF, 'Cyrillic'),
        (0x0500, 0x052F, 'Cyrillic Supplementary'),
        (0x0590, 0x05FF, 'Hebrew'),
        (0x0600, 0x06FF, 'Arabic'),
        (0x0700, 0x074F, 'Syriac'),
        (0x0900, 0x097F, 'Devanagari'),
        (0x0980, 0x09FF, 'Bengali'),
        (0x0E00, 0x0E7F, 'Thai'),
        (0x0E80, 0x0EFF, 'Lao'),
        (0x0F00, 0x0FFF, 'Tibetan'),
        (0x1000, 0x109F, 'Myanmar'),
        (0x1100, 0x11FF, 'Hangul Jamo'),
        (0x1200, 0x137F, 'Ethiopic'),
        (0x1780, 0x17FF, 'Khmer'),
        (0x1E00, 0x1EFF, 'Latin Extended Additional'),
        (0x1F00, 0x1FFF, 'Greek Extended'),
        (0x2000, 0x206F, 'General Punctuation'),
        (0x2070, 0x209F, 'Superscripts and Subscripts'),
        (0x20A0, 0x20CF, 'Currency Symbols'),
        (0x2100, 0x214F, 'Letterlike Symbols'),
        (0x2150, 0x218F, 'Number Forms'),
        (0x2190, 0x21FF, 'Arrows'),
        (0x2200, 0x22FF, 'Mathematical Operators'),
        (0x2300, 0x23FF, 'Miscellaneous Technical'),
        (0x2460, 0x24FF, 'Enclosed Alphanumerics'),
        (0x2500, 0x257F, 'Box Drawing'),
        (0x2580, 0x259F, 'Block Elements'),
        (0x25A0, 0x25FF, 'Geometric Shapes'),
        (0x2600, 0x26FF, 'Miscellaneous Symbols'),
        (0x2700, 0x27BF, 'Dingbats'),
        (0x2800, 0x28FF, 'Braille Patterns'),
        (0x2E80, 0x2EFF, 'CJK Radicals Supplement'),
        (0x2F00, 0x2FDF, 'Kangxi Radicals'),
        (0x3000, 0x303F, 'CJK Symbols and Punctuation'),
        (0x3040, 0x309F, 'Hiragana'),
        (0x30A0, 0x30FF, 'Katakana'),
        (0x3100, 0x312F, 'Bopomofo'),
        (0x3130, 0x318F, 'Hangul Compatibility Jamo'),
        (0x31A0, 0x31BF, 'Bopomofo Extended'),
        (0x31C0, 0x31EF, 'CJK Strokes'),
        (0x31F0, 0x31FF, 'Katakana Phonetic Extensions'),
        (0x3200, 0x32FF, 'Enclosed CJK Letters and Months'),
        (0x3300, 0x33FF, 'CJK Compatibility'),
        (0x3400, 0x4DBF, 'CJK Unified Ideographs Extension A'),
        (0x4DC0, 0x4DFF, 'Yijing Hexagram Symbols'),
        (0x4E00, 0x9FFF, 'CJK Unified Ideographs'),
        (0xA000, 0xA48F, 'Yi Syllables'),
        (0xAC00, 0xD7AF, 'Hangul Syllables'),
        (0xF900, 0xFAFF, 'CJK Compatibility Ideographs'),
        (0xFB00, 0xFB4F, 'Alphabetic Presentation Forms'),
        (0xFB50, 0xFDFF, 'Arabic Presentation Forms-A'),
        (0xFE00, 0xFE0F, 'Variation Selectors'),
        (0xFE30, 0xFE4F, 'CJK Compatibility Forms'),
        (0xFE50, 0xFE6F, 'Small Form Variants'),
        (0xFE70, 0xFEFF, 'Arabic Presentation Forms-B'),
        (0xFF00, 0xFFEF, 'Halfwidth and Fullwidth Forms'),
        (0x1F000, 0x1F02F, 'Mahjong Tiles'),
        (0x1F030, 0x1F09F, 'Domino Tiles'),
        (0x1F0A0, 0x1F0FF, 'Playing Cards'),
        (0x1F100, 0x1F1FF, 'Enclosed Alphanumeric Supplement'),
        (0x1F200, 0x1F2FF, 'Enclosed Ideographic Supplement'),
        (0x1F300, 0x1F5FF, 'Miscellaneous Symbols and Pictographs'),
        (0x1F600, 0x1F64F, 'Emoticons'),
        (0x1F680, 0x1F6FF, 'Transport and Map Symbols'),
        (0x1F900, 0x1F9FF, 'Supplemental Symbols and Pictographs'),
        (0x20000, 0x2A6DF, 'CJK Unified Ideographs Extension B'),
        (0x2A700, 0x2B73F, 'CJK Unified Ideographs Extension C'),
        (0x2B740, 0x2B81F, 'CJK Unified Ideographs Extension D'),
        (0x2F800, 0x2FA1F, 'CJK Compatibility Ideographs Supplement'),
    ]
    for start, end, name in blocks:
        if start <= cp <= end:
            return name
    return 'Other'


def _get_chars_by_block(chars: list) -> list:
    blocks = OrderedDict()
    for c in chars:
        block = c['block']
        if block not in blocks:
            blocks[block] = []
        if len(blocks[block]) < 200:
            blocks[block].append(c)
    return [{'name': name, 'chars': block_chars} for name, block_chars in blocks.items()]


def parse_font(font_path: str) -> Dict[str, Any]:
    """Parse metadata, metrics, and character set from a font file using fonttools.

    Returns a dict with 'name', 'metrics', 'info', and 'chars'.
    """
    try:
        from fontTools.ttLib import TTFont
    except Exception:
        raise

    tt = TTFont(font_path)

    def _get_name(name_id: int, default: str = None) -> Optional[str]:
        try:
            name_table = tt['name']
            n = getattr(name_table, 'getName', lambda *a, **k: None)(name_id, 3, 1, 0x409)
            if n:
                try:
                    return n.toStr()
                except Exception:
                    try:
                        return n.toUnicode()
                    except Exception:
                        return str(n)
        except Exception:
            pass
        return default

    # Name
    name = None
    try:
        name_table = tt['name']
        if hasattr(name_table, 'getDebugName'):
            name = name_table.getDebugName()
        else:
            try:
                n = getattr(name_table, 'getName', lambda *a, **k: None)(1, 3, 1, 0x409)
                if n:
                    try:
                        name = n.toStr()
                    except Exception:
                        try:
                            name = n.toUnicode()
                        except Exception:
                            name = str(n)
            except Exception:
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
        pass
    try:
        os2 = tt['OS/2'] if 'OS/2' in tt else None
        if os2 is not None:
            metrics['ascender'] = getattr(os2, 'sTypoAscender', None)
            metrics['descender'] = getattr(os2, 'sTypoDescender', None)
    except Exception:
        pass
    try:
        if hasattr(tt, 'getGlyphOrder'):
            glyphs = tt.getGlyphOrder()
            metrics['glyphCount'] = len(glyphs) if glyphs is not None else None
    except Exception:
        pass

    # Full metadata
    info = {
        'familyName': name,
        'style': _get_name(2, 'Regular'),
        'version': _get_name(5),
        'designer': _get_name(9),
        'copyright': _get_name(0),
        'license': _get_name(13),
        'trademark': _get_name(7),
    }

    # Character set from cmap
    chars = []
    try:
        cmap_table = tt.getBestCmap() if hasattr(tt, 'getBestCmap') else None
        if cmap_table is not None:
            for codepoint in sorted(cmap_table.keys()):
                if codepoint < 0x110000:
                    c = chr(codepoint) if 0x20 <= codepoint <= 0x10FFFF and not (0xD800 <= codepoint <= 0xDFFF) else ''
                    chars.append({
                        'codepoint': f'U+{codepoint:04X}',
                        'char': c,
                        'block': _unicode_block_name(codepoint),
                    })
    except Exception:
        pass

    return {'name': name, 'metrics': metrics, 'info': info, 'chars': chars}


def generate_preview(font_path: str, output_path: Optional[str] = None) -> str:
    """Generate a single-file HTML preview for the given font and write it."""
    from font_preview.template import render_template

    font_uri = utils.embed_font_base64(font_path)
    meta = parse_font(font_path)
    chars_by_block = _get_chars_by_block(meta.get('chars', []))

    ctx = {
        'font_name': meta['name'],
        'metrics': meta['metrics'],
        'info': meta.get('info', {}),
        'chars_by_block': chars_by_block,
        'font_data_uri': font_uri,
        'samples': {
            'english': 'The quick brown fox jumps over the lazy dog.',
            'chinese': '快速的棕色狐狸跳过懒狗。',
        },
    }
    html = render_template(ctx)
    if output_path is None:
        output_path = utils.timestamped_output_name(font_path)
    Path(output_path).write_text(html, encoding='utf8')
    return str(output_path)
