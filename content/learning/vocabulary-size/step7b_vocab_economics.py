"""
Step 7b: so what vocab size SHOULD you pick? Turn step 7's curve into a decision.
Training FLOPs ~ 6 * N_params * N_tokens  (Kaplan/Chinchilla heuristic).
"""
from tokenizers import Tokenizer

D_MODEL = 4096
# (vocab, chars_per_token) measured on held-out text in step 7
CURVE = [(512,2.07),(1024,2.63),(2048,3.07),(4096,3.44),(8192,3.80),
         (16384,4.04),(32768,4.19),(65536,4.25),(76455,4.26)]
CORPUS_CHARS = 1e12

def total_flops(n_body, vocab, cpt):
    n = n_body + vocab * D_MODEL * 2          # body + input/output embeddings
    d = CORPUS_CHARS / cpt                    # tokens needed for the corpus
    return 6 * n * d

print("=" * 78); print("WHICH VOCAB MINIMISES TRAINING COMPUTE?"); print("=" * 78)
print(f"  {'body params':>12} " + "".join(f"{v//1024:>6}k" for v, _ in CURVE[3:]))
for n_body in [1e9, 7e9, 17e9, 70e9, 400e9]:
    costs = [(total_flops(n_body, v, c), v) for v, c in CURVE]
    best = min(costs)[1]
    rel = [f"{total_flops(n_body,v,c)/min(costs)[0]:>6.3f}" for v, c in CURVE[3:]]
    print(f"  {n_body/1e9:>10.0f} B " + "".join(rel) + f"   -> best {best:,}")
print("\n  (1.000 = cheapest for that model size; higher = more expensive)")

# crossover
print("\n" + "=" * 78); print("WHY BIG MODELS WANT BIG VOCABULARIES"); print("=" * 78)
lo, hi = (32768, 4.19), (65536, 4.25)
extra_params = (hi[0]-lo[0]) * D_MODEL * 2
saved_tokens = CORPUS_CHARS/lo[1] - CORPUS_CHARS/hi[1]
print(f"  going {lo[0]:,} -> {hi[0]:,} vocab:")
print(f"    costs  you {extra_params/1e6:.0f} M extra parameters, paid on EVERY token")
print(f"    saves  you {saved_tokens/1e9:.1f} B tokens, worth 6*N_body FLOPs each")
# solve (N + e_lo) * d_lo == (N + e_hi) * d_hi for N
e_lo, e_hi = lo[0]*D_MODEL*2, hi[0]*D_MODEL*2
d_lo, d_hi = CORPUS_CHARS/lo[1], CORPUS_CHARS/hi[1]
n_cross = (e_hi*d_hi - e_lo*d_lo) / (d_lo - d_hi)
print(f"    break-even body size: {n_cross/1e9:.1f} B parameters")
print(f"\n  Below that, the extra embedding table costs more than the tokens it saves.")
print(f"  Above it, the reverse. Model size and vocab size are COUPLED decisions.")
print(f"  (Reality check: Llama 2 used 32k at every size, Llama 3 128k at every size,")
print(f"   8B included. Real vocabularies also buy multilingual and code coverage,")
print(f"   which this English-only curve cannot see.)")

# the tail of a real vocabulary
print("\n" + "=" * 78); print("WHERE 'GLITCH TOKENS' LIVE"); print("=" * 78)
g = Tokenizer.from_pretrained("gpt2")
v = sorted(g.get_vocab().items(), key=lambda kv: kv[1])
for lo_, label in [(1000,"rank  1k"), (25000,"rank 25k"), (49000,"rank 49k"), (50100,"rank 50.1k")]:
    print(f"  {label:<11} {[t for t,_ in v[lo_:lo_+6]]}")
weird = [t for t, i in v if i > 45000 and len(t) > 9 and t.isalpha()]
print(f"\n  long single-word tokens in GPT-2's last 5k slots: {weird[:12]}")
print("  Ordinary words -- the tail is not where the glitch tokens are.")
V = g.get_vocab()
glitch = ["ĠSolidGoldMagikarp", "ĠTheNitromeFan", "ĠRandomRedditor", "Ġdavidjl", "embedreportprint"]
print(f"\n  known glitch tokens: {[(t, V[t]) for t in glitch]}")
print("  They sit mid-vocabulary. They were frequent in the tokenizer's training")
print("  text and nearly absent from the models', so their embeddings got almost")
print("  no gradient signal.")
