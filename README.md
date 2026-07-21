# Font Preview

CLI tool to generate single-file HTML font previews with embedded fonts and responsive design.

## What is font-preview?

**font-preview** is a command-line tool that takes any TTF or OTF font file and generates a beautiful, responsive HTML preview in a single self-contained file. The preview includes:
- Embedded font data (base64 encoded)
- Sample text in multiple scripts and sizes
- Responsive design that works on all devices
- Complete font information and metrics

Perfect for quickly previewing, sharing, and testing fonts without needing a complex setup.

## Installation

Install the package using pip:

```bash
pip install .
```

For development with editable mode:

```bash
pip install -e .
```

## Quick Start

Generate an HTML preview for a font:

```bash
font-preview path/to/font.ttf -o preview.html
```

If no output path is specified, it defaults to `font.ttf.html`:

```bash
font-preview path/to/font.ttf
```

For more details, see [docs/USAGE.md](docs/USAGE.md).

---

## Development

字体项目 AI Coding 小工具测试仓库。

基于 `copilot_multiagent.sh` 脚本，通过 GitHub Copilot CLI + Superpowers 插件实现有纪律的 AI 辅助开发。

### 使用方式

```bash
# 先装 Copilot CLI
npm install -g @github/copilot

# 写 PRD
# 编辑 docs/PRD.md

# 运行脚本
./copilot_multiagent.sh <功能名>
```

详细说明见 `copilot_multiagent.sh` 使用手册。
