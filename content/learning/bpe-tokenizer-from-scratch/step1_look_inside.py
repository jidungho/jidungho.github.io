"""Step 1: A tokenizer is a FILE. Let's look inside it."""
import json, urllib.request

url = "https://huggingface.co/gpt2/resolve/main/tokenizer.json"
raw = json.load(urllib.request.urlopen(url))

print("Top-level keys in gpt2's tokenizer.json:")
for k in raw: print("   ", k)

vocab  = raw["model"]["vocab"]     # dict: string -> id
merges = raw["model"]["merges"]    # list of string pairs, IN ORDER

print(f"\nvocab  : {len(vocab):,} entries   (a dict, string -> int)")
print(f"merges : {len(merges):,} rules      (a LIST -- order matters)")

print("\n--- first 12 vocab entries (ids 0-11) ---")
inv = {v: k for k, v in vocab.items()}
for i in range(12): print(f"   {i:>5} : {inv[i]!r}")

print("\n--- some entries in the middle ---")
for i in [262, 995, 15496, 50256]: print(f"   {i:>5} : {inv[i]!r}")

print("\n--- the first 10 merge rules (highest priority first) ---")
for i, m in enumerate(merges[:10]):
    a, b = m if isinstance(m, list) else m.split(" ")
    print(f"   #{i:<3} {a!r} + {b!r}  ->  {a+b!r}")

print("\n--- merge rules 5000-5004 (learned later, so lower priority) ---")
for i in range(5000, 5005):
    a, b = merges[i] if isinstance(merges[i], list) else merges[i].split(" ")
    print(f"   #{i:<5} {a!r} + {b!r}  ->  {a+b!r}")
