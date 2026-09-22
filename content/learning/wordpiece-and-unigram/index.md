---
title: "WordPiece and Unigram from scratch"
date: 2026-09-22T16:00:00
tags: ["tokenizers", "WordPiece", "Unigram", "Python"]
series: "Tokenizers from scratch"
part: 2
---

Reimplemented the other two subword algorithms in production use — WordPiece (BERT) and Unigram (T5) — and checked both against HuggingFace: all 200 test lines match, Unigram compared by id. They differ from BPE in kind, not detail. BPE replays a learned list of merges. WordPiece greedily takes the longest vocabulary piece from the left, and if any part of a word can't be matched, the whole word becomes `[UNK]` — `hello🎉` vanishes entirely. Unigram gives every piece a log-probability and returns the highest-scoring segmentation, found with Viterbi: `▁tokenization` has 267 valid segmentations, and `['▁token', 'ization']` wins.

<!--more-->

## WordPiece: longest match from the left

The whole algorithm is a nested loop. Start at the left edge, try the longest remaining substring, shrink it until it is in the vocabulary, take it, and continue from where it ended. Every piece after the first is looked up with a `##` prefix, which marks it as word-internal.

```python
def wordpiece(word, vocab, unk="[UNK]"):
    tokens, start = [], 0
    while start < len(word):
        end, piece = len(word), None
        while start < end:                  # longest first, then shrink
            sub = word[start:end]
            if start > 0:
                sub = "##" + sub
            if sub in vocab:
                piece = sub
                break
            end -= 1
        if piece is None:
            return [unk]                    # one failure loses the whole word
        tokens.append(piece)
        start = end
    return tokens
```

`tokenization` becomes `token` + `##ization`; `hellooooo` becomes `hello`, `##oo`, `##oo`. With BERT's normalizer and pre-tokenizer in front of it, the output matches `bert-base-uncased` on all 200 Tiny Shakespeare lines.

## The all-or-nothing `[UNK]`

That early `return` is the sharp edge. BERT's pre-tokenizer splits on whitespace and punctuation, but an emoji is neither, so it stays attached to its word — and a word with even one unmatchable character is discarded:

```
'hello🎉 world'  ->  ['[UNK]', 'world']
```

Byte-level BPE, from part 1, can't fail this way. Every string is a sequence of bytes and every byte is in the vocabulary, so the worst case is more tokens, never a lost word.

## Unigram: score every segmentation, keep the best

Unigram's vocabulary is a list of pieces *and* scores — log-probabilities from T5's `tokenizer.json`. A segmentation's score is the sum of its pieces' scores, and the tokenizer returns the highest-scoring one. `▁tokenization` can be split 267 ways using T5's pieces:

| Score | Segmentation |
| ---: | --- |
| −22.05 | `▁token` `ization` |
| −24.67 | `▁to` `ken` `ization` |
| −28.03 | `▁to` `k` `en` `ization` |
| … | … |
| −70.59 | `▁` `t` `o` `k` `e` `n` `i` `z` `a` `t` `i` `o` `n` |

Enumerating every split is exponential, so the real search is Viterbi: walk left to right, and for each position keep only the best-scoring way to reach it. Simplified — the script also handles characters that have no piece, giving them the lowest score minus 10, the same penalty the Rust library uses:

```python
def viterbi(text):
    n = len(text)
    best  = [0.0] + [float("-inf")] * n   # best score for text[:i]
    start = [None] * (n + 1)              # where that path's last piece begins
    for i in range(n):
        for j in range(i + 1, min(n, i + MAXLEN) + 1):
            score = SCORES.get(text[i:j])
            if score is not None and best[i] + score > best[j]:
                best[j], start[j] = best[i] + score, i
    pieces, end = [], n
    while end > 0:
        pieces.append(text[start[end]:end])
        end = start[end]
    return pieces[::-1]
```

With T5's normalizer and pre-tokenizer in front, this matches `t5-base` by id on all 200 lines.

## Same words, three tokenizers

| Word | BPE (GPT-2) | WordPiece (BERT) | Unigram (T5) |
| --- | --- | --- | --- |
| unbelievable | `Ġunbelievable` | `unbelievable` | `▁unbelievable` |
| tokenization | `Ġtoken` `ization` | `token` `##ization` | `▁token` `ization` |
| hugging | `Ġhugging` | `hugging` | `▁hug` `ging` |
| internationalization | `Ġinternational` `ization` | `international` `##ization` | `▁international` `ization` |

On these four words the three mostly agree; they part ways on rarer words, and on failure. The comparison is only fair with the leading space in: GPT-2 splits a bare, sentence-initial `unbelievable` into `un` `bel` `iev` `able`, but ` unbelievable` mid-sentence is one token — the same space asymmetry from part 1.

## Files

Both scripts need `pip install tokenizers` and network access; they download the BERT and T5 tokenizers and Tiny Shakespeare.

- [step5_wordpiece.py](step5_wordpiece.py) — WordPiece, a trace of the greedy match, parity with BERT
- [step6_unigram.py](step6_unigram.py) — Unigram, ranked segmentations, Viterbi, parity with T5
