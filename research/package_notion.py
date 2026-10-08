"""Package research Markdown and figures for manual Notion import."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    root = Path(__file__).resolve().parent
    docs = root / 'docs'
    output = root / 'exports' / 'IMG_HG_Notion_import.zip'
    output.parent.mkdir(exist_ok=True)
    paths = sorted(path for path in docs.rglob('*') if path.is_file())
    if not paths:
        raise SystemExit('No research documents found')
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, path.relative_to(docs))
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise SystemExit('Archive integrity check failed')
    print(f'Created {output} ({len(paths)} files). Notion publication was not performed.')


if __name__ == '__main__':
    main()
