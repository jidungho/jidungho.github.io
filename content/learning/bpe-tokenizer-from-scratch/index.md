---
title: "Building GPT-2's tokenizer from scratch"
date: 2026-09-22
tags: ["tokenizers", "BPE", "Python", "performance"]
---

Rebuilt GPT-2's byte-level BPE tokenizer in plain Python, as a set of standalone scripts, to see what the `huggingface/tokenizers` library actually has to do. A tokenizer turns out to be a vocab dict and an ordered list of merge rules, and training BPE is four short functions. Matching GPT-2's ids exactly took two more pieces, the pre-tokenizer regex and the bytes-to-unicode map; with both, the output is identical to HuggingFace's on all 338,025 tokens of Tiny Shakespeare. Uncached, the Python version runs at a third of the Rust library's speed. A four-line dict cache keyed on the pre-token makes it 1.6x faster than HF's single-string `encode`, because 95% of pre-tokens are repeats — and that same idea is a 959-line file in the Rust library.

<!--more-->

## A tokenizer is a dict and a list

GPT-2's `tokenizer.json` holds a `vocab` of 50,257 entries (string → id) and a `merges` list of 50,000 pairs. The order of the list is the priority: rule #0 fires before rule #5000. Everything else in the file configures the stages around that model.

## BPE in four functions

Training starts with every word split into characters, then repeats one step: count every adjacent pair across the corpus, weighted by word frequency, merge the most common pair everywhere, and append it to the merge list.

```python
def train(corpus, num_merges):
    word_freqs = Counter(pre_tokenize(corpus))
    splits = {w: list(w) for w in word_freqs}
    merges = []
    for _ in range(num_merges):
        pairs = count_pairs(splits, word_freqs)
        if not pairs:
            break
        best = max(pairs, key=pairs.get)
        merges.append(best)
        splits = {w: apply_merge(s, best) for w, s in splits.items()}
    return merges
```

Encoding a new word applies the recorded merges in the same order. `pre_tokenize` glues each leading space onto the word after it (written `Ġ`), so merges never cross a word boundary.

## Matching GPT-2 exactly

Feeding GPT-2's real merges into that encoder handles plain English, but not much else:

```
'How are you 😁 ?'
   mine : ['How', 'Ġare', 'Ġyou', 'Ġ', '😁', 'Ġ?']
   hf   : ['How', 'Ġare', 'Ġyou', 'ĠðŁĺ', 'ģ', 'Ġ?']
```

GPT-2 merges bytes, not characters. 😁 is four UTF-8 bytes, and the merge list only knows them in byte-level spelling. Two stages were missing:

1. **The pre-tokenizer regex.** It cuts text into chunks that merges may never cross — contractions, runs of letters, runs of digits, punctuation, whitespace — each carrying its leading space. The `\s+(?!\S)` arm hands the last space of a run back to the following word, so `" the"` stays a single chunk.

   ```python
   GPT2_PAT = re.compile(r"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+")
   ```

2. **The bytes-to-unicode map.** A vocab stored as JSON strings can't hold a lone byte like `0xC3`, so each of the 256 bytes gets a printable stand-in character. The 188 printable bytes map to themselves; the other 68 — space, control characters, a few others — shift to codepoints 256–323. That is where `Ġ` comes from: it is byte `0x20`, the space.

With both in place, all 200 test lines produce identical ids, and so does the whole 1.1 MB file.

One more change was needed for speed. Step 2's encoder loops over every merge rule for every word, which is hopeless with 50,000 rules. Step 3 builds a `pair → rank` dict instead, and repeatedly merges whichever adjacent pair in the word has the lowest rank. The output is the same.

## Speed

Measured on the 1.1 MB Tiny Shakespeare file, `tokenizers` 0.21.4. Three runs; all within a few percent.

| Encoder | MB/s |
| --- | ---: |
| Python, as in step 3 | 1.1 |
| HF `encode`, whole file in one call | 3.2 |
| Python + dict cache | 5.1 |
| HF `encode_batch`, 40k lines on 32 cores | 21.3 |

The cache is a dict from pre-token chunk to its ids:

```python
hit = CACHE.get(chunk)
if hit is not None: ids.extend(hit); continue
got = [vocab[s] for s in bpe(to_byte_level(chunk))]
CACHE[chunk] = got; ids.extend(got)
```

It works because real text is Zipfian. The file splits into 297,833 pre-token chunks, but only 15,057 are distinct, so 95% of lookups hit. Ten chunks — `\n`, `,`, `:`, `.`, ` the`, ` to`, ` and`, ` I`, `;`, ` of` — are 34% of the file.

The comparison needs a caveat. HF's `encode` already has its own word cache, and it returns a full `Encoding` — offsets, attention mask, word ids — where the Python version returns only ids. The cache beats one single-threaded call that does more work. Across 32 cores, `encode_batch` is still 4x ahead.

## The same idea, in Rust

The library's v1 rewrite does what that dict does, much more carefully, in [`tk-encode/src/utils/word_cache.rs`](https://github.com/huggingface/tokenizers/blob/main/tokenizers/tk-encode/src/utils/word_cache.rs). It uses a Swiss-table layout with one byte of hash per slot. Words of up to 15 bytes are stored inline as their own key; longer words are compared by a 127-bit hash. The doc comment accepts that two long words could, very rarely, collide and get the wrong ids.

## Files

Each script is standalone; run them in order. They need `pip install tokenizers regex` and network access, since they download GPT-2's `tokenizer.json` and Tiny Shakespeare.

- [step1_look_inside.py](step1_look_inside.py) — what is inside `tokenizer.json`
- [step2_build_bpe.py](step2_build_bpe.py) — train BPE on a toy corpus and watch the merges form
- [step3_match_gpt2.py](step3_match_gpt2.py) — GPT-2's real merges, then the parity check
- [step4a_speed.py](step4a_speed.py) — timing against HF
- [step4b_speed_cached.py](step4b_speed_cached.py) — the same, with the cache
- [regex_explained.py](regex_explained.py) — which regex arm fires for each chunk
- [byte_level_explained.py](byte_level_explained.py) — the byte map, taken apart
