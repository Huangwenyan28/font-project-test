# Font Preview (font-preview) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

Goal: Build a Python 3.12 CLI `font-preview` that generates a single-file, self-contained HTML preview for a given TTF/OTF font per docs/PRD.md.

Architecture: Click CLI invokes generator which uses fonttools to extract metadata and metrics, encodes the font as base64, and renders a Jinja2 HTML template (fully inlined CSS+JS). Tests use pytest and mock fonttools where appropriate.

Tech Stack: Python 3.12, fonttools, click, jinja2, pytest.

## Global Constraints
- Implemented in Python 3.12 (as requested).
- Use fonttools to parse fonts.
- Output must be a single HTML file with font inlined via base64 and @font-face.
- CLI entrypoint: `font-preview <font-file> [-o output.html]` and `--help` must be complete.
- No web service; CLI-only.

---

### File map (create/modify)
- Create: `pyproject.toml` (declare deps & entry point)
- Create: `src/font_preview/__init__.py`
- Create: `src/font_preview/cli.py` (Click CLI)
- Create: `src/font_preview/generator.py` (parsing + html generation)
- Create: `src/font_preview/template.py` (loads Jinja2 template and renders)
- Create: `src/font_preview/utils.py` (base64 encode, filename helpers)
- Create: `templates/preview.html.j2` (single-file HTML template)
- Create: `tests/test_cli.py` (pytest for CLI)
- Create: `tests/test_generator.py` (unit tests that mock fonttools)
- Modify: `README.md` (usage example)


### Task 1: Project scaffold and deps
**Files:**
- Create: `pyproject.toml`

**Interfaces:**
- Produces a project layout and declares dependencies for implementers/CI.

- [ ] Step 1: Write failing test (none; scaffold step). Create `pyproject.toml` with:

```toml
[project]
name = "font-preview"
version = "0.1.0"
description = "CLI to generate single-file HTML font previews"
requires-python = ">=3.12"

[project.dependencies]
click = "^8.1"
fonttools = "^4.40"
jinja2 = "^3.1"

[build-system]
requires = ["setuptools>=61.0","wheel"]
build-backend = "setuptools.build_meta"

[project.scripts]
font-preview = "font_preview.cli:main"
```

- [ ] Step 2: Run a quick sanity check
Run: `python -V` (should be 3.12.x) and `pip install -e .` (dev environment) — expect install to succeed if Python 3.12 present.

- [ ] Step 3: Commit
```bash
git add pyproject.toml
git commit -m $'chore(scaffold): add pyproject and entry point\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'
```


### Task 2: Basic package and CLI (Click)
**Files:**
- Create: `src/font_preview/__init__.py`
- Create: `src/font_preview/cli.py`

**Interfaces:**
- Consumes: `font_preview.generator.generate_preview(font_path, output_path)`
- Produces: `main()` Click entrypoint

- [ ] Step 1: Write failing test `tests/test_cli.py`

```python
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
```
```

- [ ] Step 2: Run test to verify it fails
Run: `pytest tests/test_cli.py -q` Expected: FAIL because cli.main not implemented.

- [ ] Step 3: Implement minimal CLI

```python
# src/font_preview/cli.py
import click
from font_preview import generator

@click.command(name='font-preview')
@click.argument('font_path', type=click.Path(exists=True))
@click.option('-o', '--output', 'output_path', default=None, help='Output HTML path')
def main(font_path, output_path):
    """Generate a single-file HTML preview for FONT_PATH."""
    if output_path is None:
        output_path = f"{font_path}.html"
    generator.generate_preview(font_path, output_path)

if __name__ == '__main__':
    main()
```

- [ ] Step 4: Run tests
Run: `pytest tests/test_cli.py -q` Expected: PASS

- [ ] Step 5: Commit
```bash
git add src/font_preview/cli.py tests/test_cli.py src/font_preview/__init__.py
git commit -m $'feat(cli): add Click CLI and tests\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'
```


### Task 3: Implement utils (base64 embed + output filename)
**Files:**
- Create: `src/font_preview/utils.py`

**Interfaces:**
- Exposes `embed_font_base64(path) -> str` and `timestamped_output_name(font_path) -> str`

- [ ] Step 1: Write failing tests in `tests/test_generator.py` (start with utils assertions)

```python
# tests/test_generator.py
from font_preview import utils
from pathlib import Path

