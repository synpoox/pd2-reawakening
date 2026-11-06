import os

def files(root):
    out = {}
    for dp, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root).replace(os.sep, '/').lower()
            out[rel] = os.path.getsize(p)
    return out

s14 = files(r'extracted\s14_vanilla')
mod = files(r'extracted\s11_ra')
only_mod = sorted(set(mod) - set(s14))
only_s14 = sorted(set(s14) - set(mod))
diff = sorted(k for k in set(s14) & set(mod) if s14[k] != mod[k])
print(f'mod-only files: {len(only_mod)}')
for f in only_mod:
    print('   ', f, mod[f])
print(f'S14-only files: {len(only_s14)}')
for f in only_s14[:60]:
    print('   ', f, s14[f])
print(f'changed (size differs): {len(diff)}')
for f in diff:
    print('   ', f, f'mod={mod[f]} s14={s14[f]}')
