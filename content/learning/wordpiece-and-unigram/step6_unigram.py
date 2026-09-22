"""
Step 6: Unigram (T5, ALBERT, via SentencePiece; Llama 1/2 use SentencePiece's BPE mode instead).

BPE     : a PROCEDURE. Apply learned merges in order. The answer is whatever
          the procedure produces. No notion of a 'better' segmentation.
Unigram : an OPTIMIZATION. Every piece has a log-probability. Score a
          segmentation by summing them. Return the HIGHEST-SCORING one.
          Found with Viterbi (dynamic programming) over a lattice.
"""
import json, math, urllib.request
from tokenizers import Tokenizer

raw   = json.load(urllib.request.urlopen("https://huggingface.co/t5-base/resolve/main/tokenizer.json"))
m     = raw["model"]
PIECES = m["vocab"]                                  # list of [piece, log_prob]
SCORES = {p: s for p, s in PIECES}
ID     = {p: i for i, (p, _) in enumerate(PIECES)}
UNK_ID = m.get("unk_id", 2)
MIN_SCORE = min(s for _, s in PIECES)
UNK_SCORE = MIN_SCORE - 10.0                         # K_UNK_PENALTY, from model.rs:80
MAXLEN = max(len(p) for p, _ in PIECES)
hf = Tokenizer.from_pretrained("t5-base")

print(f"vocab {len(PIECES):,} pieces | min_score {MIN_SCORE:.3f} | unk_score {UNK_SCORE:.3f}\n")
print("A Unigram vocab entry is a piece AND a score:")
for p in ["▁the", "▁tokenization", "▁token", "ization", "▁un", "s", "▁"]:
    if p in SCORES: print(f"   {p!r:<18} score = {SCORES[p]:8.4f}")

# =====================================================================
#  VITERBI -- mirrors tk-encode/src/models/unigram/model.rs:294-360
# =====================================================================
def unigram(text):
    n = len(text)
    best  = [0.0]*(n+1)      # best total score of a path ending at i
    start = [None]*(n+1)     # backpointer
    isunk = [False]*(n+1)
    for i in range(n):
        cur, has_single = best[i], False
        for j in range(i+1, min(n, i+MAXLEN)+1):
            sc = SCORES.get(text[i:j])
            if sc is None: continue
            cand = cur + sc
            if start[j] is None or cand > best[j]:
                best[j], start[j], isunk[j] = cand, i, False
            if j - i == 1: has_single = True
        if not has_single:                      # no single-char piece -> UNK node
            j, cand = i+1, cur + UNK_SCORE
            if start[j] is None or cand > best[j]:
                best[j], start[j], isunk[j] = cand, i, True
    out, e = [], n                               # backtrack, fusing adjacent UNKs
    while e > 0:
        s = start[e]
        if out and isunk[e] and out[-1][1]: out[-1] = (text[s:e]+out[-1][0], True)
        else: out.append((text[s:e], isunk[e]))
        e = s
    return [(t, UNK_ID if u else ID[t]) for t, u in reversed(out)]

def encode(text):
    norm = hf.normalizer.normalize_str(text)
    return [tok for w, _ in hf.pre_tokenizer.pre_tokenize_str(norm) for tok in unigram(w)]

# =====================================================================
print("\n" + "=" * 74); print("IT IS AN OPTIMIZATION: all segmentations, ranked"); print("=" * 74)
def all_segs(t, depth=0):
    if not t: yield []
    for j in range(1, min(len(t), MAXLEN)+1):
        if t[:j] in SCORES:
            for rest in all_segs(t[j:], depth+1): yield [t[:j]] + rest
for word in ["▁unbelievable", "▁tokenization"]:
    segs = [(sum(SCORES[p] for p in s), s) for s in all_segs(word)]
    segs.sort(reverse=True)
    print(f"\n  {word!r}  -- {len(segs)} valid segmentations exist")
    for sc, s in segs[:5]:  print(f"      {sc:9.3f}  {s}")
    print(f"      {'...':>9}")
    for sc, s in segs[-2:]: print(f"      {sc:9.3f}  {s}")
    print(f"      Viterbi picks: {[t for t,_ in unigram(word)]}")

print("\n" + "=" * 74); print("PARITY WITH HUGGINGFACE"); print("=" * 74)
TESTS = ["the cat sat on the mat", "unbelievable tokenization results",
         "Café costs $12.50", "antidisestablishmentarianism"]
for t in TESTS:
    mine = [x[0] for x in encode(t)]
    theirs = hf.encode(t, add_special_tokens=False).tokens
    print(f"  {'MATCH' if mine == theirs else 'DIFFERS'}  {t!r}\n           {mine}")
lines = [l for l in urllib.request.urlopen(
    "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
).read().decode().split("\n") if l.strip()][:200]
bad = sum(1 for l in lines if [x[1] for x in encode(l)] != hf.encode(l, add_special_tokens=False).ids)
print(f"\n  200 lines of Shakespeare, compared by ID -> {bad} mismatches")

print("\n" + "=" * 74); print("THREE ALGORITHMS, SAME WORDS"); print("=" * 74)
g  = Tokenizer.from_pretrained("gpt2")
b  = Tokenizer.from_pretrained("bert-base-uncased")
print(f"  {'word':<20}{'BPE (gpt2)':<34}{'WordPiece (bert)':<34}{'Unigram (t5)'}")
for w in ["unbelievable", "tokenization", "hugging", "internationalization"]:
    print(f"  {w:<20}"
          f"{str(g.encode(' '+w, add_special_tokens=False).tokens):<34}"
          f"{str(b.encode(w, add_special_tokens=False).tokens):<34}"
          f"{[t for t,_ in unigram('▁'+w)]}")
