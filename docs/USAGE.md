# font-preview Usage Guide

## Overview

**font-preview** is a CLI tool that generates single-file HTML previews from font files. The tool parses font metadata and creates a responsive HTML document with the font embedded and ready to preview.

## Command Syntax

```
font-preview <FONT_PATH> [OPTIONS]
```

### Arguments

- `FONT_PATH` (required): Path to a TTF or OTF font file. The file must exist.

### Options

- `-o`, `--output TEXT`: Output HTML file path. If not specified, defaults to `<FONT_PATH>.html`
  
  Examples:
  ```bash
  font-preview fonts/myfont.ttf -o my-preview.html
  font-preview fonts/myfont.ttf --output ./previews/myfont.html
  ```

## Usage Examples

### 1. Basic Usage (Default Output)

Generate a preview with the default filename (appends `.html` to the font path):

```bash
font-preview ~/fonts/Arial.ttf
# Creates: ~/fonts/Arial.ttf.html
```

### 2. Specify Custom Output Path

Generate a preview with a custom output filename:

```bash
font-preview ~/fonts/Arial.ttf -o my-preview.html
# Creates: my-preview.html in current directory
```

### 3. Absolute Path with Custom Output

Generate a preview using an absolute path:

```bash
font-preview /usr/share/fonts/truetype/Arial.ttf -o ~/previews/arial.html
# Creates: ~/previews/arial.html
```

### 4. Output in Subdirectory

Generate previews to a specific directory:

```bash
font-preview ~/fonts/NotoSans.ttf -o ./previews/noto-sans.html
# Creates: ./previews/noto-sans.html
```

### 5. Batch Preview Multiple Fonts

Create previews for multiple fonts in a directory:

```bash
for font in fonts/*.ttf; do
  font-preview "$font" -o "previews/$(basename "$font" .ttf).html"
done
```

## Features

### Single-File HTML Output
- **Embedded Font Data**: The font is base64-encoded and embedded directly in the HTML
- **No External Dependencies**: Works completely offline once generated
- **Portable**: Share the single `.html` file with anyone

### Interactive Text Preview
The preview includes sample text showcasing:
- Latin alphabet
- Common symbols and punctuation
- Multiple text sizes (14px, 18px, 24px, 32px, 48px)
- Bold and italic variants (if available in the font)

### Responsive Design
The preview is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones
- All modern browsers (Chrome, Firefox, Safari, Edge)

### CJK and Latin Character Support
- Displays Latin character sets
- Supports Chinese, Japanese, and Korean characters
- Proper rendering of complex scripts and diacritics

## Requirements

- **Python**: 3.12 or higher
- **Dependencies**: 
  - Click (CLI framework)
  - fonttools (Font parsing)
  - Jinja2 (Template rendering)

All dependencies are installed automatically when you run `pip install .` or `pip install -e .`

## Known Limitations

### File Size Considerations

- **Latin Fonts**: Most Latin fonts generate 50KB-200KB HTML files
- **CJK Fonts** (Chinese, Japanese, Korean): Can generate 1MB-10MB+ files due to the large number of glyphs and base64 encoding overhead
  - Consider generating previews for CJK fonts strategically
  - Preview generation may take longer for large fonts

### Supported Output Format

- **HTML output only**: PDF and image exports are not supported
- **No batch processing mode**: Process multiple fonts using shell loops

### Supported Font Formats

- **TTF** (TrueType Font)
- **OTF** (OpenType Font)

## Troubleshooting

### Font File Not Found

```
Error: File does not exist.
```

Ensure the font path is correct and the file exists:

```bash
font-preview /path/to/nonexistent.ttf  # ✗ Error
font-preview ~/Downloads/Arial.ttf      # ✓ Correct
```

### Permission Denied

```
Error: Permission denied
```

Ensure you have read permissions on the font file:

```bash
chmod +r my-font.ttf
font-preview my-font.ttf
```

### Output Directory Doesn't Exist

```
Error: [output directory] does not exist
```

Create the output directory first:

```bash
mkdir -p previews
font-preview fonts/myfont.ttf -o previews/preview.html
```

### HTML File Won't Open or Appears Corrupted

If the generated HTML file won't open or displays incorrectly:
- Ensure the font file was valid and readable
- Try using a different browser
- Check that the output directory wasn't full or out of disk space
- For very large fonts (CJK), the file may take time to load in the browser