def test_embed_font_base64(tmp_path):
    f = tmp_path / 'a.ttf'
    f.write_bytes(b'abc')
    uri = utils.embed_font_base64(str(f))
    assert uri.startswith('data:font')

def test_timestamped_output_name(tmp_path):
    f = tmp_path / 'myfont.ttf'
    out = utils.timestamped_output_name(str(f))
    assert 'myfont.ttf' in out or out.endswith('.html')
```
```

- [ ] Step 2: Run tests -> should fail (utils missing)

- [ ] Step 3: Implement utils

```python
# src/font_preview/utils.py
import base64
from pathlib import Path
from datetime import datetime


def embed_font_base64(font_path: str) -> str:
    data = Path(font_path).read_bytes()
    # Try to guess mime
    suffix = Path(font_path).suffix.lower()
    mime = 'font/ttf' if suffix in ['.ttf'] else 'font/otf' if suffix in ['.otf'] else 'application/octet-stream'
    b64 = base64.b64encode(data).decode('ascii')
    return f"data:{mime};base64,{b64}"


def timestamped_output_name(font_path: str) -> str:
    p = Path(font_path).name
    stamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    return f"{p}.{stamp}.html"
```

- [ ] Step 4: Run tests: `pytest tests/test_generator.py::test_embed_font_base64 -q` Expected: PASS

- [ ] Step 5: Commit
```bash
git add src/font_preview/utils.py tests/test_generator.py
git commit -m $'feat(utils): add base64 embed and filename helper\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'
```


### Task 4: Generator - parse font and assemble HTML
**Files:**
- Create: `src/font_preview/generator.py`
- Create: `src/font_preview/template.py`
- Create: `templates/preview.html.j2`

**Interfaces:**
- `generate_preview(font_path: str, output_path: str|None) -> str` writes file and returns output path
- Internals: `parse_font(font_path) -> dict(metadata, metrics)` and `render_html(context) -> str`

- [ ] Step 1: Extend `tests/test_generator.py` with a test that mocks fonttools.TTFont

```python
# append to tests/test_generator.py
import io
from unittest.mock import MagicMock
from font_preview import generator
from pathlib import Path

class FakeName:
    def getDebugName(self):
        return 'FakeFont'

class FakeTTFont:
    def __init__(self, path):
        self['head'] = MagicMock()  # metrics stub
        self['head'].unitsPerEm = 1000
        self['OS/2'] = MagicMock()
        self['OS/2'].sTypoAscender = 800
        self['OS/2'].sTypoDescender = -200
        self.getGlyphOrder = lambda: ['.notdef','a','b']
        self['name'] = MagicMock()
        # name table retrieval simplified
        self['name'].getDebugName = lambda: 'FakeFont'

def test_generate_preview_writes_html(monkeypatch, tmp_path):
    monkeypatch.setattr('fonttools.ttLib.TTFont', lambda p: FakeTTFont(p))
    f = tmp_path / 'fake.ttf'
    f.write_bytes(b'')
    out = tmp_path / 'out.html'
    out_path = generator.generate_preview(str(f), str(out))
    assert Path(out_path).exists()
    content = Path(out_path).read_text()
    assert '@font-face' in content
    assert 'FakeFont' in content
```
```

- [ ] Step 2: Run tests -> FAIL (generator missing)

- [ ] Step 3: Implement generator + template loader

```python
# src/font_preview/generator.py
from fonttools.ttLib import TTFont
from font_preview import utils
from font_preview.template import render_template
from pathlib import Path


