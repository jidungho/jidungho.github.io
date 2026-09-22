"""
Step 7: BPE training dynamics at scale.

Train real vocabularies on 21 MB of English prose (23 books), measure what each
size buys on HELD-OUT text (Pride & Prejudice, never trained on).
"""
import glob, time, pathlib
from tokenizers import Tokenizer, models, trainers, pre_tokenizers

D = pathlib.Path("learning/data")
rd = lambda p: pathlib.Path(p).read_text(encoding="utf-8", errors="ignore")
train_files = [p for p in sorted(D.glob("book_*.txt")) if "1342" not in p.name]
heldout     = rd(D / "book_1342.txt")
train_text  = "\n".join(rd(f) for f in train_files)
code_text   = "\n".join(rd(p) for p in glob.glob("tokenizers/tk-encode/src/**/*.rs", recursive=True))

print(f"train   : {len(train_text)/1e6:5.2f} MB  ({len(train_files)} books)")
print(f"held out: {len(heldout)/1e6:5.2f} MB  (Pride and Prejudice)")
print(f"code    : {len(code_text)/1e6:5.2f} MB  (this repo's Rust source)\n")

def train(vocab_size, text, min_freq=2):
    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tr = trainers.BpeTrainer(vocab_size=vocab_size, min_frequency=min_freq, show_progress=False,
                             initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    t0 = time.perf_counter(); tok.train_from_iterator([text], tr)
    return tok, time.perf_counter() - t0

def cpt(tok, text):                     # chars per token
    return len(text) / len(tok.encode(text, add_special_tokens=False).ids)

# =====================================================================
print("=" * 88); print("1. VOCAB-SIZE SWEEP  (evaluated on HELD-OUT text)"); print("=" * 88)
SIZES = [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]
print(f"  {'asked':>8} {'got':>8} {'train_s':>8} {'tok/word':>9} {'chars/tok':>10} {'tokens':>12} {'gain':>7}")
rows, prev, toks_by_size = [], None, {}
for v in SIZES:
    tok, secs = train(v, train_text)
    got = tok.get_vocab_size()
    ids = tok.encode(heldout, add_special_tokens=False).ids
    c   = len(heldout)/len(ids)
    gain = "" if prev is None else f"{(prev-len(ids))/prev*100:5.1f}%"
    print(f"  {v:>8,} {got:>8,} {secs:>8.1f} {len(ids)/len(heldout.split()):>9.3f} "
          f"{c:>10.2f} {len(ids):>12,} {gain:>7}")
    rows.append((got, c)); prev = len(ids); toks_by_size[v] = tok

# =====================================================================
print("\n" + "=" * 88); print("2. CORPUS SIZE CAPS VOCAB SIZE"); print("=" * 88)
print("  asking for 100k merges, varying how much text you give it:\n")
print(f"  {'corpus':>10} {'vocab actually reached':>24} {'chars/tok on held-out':>23}")
for frac in [0.01, 0.05, 0.2, 0.5, 1.0]:
    sub = train_text[:int(len(train_text)*frac)]
    tok, _ = train(100_000, sub)
    print(f"  {len(sub)/1e6:>7.2f} MB {tok.get_vocab_size():>24,} {cpt(tok, heldout):>23.2f}")
print("\n  min_frequency=2 means a merge needs 2 sightings. Small corpus -> runs out")
print("  of repeated pairs -> vocab saturates no matter what you ask for.")

# =====================================================================
print("\n" + "=" * 88); print("3. WHAT GETS LEARNED, AND WHEN"); print("=" * 88)
big = toks_by_size[65536]
ranked = [t for t, _ in sorted(big.get_vocab().items(), key=lambda kv: kv[1])]
for lo, label in [(256,"rank ~0"), (500,"rank ~500"), (2000,"rank ~2k"), (8000,"rank ~8k"),
                  (20000,"rank ~20k"), (40000,"rank ~40k"), (60000,"rank ~60k")]:
    print(f"  {label:<11} {ranked[lo:lo+7]}")

# =====================================================================
print("\n" + "=" * 88); print("4. DOMAIN MISMATCH"); print("=" * 88)
code_tok, _ = train(32768, code_text)
print(f"  {'trained on':<24}{'on books':>12}{'on Rust code':>14}")
for name, tk in [("English books", toks_by_size[32768]), ("Rust source", code_tok)]:
    print(f"  {name:<24}{cpt(tk,heldout):>12.2f}{cpt(tk,code_text):>14.2f}   chars/token")
gpt2 = Tokenizer.from_pretrained("gpt2")
print(f"  {'GPT-2 (50k, WebText)':<24}{cpt(gpt2,heldout):>12.2f}{cpt(gpt2,code_text):>14.2f}   chars/token")

# =====================================================================
print("\n" + "=" * 88); print("5. THE ENGINEERING DECISION"); print("=" * 88)
D_MODEL = 4096
print(f"  d_model={D_MODEL}, untied embeddings, a 1e12-char training corpus\n")
print(f"  {'vocab':>8} {'embed params':>14} {'tokens for corpus':>19} {'chars per 8k ctx':>18}")
for v, c in rows:
    print(f"  {v:>8,} {v*D_MODEL*2/1e6:>11.0f} M {1e12/c/1e9:>16.1f} B {8192*c:>18,.0f}")
