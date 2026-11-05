"""Build the release files into dist/.

    python tools/build.py <path to StormLib shared library> <tag>

Writes pd2data-<N>x-density.mpq for each density, pd2data.mpq (= 1x), the DLLs,
and manifest.json for the launcher. The MPQs hold data/ as committed: in MPQ mode
the game reads the .bin tables, so each .bin must come from running the game with
-txt after its .txt changed. check_bins() fails the build when one is missing or stale.
"""
import ctypes
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from mpqx import MPQReader  # noqa: E402

DATA = os.path.join(ROOT, 'data')
DIST = os.path.join(ROOT, 'dist')
EXCEL = os.path.join(DATA, 'global', 'excel')
DLLS = ['BH.dll', 'D2Game.dll', 'D2Game-IdentifiedMagic.dll']
DENSITIES = [1, 2, 3, 5, 10]
# Tables the game never compiles to .bin (same set as PD2's own mpq).
NO_BIN = {'aiparms', 'cubemod', 'cubetype', 'miniskillicons', 'monname',
          'soundenviron', 'treasureclass', 'weaponclass'}

# Levels columns a density variant multiplies, and where they sit in a levels.bin record.
DENSITY_COLS = ['MonDen', 'MonDen(N)', 'MonDen(H)', 'MonUMin', 'MonUMax',
                'MonUMin(N)', 'MonUMax(N)', 'MonUMin(H)', 'MonUMax(H)']
BYTE_COLS = DENSITY_COLS[3:]
LEVELS_RECORD = 544
INT_OFFSETS = (28, 32, 36)
BYTE_OFFSETS = range(40, 46)


def density_txt(raw, n):
    lines = raw.split(b'\r\n')
    header = lines[0].split(b'\t')
    cols = {header.index(c.encode()): c in BYTE_COLS for c in DENSITY_COLS}
    for i, line in enumerate(lines[1:], 1):
        cells = line.split(b'\t')
        for j, is_byte in cols.items():
            if j < len(cells) and cells[j].strip():
                v = int(cells[j]) * n
                cells[j] = str(min(v, 255) if is_byte else v).encode()
        lines[i] = b'\t'.join(cells)
    return b'\r\n'.join(lines)


def density_bin(raw, n):
    out = bytearray(raw)
    count = struct.unpack_from('<I', out)[0]
    assert len(out) == 4 + count * LEVELS_RECORD, 'levels.bin record size changed'
    for r in range(count):
        base = 4 + r * LEVELS_RECORD
        for o in INT_OFFSETS:
            struct.pack_into('<i', out, base + o, struct.unpack_from('<i', out, base + o)[0] * n)
        for o in BYTE_OFFSETS:
            out[base + o] = min(out[base + o] * n, 255)  # byte field: cap so 10x does not wrap
    return bytes(out)


def git_time(path):
    out = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', path],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return int(out or 0)


def check_bins():
    bins = {f[:-4].lower(): f for f in os.listdir(EXCEL) if f.endswith('.bin')}
    errors = []
    for f in sorted(os.listdir(EXCEL)):
        name = f[:-4].lower()
        if not f.endswith('.txt') or name in NO_BIN:
            continue
        if name not in bins:
            errors.append(f'{f}: no {name}.bin')
        elif git_time(os.path.join(EXCEL, f)) > git_time(os.path.join(EXCEL, bins[name])):
            errors.append(f'{f}: changed after {bins[name]} was last committed')
    if errors:
        sys.exit('Bins missing or stale. Launch the game once with -txt, then commit the '
                 'regenerated .bin files:\n  ' + '\n  '.join(errors))


def read_data():
    files = {}
    for dirpath, _, names in os.walk(DATA):
        for name in names:
            path = os.path.join(dirpath, name)
            files[os.path.relpath(path, ROOT).replace('/', '\\')] = open(path, 'rb').read()
    return files


def write_mpq(storm, path, files):
    if os.path.exists(path):
        os.remove(path)
    mpq = ctypes.c_void_p()
    # Match PD2's own pd2data.mpq: format v1, 4096 hash slots, imploded files, a listfile.
    name = path if os.name == 'nt' else path.encode()
    if not storm.SFileCreateArchive(name, 0x00100000, 4096, ctypes.byref(mpq)):
        sys.exit(f'SFileCreateArchive failed: {storm.SErrGetLastError()}')
    for archived, data in sorted(files.items()):
        f = ctypes.c_void_p()
        ok = (storm.SFileCreateFile(mpq, archived.encode(), 0, len(data), 0, 0x100, ctypes.byref(f))
              and storm.SFileWriteFile(f, data, len(data), 0)
              and storm.SFileFinishFile(f))
        if not ok:
            sys.exit(f'adding {archived} failed: {storm.SErrGetLastError()}')
    storm.SFileCloseArchive(mpq)
    reader = MPQReader(path)
    for archived, data in files.items():
        assert reader.read_file(archived) == data, f'{path}: {archived} does not read back'


def load_storm(lib):
    storm = (ctypes.WinDLL if os.name == 'nt' else ctypes.CDLL)(lib)
    path_t = ctypes.c_wchar_p if os.name == 'nt' else ctypes.c_char_p
    p, u32 = ctypes.c_void_p, ctypes.c_uint32
    storm.SFileCreateArchive.argtypes = [path_t, u32, u32, ctypes.POINTER(p)]
    storm.SFileCreateFile.argtypes = [p, ctypes.c_char_p, ctypes.c_uint64, u32, u32, u32, ctypes.POINTER(p)]
    storm.SFileWriteFile.argtypes = [p, ctypes.c_char_p, u32, u32]
    storm.SFileFinishFile.argtypes = [p]
    storm.SFileCloseArchive.argtypes = [p]
    for fn in ('SFileCreateArchive', 'SFileCreateFile', 'SFileWriteFile', 'SFileFinishFile', 'SFileCloseArchive'):
        getattr(storm, fn).restype = ctypes.c_bool
    storm.SErrGetLastError.restype = u32
    return storm


def main():
    lib, tag = sys.argv[1], sys.argv[2]
    check_bins()
    storm = load_storm(lib)
    shutil.rmtree(DIST, ignore_errors=True)
    os.makedirs(DIST)
    files = read_data()
    txt, bin_ = 'data\\global\\excel\\Levels.txt', 'data\\global\\excel\\levels.bin'
    for n in DENSITIES:
        variant = dict(files, **{txt: density_txt(files[txt], n), bin_: density_bin(files[bin_], n)})
        write_mpq(storm, os.path.join(DIST, f'pd2data-{n}x-density.mpq'), variant)
    shutil.copy(os.path.join(DIST, 'pd2data-1x-density.mpq'), os.path.join(DIST, 'pd2data.mpq'))
    for dll in DLLS:
        shutil.copy(os.path.join(ROOT, dll), DIST)

    repo = os.environ.get('GITHUB_REPOSITORY', 'synpoox/pd2-reawakening')
    manifest = [{'filename': f,
                 'url': f'https://github.com/{repo}/releases/download/{tag}/{f}',
                 'hash': hashlib.sha256(open(os.path.join(DIST, f), 'rb').read()).hexdigest()}
                for f in sorted(os.listdir(DIST))]
    with open(os.path.join(DIST, 'manifest.json'), 'w') as fh:
        json.dump(manifest, fh, indent=2)
    print('\n'.join(f"{m['hash'][:12]}  {m['filename']}" for m in manifest))


if __name__ == '__main__':
    main()
