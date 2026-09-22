"""GPT-2's bytes<->unicode bijection, taken apart."""
import json, unicodedata

def bytes_to_unicode():
    bs = list(range(33,127)) + list(range(161,173)) + list(range(174,256))
    cs = bs[:]; n = 0
    for b in range(256):
        if b not in bs: bs.append(b); cs.append(256+n); n += 1
    return dict(zip(bs, (chr(c) for c in cs)))

B2U = bytes_to_unicode()
U2B = {c: b for b, c in B2U.items()}          # the inverse

print("=" * 70); print("THE PROBLEM"); print("=" * 70)
raw = "Café".encode("utf-8")
print(f"  'Café' as bytes      : {list(raw)}")
print(f"  byte 0xC3 alone      : {raw[3:4]}  <- not valid UTF-8 on its own")
try:
    json.dumps({raw[3:4].decode("utf-8"): 1})
except UnicodeDecodeError as e:
    print(f"  putting it in JSON   : UnicodeDecodeError: {e.reason}")
print("  ...but a BPE vocab IS a JSON file of strings. So we need bytes-as-text.")

print("\n" + "=" * 70); print("THE THREE 'MAP TO SELF' RANGES"); print("=" * 70)
groups = [(33,127,"printable ASCII"), (161,173,"printable Latin-1 (upper)"), (174,256,"printable Latin-1 (rest)")]
for lo, hi, label in groups:
    print(f"  range({lo},{hi})  {hi-lo:>3} bytes  {label}")
    print(f"      e.g. byte {lo} -> {B2U[lo]!r}, byte {hi-1} -> {B2U[hi-1]!r}   (codepoint == byte value)")

print("\n  What those ranges DELIBERATELY skip:")
for b in [0, 9, 10, 32, 127, 160, 173]:
    name = unicodedata.name(chr(b), "<no name>")
    print(f"      byte {b:>3} = {name:<28} -> remapped to {B2U[b]!r} (U+{ord(B2U[b]):04X})")

print("\n" + "=" * 70); print("THE REMAP"); print("=" * 70)
remapped = sorted(b for b in range(256) if B2U[b] != chr(b))
print(f"  bytes that map to themselves : {256-len(remapped)}")
print(f"  bytes that get shifted       : {len(remapped)}  -> codepoints 256..{max(ord(B2U[b]) for b in remapped)}")
print(f"  highest codepoint used       : {max(ord(c) for c in B2U.values())}")
print("  (so a 512-entry array holds the whole inverse -- no hashing needed)")

print("\n" + "=" * 70); print("THE INVARIANTS THAT MAKE IT WORK"); print("=" * 70)
print(f"  1. bijective (256 distinct outputs) : {len(set(B2U.values())) == 256}")
print(f"  2. no whitespace in the alphabet    : {not any(c.isspace() for c in B2U.values())}")
print(f"  3. no control chars in the alphabet : {not any(unicodedata.category(c) == 'Cc' for c in B2U.values())}")
print("     -> every token is a safe, visible JSON string, and the pre-tokenizer")
print("        regex can never accidentally split inside one.")

print("\n" + "=" * 70); print("ROUND TRIP"); print("=" * 70)
for s in ["Café", "How are you 😁", "tab\there"]:
    enc = "".join(B2U[b] for b in s.encode("utf-8"))
    dec = bytes(U2B[c] for c in enc).decode("utf-8")
    print(f"  {s!r:<20} -> {enc!r:<26} -> {dec!r}   {'OK' if dec == s else 'FAIL'}")

print("\n  every one of the 256 bytes round-trips:",
      all(bytes([b]) == bytes([U2B[B2U[b]]]) for b in range(256)))
