"""Merge mod S11 patchstring.tbl into S14 patchstring.tbl; write a rebuilt tbl.

Lookup model (verified on both files): plain linear probing over the entries array
from bucket ELFhash(key)%HashSize, capped at NumLoops (= max probe distance + 1).
WORD array = idx->position permutation for index-based access; existing S14 idx values
MUST be preserved because compiled .bin files reference strings by idx.
CRC16-CCITT (init 0xFFFF, poly 0x1021) over the string pool.
"""
import struct, sys, os

def elf_hash(key: bytes, mod: int) -> int:
    h = 0
    for c in key:
        h = ((h << 4) + c) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
            h &= ~g
    return h % mod

def crc16_ccitt(buf, init=0xFFFF, poly=0x1021):
    c = init
    for b in buf:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c

def parse(path):
    data = open(path, 'rb').read()
    crc, keycount, hashsize, version, stringoff, numloops, filesize = struct.unpack_from('<HHI B III', data, 0)
    warr = list(struct.unpack_from('<%dH' % keycount, data, 21))
    entries = []
    eoff = 21 + 2 * keycount
    for p in range(keycount):
        used, idx, hval, koff, voff, vlen = struct.unpack_from('<B H I I I H', data, eoff + 17 * p)
        kend = data.index(b'\x00', koff)
        vend = data.index(b'\x00', voff)
        entries.append(dict(pos=p, used=used, idx=idx, hash=hval,
                            key=data[koff:kend], val=data[voff:vend]))
    hdr = dict(crc=crc, keycount=keycount, hashsize=hashsize, version=version,
               stringoff=stringoff, numloops=numloops, filesize=filesize)
    return hdr, warr, entries

def build(pairs_by_idx):
    """pairs_by_idx: list of (key, val) in idx order. Returns file bytes + stats."""
    N = len(pairs_by_idx)
    # positions via linear probing, insertion in idx order
    table = [None] * N          # pos -> idx
    pos_of_idx = [0] * N
    maxprobe = 0
    for idx, (key, val) in enumerate(pairs_by_idx):
        h = elf_hash(key, N)
        p = h
        d = 0
        while table[p] is not None:
            p = (p + 1) % N
            d += 1
        table[p] = idx
        pos_of_idx[idx] = p
        maxprobe = max(maxprobe, d)
    # string pool in idx order
    pool = bytearray()
    koffs, voffs = [], []
    for key, val in pairs_by_idx:
        koffs.append(0)  # placeholder, patched after stringoff known
    # first compute pool relative offsets
    rel = 0
    krel, vrel = [], []
    for key, val in pairs_by_idx:
        krel.append(rel); rel += len(key) + 1
        vrel.append(rel); rel += len(val) + 1
        pool += key + b'\x00' + val + b'\x00'
    stringoff = 21 + 2 * N + 17 * N
    # warr: idx -> pos
    warr = pos_of_idx
    out = bytearray()
    filesize = stringoff + len(pool)
    out += struct.pack('<HHI B III', crc16_ccitt(bytes(pool)), N, N, 1, stringoff, maxprobe + 1, filesize)
    out += struct.pack('<%dH' % N, *warr)
    for p in range(N):
        idx = table[p]
        key, val = pairs_by_idx[idx]
        out += struct.pack('<B H I I I H', 1, idx, elf_hash(key, N),
                           stringoff + krel[idx], stringoff + vrel[idx], len(val) + 1)
    out += pool
    assert len(out) == filesize
    return bytes(out), maxprobe + 1

