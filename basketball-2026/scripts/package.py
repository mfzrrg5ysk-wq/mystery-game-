"""Bundle a genuinely offline single-file game and a source ZIP. No third-party libraries."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
out = root / 'dist'
out.mkdir(exist_ok=True)
html = (root / 'index.html').read_text(encoding='utf-8')
css = (root / 'styles.css').read_text(encoding='utf-8').replace('@charset "UTF-8";', '')
html = html.replace('<link rel="stylesheet" href="styles.css">', '<style>\n' + css + '\n</style>')
for name in ('engine', 'render', 'app'):
    script = (root / 'src' / (name + '.js')).read_text(encoding='utf-8')
    html = html.replace('<script src="src/' + name + '.js"></script>', '<script>\n' + script + '\n</script>')
standalone = out / 'Court-Kings-2026.html'
standalone.write_text(html, encoding='utf-8')
archive = out / 'Court-Kings-2026-Game-and-Code.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(standalone, 'Court-Kings-2026.html')
    for file in sorted(root.rglob('*')):
        if file.is_file() and not any(part in ('dist', '.git', '.qa', 'node_modules', '__pycache__') for part in file.relative_to(root).parts):
            z.write(file, 'source/' + str(file.relative_to(root)))
print(f'Offline game: {standalone} ({standalone.stat().st_size:,} bytes)')
print(f'Game + source: {archive} ({archive.stat().st_size:,} bytes)')
