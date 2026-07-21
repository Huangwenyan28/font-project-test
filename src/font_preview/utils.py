import base64
from pathlib import Path
from datetime import datetime, timezone


def embed_font_base64(font_path: str) -> str:
    """Read font file and return a data URI with base64-encoded contents.

    The mime type is guessed from the file suffix: .ttf -> font/ttf, .otf -> font/otf,
    otherwise application/octet-stream.
    """
    data = Path(font_path).read_bytes()
    suffix = Path(font_path).suffix.lower()
    if suffix == '.ttf':
        mime = 'font/ttf'
    elif suffix == '.otf':
        mime = 'font/otf'
    else:
        mime = 'application/octet-stream'
    b64 = base64.b64encode(data).decode('ascii')
    return f"data:{mime};base64,{b64}"


def timestamped_output_name(font_path: str) -> str:
    """Return a timestamped output filename for the given font path.

    Example: myfont.ttf -> myfont.ttf.20260720T000000Z.html
    Uses UTC time in format YYYYMMDDTHHMMSSZ.
    """
    p = Path(font_path).name
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return f"{p}.{stamp}.html"