def verify(blob, expect):
    """Re-parse built blob; check every key findable via linear probe within NumLoops."""
    data = blob
    crc, keycount, hashsize, version, stringoff, numloops, filesize = struct.unpack_from('<HHI B III', data, 0)
    entries = []
    eoff = 21 + 2 * keycount
    for p in range(keycount):
        used, idx, hval, koff, voff, vlen = struct.unpack_from('<B H I I I H', data, eoff + 17 * p)
        kend = data.index(b'\x00', koff)
        vend = data.index(b'\x00', voff)
        entries.append((idx, hval, data[koff:kend], data[voff:vend]))
    bad = 0
    for idx, hval, key, val in entries:
        if hval != elf_hash(key, hashsize):
            bad += 1; continue
        found = False
        for i in range(numloops):
            p = (hval + i) % keycount
            e2 = entries[p]
            if e2[2] == key:
                found = True; break
        if not found:
            bad += 1
    # content check (multiset — duplicate keys are legal in tbl files)
    from collections import Counter
    got = Counter((e[2], e[3]) for e in entries)
    content_ok = got == Counter(expect)
    return bad, content_ok

if __name__ == '__main__':
    s14_path = r'extracted\s14_vanilla\data\local\LNG\ENG\patchstring.tbl'
    mod_path = r'extracted\s11_ra\data\local\LNG\ENG\patchstring.tbl'
    out_path = r'..\reawakening-s14\data\local\LNG\ENG\patchstring.tbl'
    log_path = r'..\reawakening-s14\docs\patchstring_merge.md'

    hdr14, w14, e14 = parse(s14_path)
    hdrm, wm, em = parse(mod_path)

    # round-trip self-test: rebuild pure S14 and verify
    pairs14 = [(e['key'], e['val']) for e in sorted(e14, key=lambda x: x['idx'])]
    blob, nl = build(pairs14)
    bad, ok = verify(blob, pairs14)
    print(f'S14-only roundtrip: {bad} bad lookups, content ok={ok}, NumLoops={nl}')

    s14_keys = {e['key'] for e in e14}
    pairs = list(pairs14)
    appended, deferred = [], []
    for e in sorted(em, key=lambda x: x['idx']):
        k, v = e['key'], e['val']
        if k in s14_keys:
            # key exists in S14: S14 value wins in Stage 1 (consistency with S14 data rows).
            # Mod's variant is deferred for the Stage-2 awakening/string review.
            s14vals = {x['val'] for x in e14 if x['key'] == k}
            if v not in s14vals:
                deferred.append((k, v, next(iter(s14vals))))
        else:
            pairs.append((k, v))
            appended.append((k, v))

    blob, nl = build(pairs)
    bad, ok = verify(blob, pairs)
    print(f'merged: {len(pairs)} entries (+{len(appended)} mod-only, {len(deferred)} mod variants deferred to Stage 2), {bad} bad lookups, content ok={ok}, NumLoops={nl}')

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, 'wb').write(blob)
    print('wrote', out_path, len(blob), 'bytes')

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f'# patchstring.tbl merge: S14 ({hdr14["keycount"]} entries) + Reawakening S11 ({hdrm["keycount"]} entries)\n\n')
        f.write(f'- Result: {len(pairs)} entries, NumLoops={nl}\n')
        f.write(f'- {len(appended)} mod-only keys appended (new idx {hdr14["keycount"]}..{len(pairs)-1})\n')
        f.write(f'- {len(deferred)} mod value variants NOT applied (S14 wins in Stage 1 for consistency with S14 data rows).\n')
        f.write('  Includes the mod\'s mastery rename (General Mastery / Polearm And Spear Mastery) and\n')
        f.write('  awakened-summon strings (ExtraGolem etc.) - review together with the corresponding\n')
        f.write('  Skills/ItemStatCost data in Stage 2.\n\n')
        f.write('## Deferred conflicts (mod value NOT applied)\n\n')
        for k, modv, s14v in deferred:
            f.write(f'- `{k.decode("latin1")}`\n  - S14 (kept): {s14v.decode("latin1")!r}\n  - mod (deferred): {modv.decode("latin1")!r}\n')
        f.write('\n## Appended mod-only keys\n\n')
        for k, v in appended:
            f.write(f'- `{k.decode("latin1")}` = {v.decode("latin1")!r}\n')
    print('wrote', log_path)
