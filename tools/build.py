"""Build the release files into dist/.

    python tools/build.py <path to StormLib shared library> <tag>

Writes pd2data-<N>x-density.mpq for each density, pd2data.mpq (= 1x), the DLLs,
and manifest.json for the launcher. The MPQs hold data/ as committed: in MPQ mode
the game reads the .bin tables, so each .bin must come from running the game with
-txt after its .txt changed. check_bins() fails the build when one is missing;
it can't tell a stale one.
"""
import ctypes
import hashlib
import json
import os
import shutil
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from mpqx import MPQReader  # noqa: E402

DATA = os.path.join(ROOT, 'data')
DIST = os.path.join(ROOT, 'dist')
EXCEL = os.path.join(DATA, 'global', 'excel')
DLLS = ['BH.dll', 'D2Game.dll', 'D2Game-IdentifiedMagic.dll']
DENSITIES = [1, 2, 3, 5, 10]
# Tables the game reads straight from .txt and never compiles (same set as PD2's own mpq).
TXT_ONLY_TABLES = {'aiparms', 'cubemod', 'cubetype', 'miniskillicons', 'monname',
                   'soundenviron', 'treasureclass', 'weaponclass'}

LEVELS_TXT = r'data\global\excel\Levels.txt'
LEVELS_BIN = r'data\global\excel\levels.bin'
LEVELS_RECORD_SIZE = 544
# Levels fields a density variant multiplies: txt column, offset in a levels.bin record, bin type.
# Byte fields cap at 255; the game would wrap them (v11's 10x turned 60 unique packs into 88).
DENSITY_FIELDS = [('MonDen', 28, '<i'), ('MonDen(N)', 32, '<i'), ('MonDen(H)', 36, '<i'),
                  ('MonUMin', 40, 'B'), ('MonUMin(N)', 41, 'B'), ('MonUMin(H)', 42, 'B'),
                  ('MonUMax', 43, 'B'), ('MonUMax(N)', 44, 'B'), ('MonUMax(H)', 45, 'B')]


def scale(value, bin_type, n):
    return min(value * n, 255) if bin_type == 'B' else value * n


def density_txt(raw, n):
    lines = raw.split(b'\r\n')
    header = lines[0].split(b'\t')
    columns = [(header.index(col.encode()), bin_type) for col, _, bin_type in DENSITY_FIELDS]
    for i, line in enumerate(lines[1:], 1):
        cells = line.split(b'\t')
        for j, bin_type in columns:
            if j < len(cells) and cells[j].strip():
                cells[j] = str(scale(int(cells[j]), bin_type, n)).encode()
        lines[i] = b'\t'.join(cells)
    return b'\r\n'.join(lines)


def density_bin(raw, n):
    out = bytearray(raw)
    count = struct.unpack_from('<I', out)[0]
    assert len(out) == 4 + count * LEVELS_RECORD_SIZE, 'levels.bin record size changed'
    for r in range(count):
        record = 4 + r * LEVELS_RECORD_SIZE
        for _, offset, bin_type in DENSITY_FIELDS:
            value = struct.unpack_from(bin_type, out, record + offset)[0]
            struct.pack_into(bin_type, out, record + offset, scale(value, bin_type, n))
    return bytes(out)


def check_bins():
    # shortcut: a .bin older than its .txt can't be detected without the game's compiler.
    bins = {f[:-4].lower() for f in os.listdir(EXCEL) if f.endswith('.bin')}
    missing = [f for f in sorted(os.listdir(EXCEL))
               if f.endswith('.txt') and f[:-4].lower() not in TXT_ONLY_TABLES | bins]
    if missing:
        sys.exit('No .bin for: ' + ', '.join(missing) + '. Launch the game once with -txt, '
                 'then commit the .bin files it writes to data/global/excel/.')


def read_bytes(path):
    with open(path, 'rb') as fh:
        return fh.read()


