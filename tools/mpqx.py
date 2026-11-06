"""MPQ extractor with file decryption support (extends mpyq concepts)."""
import bz2
import os
import struct
import sys
import zlib

from blast import explode

def pk_explode(data):
    return explode(bytes(data))

MPQ_FILE_IMPLODE     = 0x00000100
MPQ_FILE_COMPRESS    = 0x00000200
MPQ_FILE_ENCRYPTED   = 0x00010000
MPQ_FILE_FIX_KEY     = 0x00020000
MPQ_FILE_SINGLE_UNIT = 0x01000000
MPQ_FILE_SECTOR_CRC  = 0x04000000
MPQ_FILE_EXISTS      = 0x80000000


def prepare_encryption_table():
    seed = 0x00100001
    table = {}
    for i in range(256):
        index = i
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp1 = (seed & 0xFFFF) << 0x10
            seed = (seed * 125 + 3) % 0x2AAAAB
            temp2 = seed & 0xFFFF
            table[index] = temp1 | temp2
            index += 0x100
    return table

CRYPT = prepare_encryption_table()

HASH_TYPES = {'TABLE_OFFSET': 0, 'HASH_A': 1, 'HASH_B': 2, 'TABLE': 3}

def mpq_hash(string, hash_type):
    seed1 = 0x7FED7FED
    seed2 = 0xEEEEEEEE
    base = HASH_TYPES[hash_type] << 8
    for ch in string.upper():
        c = ord(ch)
        value = CRYPT[base + c]
        seed1 = (value ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed2 = (c + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1

def mpq_decrypt(data, key):
    seed1 = key
    seed2 = 0xEEEEEEEE
    n = len(data) // 4
    out = bytearray()
    for i in range(n):
        seed2 = (seed2 + CRYPT[0x400 + (seed1 & 0xFF)]) & 0xFFFFFFFF
        value = struct.unpack('<I', data[i*4:i*4+4])[0]
        value = (value ^ (seed1 + seed2)) & 0xFFFFFFFF
        seed1 = ((((~seed1 << 0x15) + 0x11111111) & 0xFFFFFFFF) | (seed1 >> 0x0B)) & 0xFFFFFFFF
        seed2 = (value + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
        out += struct.pack('<I', value)
    out += data[n*4:]
    return bytes(out)

def decompress(data, expected_size=None):
    ctype = data[0]
    if ctype == 0:
        return data[1:] if (expected_size is None or len(data)-1 == expected_size) else data
    if ctype == 2:
        return zlib.decompress(data[1:], 15)
    if ctype == 16:
        return bz2.decompress(data[1:])
    if ctype == 8:
        return pk_explode(data[1:])
    if ctype == 1:
        raise RuntimeError("Huffman not implemented")
    raise RuntimeError(f"Unsupported compression type {ctype}")


class MPQReader:
    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        hdr = self.f.read(32)
        assert hdr[:4] == b'MPQ\x1a', 'not mpq'
        (self.header_size, self.archive_size, self.format_version,
         self.sector_shift, self.hash_off, self.block_off,
         self.hash_entries, self.block_entries) = struct.unpack('<IIHHIIII', hdr[4:32])
        self.base_off = 0
        self.hash_table = self._read_table('hash')
        self.block_table = self._read_table('block')

    def _read_table(self, which):
        off = self.hash_off if which == 'hash' else self.block_off
        cnt = self.hash_entries if which == 'hash' else self.block_entries
        key = mpq_hash('(%s table)' % which, 'TABLE')
        self.f.seek(self.base_off + off)
        data = mpq_decrypt(self.f.read(cnt * 16), key)
        entries = []
        for i in range(cnt):
            entries.append(struct.unpack('<IIHHI' if which == 'hash' else '<IIII',
                                         data[i*16:(i+1)*16]))
        return entries

    def find(self, filename):
        ha = mpq_hash(filename, 'HASH_A')
        hb = mpq_hash(filename, 'HASH_B')
        for h in self.hash_table:
            if h[0] == ha and h[1] == hb and h[4] != 0xFFFFFFFF:
                return h
        return None

    def read_file(self, filename):
        h = self.find(filename)
        if h is None:
            return None
        off, csize, size, flags = self.block_table[h[4]]
        if not (flags & MPQ_FILE_EXISTS) or csize == 0:
            return None
        self.f.seek(self.base_off + off)
        raw = self.f.read(csize)

        key = None
        if flags & MPQ_FILE_ENCRYPTED:
            base = filename.replace('\\', '/').split('/')[-1]
            key = mpq_hash(base, 'TABLE')  # file key uses hash type 3
            if flags & MPQ_FILE_FIX_KEY:
                key = ((key + off) ^ size) & 0xFFFFFFFF

        if not (flags & MPQ_FILE_SINGLE_UNIT):
            sector_size = 512 << self.sector_shift
            sectors = size // sector_size + 1
            crc = bool(flags & MPQ_FILE_SECTOR_CRC)
            npos = sectors + (2 if crc else 1)
            pos_data = raw[:4 * npos]
            if flags & MPQ_FILE_ENCRYPTED:
                pos_data = mpq_decrypt(pos_data, (key - 1) & 0xFFFFFFFF)
            positions = struct.unpack('<%dI' % npos, pos_data)
            result = bytearray()
            left = size
            for i in range(sectors):
                sector = raw[positions[i]:positions[i+1]]
                if flags & MPQ_FILE_ENCRYPTED:
                    sector = mpq_decrypt(sector, (key + i) & 0xFFFFFFFF)
                expected = min(sector_size, left)
                if (flags & MPQ_FILE_COMPRESS) and len(sector) < expected:
                    sector = decompress(sector, expected)
                elif (flags & MPQ_FILE_IMPLODE) and len(sector) < expected:
                    sector = pk_explode(sector)
                result += sector
                left -= len(sector)
            return bytes(result)
        else:
            if flags & MPQ_FILE_ENCRYPTED:
                raw = mpq_decrypt(raw, key)
            if (flags & MPQ_FILE_COMPRESS) and size > csize:
                raw = decompress(raw, size)
            elif (flags & MPQ_FILE_IMPLODE) and size > csize:
                raw = pk_explode(raw)
            return raw

    def listfile(self):
        data = self.read_file('(listfile)')
        if data is None:
            return []
        return [ln.strip() for ln in data.decode('latin1').replace('\r\n', '\n').split('\n') if ln.strip()]


def main():
    mpq_path, out_dir = sys.argv[1], sys.argv[2]
    only = sys.argv[3:] if len(sys.argv) > 3 else None
    r = MPQReader(mpq_path)
    names = r.listfile()
    print(f"listfile: {len(names)} files")
    if not names:
        print("WARNING: no listfile")
        return
    os.makedirs(out_dir, exist_ok=True)
    ok, fail = 0, 0
    for name in names:
        rel = name.replace('\\', '/')
        if only and not any(o.lower() in rel.lower() for o in only):
            continue
        try:
            data = r.read_file(name)
            if data is None:
                print("  MISSING:", name); fail += 1; continue
            dst = os.path.join(out_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'wb') as fh:
                fh.write(data)
            ok += 1
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            fail += 1
    print(f"extracted {ok}, failed {fail}")

if __name__ == '__main__':
    main()
