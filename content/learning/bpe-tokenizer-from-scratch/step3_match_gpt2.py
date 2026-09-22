"""
Step 3: feed GPT-2's REAL 50,000 merge rules to the encoder from step 2.
Phase A shows the naive version failing. Phase B fixes it and gets exact parity.
"""
import json, time, urllib.request
import regex as re            # `regex`, not `re` -- needed for \p{L}
from tokenizers import Tokenizer   # HuggingFace, as the reference to check against

# ---------------------------------------------------------------- load the real thing
raw    = json.load(urllib.request.urlopen("https://huggingface.co/gpt2/resolve/main/tokenizer.json"))
vocab  = raw["model"]["vocab"]
merges = [tuple(m) if isinstance(m, list) else tuple(m.split(" ")) for m in raw["model"]["merges"]]
RANKS  = {pair: i for i, pair in enumerate(merges)}     # pair -> priority. O(1) lookup.
hf     = Tokenizer.from_pretrained("gpt2")

print(f"loaded {len(vocab):,} vocab entries, {len(merges):,} merge rules\n")

# ---------------------------------------------------------------- the merge loop (step 2's, sped up)
def apply_merge(symbols, pair):
    a, b = pair; out, i = [], 0
    while i < len(symbols):
        if i < len(symbols)-1 and symbols[i] == a and symbols[i+1] == b:
            out.append(a+b); i += 2
        else:
            out.append(symbols[i]); i += 1
    return out

def bpe(word):
    """Instead of looping over 50,000 rules, look at the ~5 pairs actually in
    this word and pick the best-ranked one. Same answer, ~10,000x less work."""
    symbols = list(word)
    while len(symbols) > 1:
        best, best_rank = None, None
        for i in range(len(symbols)-1):
            r = RANKS.get((symbols[i], symbols[i+1]))
            if r is not None and (best_rank is None or r < best_rank):
                best, best_rank = (symbols[i], symbols[i+1]), r
        if best is None:
            break
        symbols = apply_merge(symbols, best)
    return symbols

# ---------------------------------------------------------------- PHASE A: naive
def pre_tokenize_naive(text):
    return ["Ġ" + w if i > 0 else w for i, w in enumerate(text.split(" "))]

def encode_naive(text):
    toks = []
    for w in pre_tokenize_naive(text):
        toks.extend(bpe(w))
    return toks

TESTS = [
    "the cat sat on the mat",
    "Hello, world!",
    "def foo(x): return x + 1",
    "Café costs $12.50",
    "How are you 😁 ?",
]

print("=" * 78)
print("PHASE A -- step 2's pre_tokenizer + GPT-2's real merges")
print("=" * 78)
for t in TESTS:
    mine = encode_naive(t)
    theirs = hf.encode(t, add_special_tokens=False).tokens
    ok = "MATCH" if mine == theirs else "differs"
    print(f"  {t!r}")
    print(f"     mine  : {mine}")
    print(f"     hf    : {theirs}")
    print(f"     -> {ok}\n")

# ---------------------------------------------------------------- PHASE B: the real stages 1+2
def bytes_to_unicode():
    bs = list(range(33,127)) + list(range(161,173)) + list(range(174,256))
    cs = bs[:]; n = 0
    for b in range(256):
        if b not in bs: bs.append(b); cs.append(256+n); n += 1
    return dict(zip(bs, (chr(c) for c in cs)))
B2U = bytes_to_unicode()

GPT2_PAT = re.compile(r"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+")

def encode_real(text):
    toks = []
    for chunk in GPT2_PAT.findall(text):                      # stage 2a: the regex
        chunk = "".join(B2U[b] for b in chunk.encode("utf-8"))# stage 2b: bytes -> unicode
        toks.extend(bpe(chunk))                               # stage 3:  merge
    return toks

print("=" * 78)
print("PHASE B -- + the GPT-2 regex + the byte-level mapping")
print("=" * 78)
for t in TESTS:
    mine = encode_real(t)
    theirs = hf.encode(t, add_special_tokens=False).tokens
    print(f"  {'MATCH' if mine == theirs else 'DIFFERS'}  {t!r}")
    if mine != theirs:
        print(f"     mine: {mine}\n     hf  : {theirs}")

# ---------------------------------------------------------------- bulk parity check
print("\n" + "=" * 78)
print("BULK CHECK -- 200 lines of real text, ids not just tokens")
print("=" * 78)
text = urllib.request.urlopen(
    "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
).read().decode()
lines = [l for l in text.split("\n") if l.strip()][:200]

def encode_ids(t):
    return [vocab[s] for s in encode_real(t)]

bad = 0
for l in lines:
    if encode_ids(l) != hf.encode(l, add_special_tokens=False).ids:
        bad += 1
print(f"  lines checked : {len(lines)}")
print(f"  mismatches    : {bad}")
print(f"  -> {'EXACT PARITY with HuggingFace' if bad == 0 else 'not there yet'}")

# ---------------------------------------------------------------- speed
blob = "\n".join(lines)
t0 = time.perf_counter(); encode_ids(blob);                           t_mine = time.perf_counter()-t0
t0 = time.perf_counter(); hf.encode(blob, add_special_tokens=False);  t_hf   = time.perf_counter()-t0
n = len(blob.encode())
print(f"\n  yours (Python) : {t_mine*1000:8.1f} ms   {n/t_mine/1e6:6.2f} MB/s")
print(f"  HF    (Rust)   : {t_hf*1000:8.1f} ms   {n/t_hf/1e6:6.2f} MB/s")
print(f"  -> HF is {t_mine/t_hf:.0f}x faster, for byte-identical output")
