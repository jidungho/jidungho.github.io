"""
The GPT-2 pre-tokenizer regex, taken apart.

Same pattern as step3, but each alternative is a NAMED GROUP, so we can print
which one actually fired for every chunk.
"""
import regex as re     # NOT stdlib `re` -- stdlib has no \p{L} / \p{N}

ARMS = [
    ("contraction", r"'s|'t|'re|'ve|'m|'ll|'d"),   # 1
    ("letters",     r" ?\p{L}+"),                  # 2
    ("digits",      r" ?\p{N}+"),                  # 3
    ("punct",       r" ?[^\s\p{L}\p{N}]+"),        # 4
    ("ws_giveback", r"\s+(?!\S)"),                 # 5
    ("ws_rest",     r"\s+"),                       # 6
]
PAT = re.compile("|".join(f"(?P<{n}>{p})" for n, p in ARMS))

def show(text):
    print(f"\n  {text!r}")
    for m in PAT.finditer(text):
        print(f"      {m.group()!r:<14} <- arm {[a for a,_ in ARMS].index(m.lastgroup)+1}: {m.lastgroup}")

print("=" * 66)
print("ARM BY ARM")
print("=" * 66)
for t in ["hello",  "  hello", "it's", "It'S", "12.50", "x=1", '"quoted"']:
    show(t)

print("\n" + "=" * 66)
print("THE TRICKY ONE: \\s+(?!\\S)  -- 'give the last space back'")
print("=" * 66)
for t in ["a  b", "a   b", "a  ", "a\n\nb", "a\tb"]:
    show(t)

print("\n" + "=" * 66)
print("WHY IT MATTERS: the space belongs to the word AFTER it")
print("=" * 66)
for t in ["the cat", "  the cat"]:
    chunks = [m.group() for m in PAT.finditer(t)]
    print(f"  {t!r:<14} -> {chunks}")
print("\n  ' the' is ONE chunk, so BPE can learn the single token 'Gthe'.")
print("  Split the other way ('the ') and word-initial 'the' would be")
print("  indistinguishable from mid-word 'the'.")
