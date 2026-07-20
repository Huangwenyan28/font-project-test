from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

# Resolve to the repository-level templates/ directory (two levels up from src/font_preview)
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / 'templates'

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml']),
)


def render_template(context: dict) -> str:
    tmpl = env.get_template('preview.html.j2')
    return tmpl.render(**context)
