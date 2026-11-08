"""Self-check for the density patch and the bin check. Run: python tools/test_build.py"""
import os
import struct
import tempfile

from build import DENSITY_FIELDS, LEVELS_RECORD_SIZE, bin_problems, density_bin, density_txt

header = b'Name\t' + b'\t'.join(col.encode() for col, _, _ in DENSITY_FIELDS) + b'\tOther'
row = b'Lvl\t100\t200\t300\t1\t2\t3\t4\t5\t60\t7'
blank = b'Town\t\t\t\t\t\t\t\t\t\t7'
txt = density_txt(b'\r\n'.join([header, row, blank, b'']), 5)
assert txt == b'\r\n'.join([header, b'Lvl\t500\t1000\t1500\t5\t10\t15\t20\t25\t255\t7', blank, b'']), txt

rec = bytearray(LEVELS_RECORD_SIZE)
struct.pack_into('<3i', rec, 28, 100, 200, 300)
rec[40:46] = bytes([1, 2, 3, 4, 5, 60])
out = density_bin(struct.pack('<I', 1) + bytes(rec), 5)
assert struct.unpack_from('<3i', out, 4 + 28) == (500, 1000, 1500)
assert list(out[4 + 40:4 + 46]) == [5, 10, 15, 20, 25, 255]
assert out[4 + 46:] == bytes(LEVELS_RECORD_SIZE - 46)

with tempfile.TemporaryDirectory() as excel:
    def put(name, data):
        with open(os.path.join(excel, name), 'wb') as fh:
            fh.write(data)
    table = b'name\tcode\r\na\t1\r\nExpansion\r\nb\t2\r\n\r\n'  # 2 rows + a divider
    put('Good.txt', table); put('good.bin', struct.pack('<I', 2))
    put('Kept.txt', table); put('kept.bin', struct.pack('<I', 3))   # divider counted, like objgroup
    put('Spacer.txt', b'name\tcode\r\na\t1\r\n\t\r\nb\t2\r\n'); put('spacer.bin', struct.pack('<I', 3))  # tab-only row counted
    put('Stale.txt', table); put('stale.bin', struct.pack('<I', 1))
    put('Missing.txt', table)
    put('MonName.txt', table)  # txt-only table
    assert bin_problems(excel) == ['Missing.txt: no .bin', 'stale.bin: 1 records, Stale.txt has 2 rows'], bin_problems(excel)
print('ok')
