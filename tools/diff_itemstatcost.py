"""Positional comparison of ItemStatCost.txt: mod (s11) vs vanilla (s14)."""
import sys

def load(path):
    with open(path, 'r', encoding='latin1') as f:
        lines = [ln.rstrip('\r\n') for ln in f if ln.strip()]
    return [ln.split('\t') for ln in lines]

m = load(r'pd2-reawakening\data\global\excel\ItemStatCost.txt')
v = load(r'extracted\s14_vanilla\data\global\excel\ItemStatCost.txt')

mhdr, vhdr = m[0], v[0]
# trim trailing empties
while mhdr and mhdr[-1] == '': mhdr.pop()
while vhdr and vhdr[-1] == '': vhdr.pop()
print(f"HEADER: mod {len(mhdr)} cols, vanilla {len(vhdr)} cols")
mset = set(mhdr); vset = set(vhdr)
print(" vanilla-only cols:", sorted(vset - mset))
print(" mod-only cols:", sorted(mset - vset))

mbody, vbody = m[1:], v[1:]
print(f"\nROWS: mod={len(mbody)} vanilla={len(vbody)}")
diffs = []
for i in range(max(len(mbody), len(vbody))):
    mn = mbody[i][0] if i < len(mbody) else '<NONE>'
    vn = vbody[i][0] if i < len(vbody) else '<NONE>'
    if mn != vn:
        diffs.append((i, mn, vn))
print(f"rows with different Stat name at same index: {len(diffs)}")
for i, mn, vn in diffs:
    print(f"  row {i:3d}: mod={mn!r:40s} vanilla={vn!r}")