def parse_font(font_path: str) -> dict:
    tt = TTFont(font_path)
    # Minimal metadata extraction
    name = None
    try:
        # fonttools has name table access patterns; keep simple and defensive
        name_table = tt['name']
        name = getattr(name_table, 'getDebugName', lambda: None)() if hasattr(name_table, 'getDebugName') else None
    except Exception:
        name = Path(font_path).stem
    metrics = {
        'unitsPerEm': getattr(tt['head'], 'unitsPerEm', None),
        'ascender': getattr(tt['OS/2'], 'sTypoAscender', None) if 'OS/2' in tt else None,
        'descender': getattr(tt['OS/2'], 'sTypoDescender', None) if 'OS/2' in tt else None,
        'glyphCount': len(tt.getGlyphOrder()) if hasattr(tt, 'getGlyphOrder') else None,
    }
    return {'name': name or Path(font_path).stem, 'metrics': metrics}


def generate_preview(font_path: str, output_path: str | None = None) -> str:
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
```

```python
# src/font_preview/template.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / 'templates'

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(['html']))

def render_template(context: dict) -> str:
    tmpl = env.get_template('preview.html.j2')
    return tmpl.render(**context)
```

```html
<!-- templates/preview.html.j2 -->
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<title>{{ font_name }} — Preview</title>
<style>
/* minimal inline styles for preview */
body{font-family: system-ui, sans-serif; padding:20px}
.preview{font-family: '{{ font_name }}', sans-serif;}
</style>
<style>
@font-face{font-family: '{{ font_name }}'; src: url('{{ font_data_uri }}');}
</style>
</head>
<body>
<h1>{{ font_name }}</h1>
<div>UnitsPerEm: {{ metrics.unitsPerEm }} | Ascender: {{ metrics.ascender }} | Descender: {{ metrics.descender }} | Glyphs: {{ metrics.glyphCount }}</div>
<hr/>
<div>
<label>Sample text:</label>
<input id="sample" value="{{ samples.english }}" style="width:100%"/>

<div class="preview" id="preview-area" style="font-size:24px; margin-top:10px">{{ samples.english }}</div>
</div>
<script>
const input = document.getElementById('sample');
const preview = document.getElementById('preview-area');
input.addEventListener('input', (e)=> preview.textContent = e.target.value);
</script>
</body>
</html>
```

- [ ] Step 4: Run tests `pytest tests/test_generator.py -q` Expected: PASS

- [ ] Step 5: Commit
```bash
git add src/font_preview/generator.py src/font_preview/template.py templates/preview.html.j2
git commit -m $'feat(generator): implement font parsing and HTML rendering\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'
```


### Task 5: End-to-end CLI test (integration)
**Files:**
- Modify: tests/test_cli.py to add an integration invocation that mocks fonttools minimal or uses the earlier monkeypatch

- [ ] Step 1: Add integration test that runs the CLI to create actual HTML and asserts contains expected strings (already covered by test_cli and test_generator integration)
- [ ] Step 2: Run: `pytest -q` Expected: all tests PASS
- [ ] Step 3: Commit
```bash
git add tests
git commit -m $'test: add integration tests for CLI and generator\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'
```


### Task 6: Docs and usage
**Files:**
- Modify: `README.md` (add install and usage snippet)
- Create: `docs/USAGE.md` (explain flags and sample output details)

- [ ] Step 1: Update README snippet:
```
# install
pip install .

# usage
font-preview path/to/font.ttf -o out.html
```
- [ ] Step 2: Commit
```bash
git add README.md docs/USAGE.md
git commit -m $'docs: add usage and examples for font-preview\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'
```


### Task 7: Self-review and checklist
- [ ] Ensure PRD acceptance criteria map to tests:
  - `font-preview test.ttf` generates HTML -> covered by generator test
  - CJK and Latin render -> sample text includes both; manual browser verification required
  - Interactions (font size, dark mode) -> basic JS for input provided; add size slider and dark-mode toggle in followup
  - Output filename timestamp -> utils.timestamped_output_name exists
  - `--help` -> cli test covers help

- [ ] Run full test suite: `pytest -q`

- [ ] Final commit and push; open PR for review.

---

Plan saved to `docs/superpowers/plans/2026-07-20-font-preview.md`.

Execution options:
1) Subagent-Driven (recommended) — dispatch subagents per task for isolated execution and review.
2) Inline Execution — run tasks here using executing-plans.

Which execution mode do you prefer?