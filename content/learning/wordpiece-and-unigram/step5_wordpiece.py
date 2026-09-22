"""
Step 5: WordPiece (BERT). A second algorithm, ~15 lines.

BPE builds UP from characters by applying learned merges.
WordPiece eats DOWN from the left, always taking the longest piece in the vocab.
"""
from tokenizers import Tokenizer

hf = Tokenizer.from_pretrained("bert-base-uncased")
VOCAB = hf.get_vocab()

# =====================================================================
#  THE ALGORITHM -- greedy longest-match-first
# =====================================================================
def wordpiece(word, vocab, unk="[UNK]", max_chars=100):
    if len(word) > max_chars:
        return [unk]
    tokens, start = [], 0
    while start < len(word):
        end = len(word)
        piece = None
        while start < end:                       # try longest first, shrink
            sub = word[start:end]
            if start > 0:
                sub = "##" + sub                 # '##' marks 'not word-initial'
            if sub in vocab:
                piece = sub
                break
            end -= 1
        if piece is None:
            return [unk]          # NOTE: one failure and the WHOLE word is UNK
        tokens.append(piece)
        start = end
    return tokens

def encode(text):
    """stages 1-2 from HF (not what we're studying), stage 3 is ours."""
    norm = hf.normalizer.normalize_str(text)
    return [t for w, _ in hf.pre_tokenizer.pre_tokenize_str(norm)
              for t in wordpiece(w, VOCAB)]

# =====================================================================
print("=" * 72); print("WATCH IT EAT LEFT TO RIGHT"); print("=" * 72)
def trace(word):
    print(f"\n  {word!r}")
    start = 0
    while start < len(word):
        end = len(word)
        while start < end:
            sub = word[start:end]
            disp = ("##" + sub) if start > 0 else sub
            if disp in VOCAB:
                print(f"      take {disp!r:<14} (longest match from position {start})")
                break
            end -= 1
        else:
            print("      no match -> whole word becomes [UNK]"); return
        start = end
for w in ["playing", "unbelievable", "tokenization", "hugging"]:
    trace(w)

print("\n" + "=" * 72); print("PARITY WITH HUGGINGFACE"); print("=" * 72)
TESTS = ["the cat sat on the mat", "unbelievable tokenization results",
         "playing embeddings antidisestablishmentarianism", "COVID-19 vaccine efficacy"]
for t in TESTS:
    mine, theirs = encode(t), hf.encode(t, add_special_tokens=False).tokens
    print(f"  {'MATCH' if mine == theirs else 'DIFFERS'}  {t!r}")
    print(f"           {mine}")

import urllib.request
lines = [l for l in urllib.request.urlopen(
    "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
).read().decode().split("\n") if l.strip()][:200]
bad = sum(1 for l in lines if encode(l) != hf.encode(l, add_special_tokens=False).tokens)
print(f"\n  200 lines of Shakespeare -> {bad} mismatches")

print("\n" + "=" * 72); print("THE ALL-OR-NOTHING UNK"); print("=" * 72)
for w in ["hello", "hellooooo", "日本語", "🎉"]:
    print(f"  {w!r:<12} -> {wordpiece(w, VOCAB)}")
print("  BPE would degrade gracefully into pieces. WordPiece throws the word away.")

print("\n" + "=" * 72); print("BPE vs WORDPIECE ON THE SAME WORDS"); print("=" * 72)
gpt2 = Tokenizer.from_pretrained("gpt2")
print(f"  {'word':<22}{'WordPiece (BERT)':<40}{'BPE (GPT-2)'}")
for w in ["unbelievable", "tokenization", "antidisestablishmentarianism", "hugging"]:
    wp = wordpiece(w, VOCAB)
    bp = gpt2.encode(w, add_special_tokens=False).tokens
    print(f"  {w:<22}{str(wp):<40}{bp}")
