# Port of Mark Adler's blast.c (PKWARE DCL explode), for reading imploded MPQ files.
LITLEN = [11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8,
          9, 7, 6, 7, 8, 7, 6, 55, 8, 23, 24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5,
          7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9, 12,
          8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27,
          44, 253, 253, 253, 252, 252, 252, 13, 12, 45, 12, 45, 12, 61, 12, 45,
          44, 173]
LENLEN = [2, 35, 36, 53, 38, 23]
DISTLEN = [2, 20, 53, 230, 247, 151, 248]
BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]


def construct(rep):
    length = []
    for r in rep:
        n = (r >> 4) + 1
        length += [r & 15] * n
    count = [0] * 14
    for l in length:
        count[l] += 1
    offs = [0] * 14
    for i in range(1, 13):
        offs[i + 1] = offs[i] + count[i]
    symbol = [0] * len(length)
    for s, l in enumerate(length):
        if l:
            symbol[offs[l]] = s
            offs[l] += 1
    return count, symbol


LIT, LEN, DIST = construct(LITLEN), construct(LENLEN), construct(DISTLEN)


def explode(src):
    pos, bitbuf, bitcnt = 0, 0, 0

    def bits(need):
        nonlocal pos, bitbuf, bitcnt
        val = bitbuf
        while bitcnt < need:
            val |= src[pos] << bitcnt
            pos += 1
            bitcnt += 8
        bitbuf = val >> need
        bitcnt -= need
        return val & ((1 << need) - 1)

    def decode(h):
        count, symbol = h
        code = first = index = 0
        for l in range(1, 14):
            code |= bits(1) ^ 1
            c = count[l]
            if code < first + c:
                return symbol[index + (code - first)]
            index += c
            first = (first + c) << 1
            code <<= 1
        raise ValueError("bad code")

    lit = bits(8)
    dictbits = bits(8)
    out = bytearray()
    while True:
        if bits(1):
            sym = decode(LEN)
            ln = BASE[sym] + bits(EXTRA[sym])
            if ln == 519:
                return bytes(out)
            sym = 2 if ln == 2 else dictbits
            dist = (decode(DIST) << sym) + bits(sym) + 1
            for _ in range(ln):
                out.append(out[-dist])
        else:
            out.append(decode(LIT) if lit else bits(8))
