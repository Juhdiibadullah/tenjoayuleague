#!/usr/bin/env python3
"""Mengubah file Apps Script (folder src/) menjadi situs statis (folder dist/) untuk GitHub Pages.
Tidak mengubah kode Anda: hanya menempel include, mengisi ADMIN_PAGE, dan menyisipkan shim.js."""
import re, shutil, sys
from pathlib import Path

SRC, OUT = Path('src'), Path('dist')
INC = re.compile(r"<\?!=\s*include_\('([A-Za-z0-9_]+)'\)\s*\?>")
ADM = re.compile(r"<\?!=\s*ADMIN\s*\?\s*'true'\s*:\s*'false'\s*\?>")
SISA = re.compile(r"<\?[=!]?.*?\?>", re.S)


def baca(nama):
    p = SRC / (nama + '.html')
    if not p.exists():
        sys.exit('ERROR: src/%s.html tidak ditemukan' % nama)
    return p.read_text(encoding='utf-8')


def pastikan(h, baru, setelah):
    """Sisipkan include baru tepat setelah include lain bila belum ada."""
    if "include_('%s')" % baru in h:
        return h
    m = re.search(r"<\?!=\s*include_\('%s'\)\s*\?>" % setelah, h)
    if not m:
        sys.exit("ERROR: baris include_('%s') tidak ditemukan di Index.html" % setelah)
    return h[:m.end()] + "\n<?!= include_('%s') ?>" % baru + h[m.end():]


def proses(nama, admin, wajib):
    h = baca(nama) if wajib else (SRC / (nama + '.html')).read_text(encoding='utf-8')
    if nama == 'Index':
        h = pastikan(h, 'AdminMusim', 'AdminPanel')
        h = pastikan(h, 'JuaraPublik', 'PublikPanel')
    for _ in range(3):
        h = INC.sub(lambda m: baca(m.group(1)), h)
    h, n = ADM.subn('true' if admin else 'false', h)
    if nama == 'Index' and n != 1:
        sys.exit('ERROR: baris "const ADMIN_PAGE = <?!= ADMIN ... ?>" tidak ditemukan di Index.html')
    sisip = '<script src="config.js"></script>\n<script src="shim.js"></script>'
    if '<head>' in h:
        h = h.replace('<head>', '<head>\n' + sisip, 1)
    else:
        h = sisip + '\n' + h
    sisa = SISA.findall(h)
    if sisa:
        pesan = 'Masih ada tag template Apps Script di %s: %s' % (nama, sisa[:3])
        if wajib:
            sys.exit('ERROR: ' + pesan)
        print('PERINGATAN: ' + pesan)
    return h


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    (OUT / 'index.html').write_text(proses('Index', False, True), encoding='utf-8')
    (OUT / 'admin.html').write_text(proses('Index', True, True), encoding='utf-8')
    for nama, keluar in [('Tv', 'tv.html'), ('Cetak', 'cetak.html'), ('Daftar', 'daftar.html')]:
        if (SRC / (nama + '.html')).exists():
            (OUT / keluar).write_text(proses(nama, False, False), encoding='utf-8')
            print('Dibuat:', keluar)
    for f in ['shim.js', 'config.js']:
        shutil.copy(f, OUT / f)
    (OUT / '.nojekyll').write_text('')
    print('Selesai. Isi dist/:', sorted(p.name for p in OUT.iterdir()))


if __name__ == '__main__':
    main()
