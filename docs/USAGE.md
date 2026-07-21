# font-preview Usage Guide

## Overview

**font-preview** is a CLI tool that generates single-file HTML previews from font files. The tool parses font metadata and creates a responsive HTML document with the font embedded and ready to preview.

## Command

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

### Basic Usage (Default Output)

Generate a preview with the default filename (appends `.html` to the font path):

```bash
font-preview ~/fonts/NotoSans.ttf
# Creates: ~/fonts/NotoSans.ttf.html
```

### Specify Custom Output Path

Generate a preview with a custom output filename:

```bash
font-preview ~/fonts/NotoSans.ttf -o preview.html
# Creates: preview.html in current directory
```

### Output in Subdirectory

Generate previews to a specific directory:

```bash
font-preview ~/fonts/NotoSans.ttf -o ./previews/noto-sans.html
# Creates: ./previews/noto-sans.html
```

### Batch Preview Multiple Fonts

Create previews for multiple fonts in a directory:

```bash
for font in fonts/*.ttf; do
  font-preview "$font" -o "previews/$(basename "$font" .ttf).html"
done
```

## Features

### Single Self-Contained File

The generated HTML file includes:
- **Embedded Font Data**: The font is base64-encoded and embedded directly in the HTML
- **No External Dependencies**: Works completely offline once generated
- **Portable**: Share the single `.html` file with anyone

### Responsive Design

The preview is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones
- All modern browsers (Chrome, Firefox, Safari, Edge)

### Sample Text

The preview includes sample text showcasing:
- Latin alphabet
- Common symbols and punctuation
- Multiple text sizes (14px, 18px, 24px, 32px, 48px)
- Bold and italic variants (if available in the font)

### Font Information

The HTML displays:
- Font family name
- Font file size
- Available characters
- Font weight and style information
- Character set and encoding details

## Example Output

The generated HTML file shows:

1. **Font Title**: Name and basic information
2. **Quick Stats**: File size and character count
3. **Size Samples**: Text rendered in different sizes
4. **Character Table**: Detailed view of available glyphs
5. **Metadata**: Font properties and licensing information

## Notes and Limitations

### File Size Considerations

- **Latin Fonts**: Most Latin fonts generate 50KB-200KB HTML files
- **CJK Fonts** (Chinese, Japanese, Korean): Can generate 1MB-10MB+ files due to the large number of glyphs
  - Consider generating previews for CJK fonts strategically
  - Preview generation may take longer for large fonts
  
### Supported Formats

- **TTF** (TrueType Font)
- **OTF** (OpenType Font)

### Best Practices

1. **Preview Before Sharing**: The generated file should work in any browser
2. **Test Offline**: The HTML file works completely offline
3. **Organize by Purpose**: Keep previews in a dedicated directory
4. **Large Fonts**: For very large fonts (>50MB), preview generation may be slow

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

## Environment

- **Python**: 3.12 or higher
- **Dependencies**: 
  - Click (CLI framework)
  - fonttools (Font parsing)
  - Jinja2 (Template rendering)

All dependencies are installed automatically when you run `pip install .`