def read_data():
    files = {}
    for dirpath, _, names in os.walk(DATA):
        for name in names:
            path = os.path.join(dirpath, name)
            files[os.path.relpath(path, ROOT).replace('/', '\\')] = read_bytes(path)
    return files


def write_mpq(storm, path, files):
    if os.path.exists(path):
        os.remove(path)
    mpq = ctypes.c_void_p()
    # Match PD2's own pd2data.mpq: format v1, 4096 hash slots, imploded files, a listfile.
    name = path if os.name == 'nt' else path.encode()
    if not storm.SFileCreateArchive(name, 0x00100000, 4096, ctypes.byref(mpq)):
        sys.exit(f'SFileCreateArchive failed: {storm.SErrGetLastError()}')
    try:
        for archived, data in sorted(files.items()):
            f = ctypes.c_void_p()
            ok = (storm.SFileCreateFile(mpq, archived.encode(), 0, len(data), 0, 0x100, ctypes.byref(f))
                  and storm.SFileWriteFile(f, data, len(data), 0)
                  and storm.SFileFinishFile(f))
            if not ok:
                sys.exit(f'adding {archived} failed: {storm.SErrGetLastError()}')
    finally:
        closed = storm.SFileCloseArchive(mpq)
    if not closed:
        sys.exit(f'SFileCloseArchive failed: {storm.SErrGetLastError()}')
    reader = MPQReader(path)
    for archived, data in files.items():
        assert reader.read_file(archived) == data, f'{path}: {archived} does not read back'


def load_storm(lib):
    storm = (ctypes.WinDLL if os.name == 'nt' else ctypes.CDLL)(lib)
    path_t = ctypes.c_wchar_p if os.name == 'nt' else ctypes.c_char_p
    handle, dword = ctypes.c_void_p, ctypes.c_uint32
    out_handle = ctypes.POINTER(handle)
    storm.SFileCreateArchive.argtypes = [path_t, dword, dword, out_handle]
    storm.SFileCreateFile.argtypes = [handle, ctypes.c_char_p, ctypes.c_uint64, dword, dword, dword, out_handle]
    storm.SFileWriteFile.argtypes = [handle, ctypes.c_char_p, dword, dword]
    storm.SFileFinishFile.argtypes = [handle]
    storm.SFileCloseArchive.argtypes = [handle]
    for fn in ('SFileCreateArchive', 'SFileCreateFile', 'SFileWriteFile', 'SFileFinishFile', 'SFileCloseArchive'):
        getattr(storm, fn).restype = ctypes.c_bool
    storm.SErrGetLastError.restype = dword
    return storm


def main():
    lib, tag = sys.argv[1], sys.argv[2]
    storm = load_storm(lib)
    shutil.rmtree(DIST, ignore_errors=True)
    os.makedirs(DIST)
    files = read_data()
    for n in DENSITIES:
        variant = dict(files)
        variant[LEVELS_TXT] = density_txt(files[LEVELS_TXT], n)
        variant[LEVELS_BIN] = density_bin(files[LEVELS_BIN], n)
        write_mpq(storm, os.path.join(DIST, f'pd2data-{n}x-density.mpq'), variant)
    shutil.copy(os.path.join(DIST, 'pd2data-1x-density.mpq'), os.path.join(DIST, 'pd2data.mpq'))
    for dll in DLLS:
        shutil.copy(os.path.join(ROOT, dll), DIST)

    repo = os.environ.get('GITHUB_REPOSITORY', 'synpoox/pd2-reawakening')
    manifest = [{'filename': f,
                 'url': f'https://github.com/{repo}/releases/download/{tag}/{f}',
                 'hash': hashlib.sha256(read_bytes(os.path.join(DIST, f))).hexdigest()}
                for f in sorted(os.listdir(DIST))]
    with open(os.path.join(DIST, 'manifest.json'), 'w') as fh:
        json.dump(manifest, fh, indent=2)
    print('\n'.join(f"{m['hash'][:12]}  {m['filename']}" for m in manifest))
    check_bins()  # last, so CI still proves the packing while a bin is missing


if __name__ == '__main__':
    main()
