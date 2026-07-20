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
