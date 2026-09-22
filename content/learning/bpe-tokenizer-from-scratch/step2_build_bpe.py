"""
A complete BPE tokenizer in ~60 lines of real code.
Train it, encode with it, decode with it. No libraries.

Run:  python3 step2_build_bpe.py
"""
from collections import Counter

# =====================================================================
#  THE FOUR FUNCTIONS. This is the entire algorithm.
# =====================================================================

def pre_tokenize(text):
    """Cut text into words. Each leading space is glued to the word that
    follows it and written 'G' (GPT-2 writes it 'Ġ'). The model may never
    merge across these boundaries."""
    return ["Ġ" + w if i > 0 else w for i, w in enumerate(text.split(" "))]


def count_pairs(splits, word_freqs):
    """How often does each ADJACENT PAIR of symbols occur in the corpus?
    splits[w] is the current symbol list for word w, e.g. ['t','h','e']."""
    pairs = Counter()
    for word, freq in word_freqs.items():
        symbols = splits[word]
        for i in range(len(symbols) - 1):
            pairs[(symbols[i], symbols[i + 1])] += freq   # weight by word frequency
    return pairs


def apply_merge(symbols, pair):
    """Replace every adjacent occurrence of `pair` with the glued symbol."""
    a, b = pair
    out, i = [], 0
    while i < len(symbols):
        if i < len(symbols) - 1 and symbols[i] == a and symbols[i + 1] == b:
            out.append(a + b)     # glue
            i += 2
        else:
            out.append(symbols[i])
            i += 1
    return out


def train(corpus, num_merges, verbose_steps=5):
    """Learn a merge list. THIS IS THE WHOLE TRAINING ALGORITHM."""
    word_freqs = Counter(pre_tokenize(corpus))          # word -> how often it appears
    splits = {w: list(w) for w in word_freqs}           # start: every word = its characters
    merges = []                                          # the ordered rule list we're building

    for step in range(num_merges):
        pairs = count_pairs(splits, word_freqs)
        if not pairs:
            break
        best = max(pairs, key=pairs.get)                # most frequent adjacent pair
        merges.append(best)
        splits = {w: apply_merge(s, best) for w, s in splits.items()}   # apply it everywhere

        if step < verbose_steps:
            top = pairs.most_common(4)
            cands = "   ".join(f"{a+b!r}:{c}" for (a, b), c in top)
            print(f"  step {step:>3}: candidates -> {cands}")
            print(f"            WINNER: {best[0]!r} + {best[1]!r} = {(best[0]+best[1])!r}\n")

    # the vocabulary is: every starting character, plus every merge result
    vocab = sorted({c for w in word_freqs for c in w} | {a + b for a, b in merges})
    return merges, vocab


def encode(text, merges):
    """Apply the merge rules IN PRIORITY ORDER to each word.
    (Equivalent to 'repeatedly apply the highest-priority available rule',
     because a rule can never fire before the rule that created its inputs.)"""
    tokens = []
    for word in pre_tokenize(text):
        symbols = list(word)
        for pair in merges:              # rank order == priority order
            if len(symbols) == 1:
                break
            symbols = apply_merge(symbols, pair)
        tokens.extend(symbols)
    return tokens


def decode(tokens):
    """Glue everything back and turn the delimiter back into a space."""
    return "".join(tokens).replace("Ġ", " ")


# =====================================================================
#  DEMO
# =====================================================================
CORPUS = (
    "the cat sat on the mat the cat ate the rat "
    "the dog sat on the log the dog ate the frog "
    "that is the fact that the cat and the dog are fat "
    "the father of the cat is the other cat that sat there "
)

print("=" * 70)
print("TRAINING — watch the merge list get built")
print("=" * 70)
print(f"corpus: {len(CORPUS.split())} words, {len(set(CORPUS.split()))} unique\n")

merges, vocab = train(CORPUS, num_merges=30, verbose_steps=5)

print("  ... (25 more steps) ...\n")
print("Full merge list, in priority order:")
for i, (a, b) in enumerate(merges):
    print(f"  #{i:<3} {a!r:>8} + {b!r:<8} -> {(a+b)!r}")

print(f"\nResulting vocabulary ({len(vocab)} entries):")
print(" ", vocab)

print("\n" + "=" * 70)
print("ENCODING")
print("=" * 70)
for s in ["the cat sat", "the father", "a zebra sat"]:
    toks = encode(s, merges)
    print(f"  {s!r:<16} -> {toks}")
    print(f"  {'':<16}    {len(toks)} tokens, decode -> {decode(toks)!r}")

print("\n" + "=" * 70)
print("WHAT HAPPENS WITH MORE MERGES?")
print("=" * 70)
for n in [0, 5, 10, 20, 30, 60]:
    m, v = train(CORPUS, num_merges=n, verbose_steps=0)
    t = encode("the father of the cat", m)
    print(f"  {n:>3} merges (vocab {len(v):>3}) -> {len(t):>2} tokens  {t}")
