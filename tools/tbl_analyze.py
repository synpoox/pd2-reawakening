"""Analyze D2 .tbl string table structure; test linear-probing hypothesis for the hash table."""
import struct, sys

def elf_hash(key: bytes, mod: int) -> int:
    h = 0
    for c in key:
        h = ((h << 4) + c) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
            h &= ~g
    return h % mod

def parse(path):
    data = open(path, 'rb').read()
    crc, keycount, hashsize, version, stringoff, numloops, filesize = struct.unpack_from('<HHI B III', data, 0)
    hdr = dict(crc=crc, keycount=keycount, hashsize=hashsize, version=version,
               stringoff=stringoff, numloops=numloops, filesize=filesize, actual=len(data))
    warr = list(struct.unpack_from('<%dH' % keycount, data, 21))
    entries = []
    eoff = 21 + 2 * keycount
    for p in range(keycount):
        used, idx, hval, koff, voff, vlen = struct.unpack_from('<B H I I I H', data, eoff + 17 * p)
        entries.append(dict(pos=p, used=used, idx=idx, hash=hval, koff=koff, voff=voff, vlen=vlen))
    # pool: keys via entry koff
    for e in entries:
        kend = data.index(b'\x00', e['koff'])
        e['key'] = data[e['koff']:kend]
        vend = data.index(b'\x00', e['voff'])
        e['val'] = data[e['voff']:vend]
    return hdr, warr, entries, data

path = sys.argv[1] if len(sys.argv) > 1 else r'extracted\s14_vanilla\data\local\LNG\ENG\patchstring.tbl'
hdr, warr, entries, data = parse(path)
print('HEADER:', hdr)
N = hdr['keycount']

# 1. hash field check
bad_hash = sum(1 for e in entries if e['hash'] != elf_hash(e['key'], hdr['hashsize']))
print(f'hash field mismatches: {bad_hash}/{N}')

# 2. warr inverse check: warr[idx] == pos ?
bad_warr = sum(1 for e in entries if warr[e['idx']] != e['pos'])
print(f'warr[idx]!=pos count: {bad_warr}/{N}')

# 3. identity fraction
ident = sum(1 for i in range(N) if warr[i] == i)
print(f'warr identity: {ident}/{N}')

# 4. linear probing simulation, insertion order = pool order (koff ascending)
by_pool = sorted(entries, key=lambda e: e['koff'])
table = [None] * N
order_pos = {}
maxprobe = 0
for e in by_pool:
    h = e['hash']
    p = h
    d = 0
    while table[p] is not None:
        p = (p + 1) % N
        d += 1
    table[p] = e['key']
    order_pos[e['key']] = p
    maxprobe = max(maxprobe, d)
match = sum(1 for e in entries if order_pos[e['key']] == e['pos'])
print(f'linear-probe(pool order) position match: {match}/{N}, max probe dist {maxprobe}, NumLoops hdr={hdr["numloops"]}')

# 5. try insertion order = idx order
by_idx = sorted(entries, key=lambda e: e['idx'])
table = [None] * N
order_pos2 = {}
maxprobe2 = 0
for e in by_idx:
    h = e['hash']; p = h; d = 0
    while table[p] is not None:
        p = (p + 1) % N; d += 1
    table[p] = e['key']
    order_pos2[e['key']] = p
    maxprobe2 = max(maxprobe2, d)
match2 = sum(1 for e in entries if order_pos2[e['key']] == e['pos'])
print(f'linear-probe(idx order)  position match: {match2}/{N}, max probe dist {maxprobe2}')

# 6. chain structure: for each bucket b, does entry at warr[b] have hash==b?
has_entry_with_hash = set(e['hash'] for e in entries)
chain_head_ok = 0
for b in range(hdr['hashsize']):
    e = entries[warr[b]]
    if e['hash'] == b:
        chain_head_ok += 1
print(f'buckets where entry[warr[b]].hash==b: {chain_head_ok}/{hdr["hashsize"]}')

# 7. for buckets with a mismatch, what does warr[b] point at?
mism = [b for b in range(hdr['hashsize']) if entries[warr[b]]['hash'] != b]
if mism:
    print(f'  sample mismatched buckets: {mism[:10]}')
    for b in mism[:5]:
        e = entries[warr[b]]
        print(f'   bucket {b}: warr->{e["pos"]} entry.hash={e["hash"]} key={e["key"][:40]}')

# 8. probe-from-bucket reachability: can every key be found by linear scan from bucket h,
#    stopping when entry.hash != h after seeing at least one? (chain-run model)
def find(key):
    h = elf_hash(key, hdr['hashsize'])
    seen = 0
    for i in range(N):
        e = entries[(h + i) % N]
        if e['hash'] == h:
            seen += 1
            if e['key'] == key:
                return i
        elif seen:
            return None
    return None
unfindable = [e for e in entries if find(e['key']) is None]
print(f'chain-run model unfindable keys: {len(unfindable)}/{N}')

# 9. pure linear probing from bucket h (ignore warr), full table, cap NumLoops+1?
def find_lp(key, cap):
    h = elf_hash(key, hdr['hashsize'])
    for i in range(min(cap, N)):
        e = entries[(h + i) % N]
        if e['key'] == key:
            return i
    return None
for cap in (hdr['numloops'], hdr['numloops'] + 1, 2 * hdr['numloops'] + 1, N):
    unf = sum(1 for e in entries if find_lp(e['key'], cap) is None)
    print(f'linear-probe from bucket (cap={cap}): unfindable {unf}/{N}')
