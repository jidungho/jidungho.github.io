---
title: "How big should a vocabulary be?"
date: 2026-09-22T17:00:00
tags: ["tokenizers", "BPE", "training", "scaling"]
series: "Tokenizers from scratch"
part: 3
---

Trained byte-level BPE vocabularies from 512 to 131k entries on 21 MB of Project Gutenberg, and measured each on a book it never saw, *Pride and Prejudice*. Returns shrink fast: the first doubling saves 21% of tokens, going from 16k to 32k saves 3.6%, 32k to 64k saves 1.5%, and asking for 131k only reaches 76k, because the corpus runs out of pairs seen at least twice. Fed into the 6·N·D compute estimate, the curve says the cheapest vocabulary grows with model size — 8–16k at 1B body parameters, 32k at 7–17B, the largest measured from 70B up. Real model families don't choose that way: Llama 2 used 32k at every size, and Llama 3 used 128k at every size, 8B included.

<!--more-->

## The sweep

Training text is 23 Gutenberg books, 21 MB; *Pride and Prejudice* (0.75 MB) is held out. Each vocabulary is byte-level BPE from HF's trainer with `min_frequency=2`, and takes about five seconds to train.

| Asked for | Got | Chars / token | Tokens for the held-out book | Saved vs. previous row |
| ---: | ---: | ---: | ---: | ---: |
| 512 | 512 | 2.07 | 361,137 | |
| 1,024 | 1,024 | 2.63 | 284,760 | 21.1% |
| 2,048 | 2,048 | 3.07 | 243,710 | 14.4% |
| 4,096 | 4,096 | 3.44 | 217,501 | 10.8% |
| 8,192 | 8,192 | 3.80 | 196,865 | 9.5% |
| 16,384 | 16,384 | 4.04 | 185,301 | 5.9% |
| 32,768 | 32,768 | 4.19 | 178,638 | 3.6% |
| 65,536 | 65,536 | 4.25 | 175,924 | 1.5% |
| 131,072 | 76,455 | 4.26 | 175,446 | 0.3% |

## The corpus caps the vocabulary

A merge needs a pair seen at least twice, so a small corpus runs out of merges no matter what size you ask for. Asking for 100k every time:

| Training text | Vocabulary reached | Chars / token, held out |
| ---: | ---: | ---: |
| 0.21 MB | 5,041 | 3.29 |
| 1.05 MB | 14,635 | 3.86 |
| 4.21 MB | 28,345 | 4.08 |
| 10.53 MB | 43,647 | 4.18 |
| 21.05 MB | 76,455 | 4.26 |

## What gets learned, and when

Merge order is a frequency ranking of the training text, and it shows:

- **Rank ~0:** `Ġt`, `he`, `Ġa`, `in`, `Ġthe` — the commonest fragments of English.
- **Rank ~2k:** `ĠVronsky`, next to `Ġsoft` and `Ġfront`. *Anna Karenina* is about 10% of the training text, so its hero earns a slot as early as everyday words.
- **Rank ~8k:** whole words — `Ġdecision`, `Ġdetail`, `Ġnumerous`, `Ġhastened`.
- **Rank ~60k:** `Tower`, `Taught`, `Talked` — capitalized words with no leading space, the spelling a word takes at the start of a line or after a quotation mark. Merges this late buy little: everything from 32k to 76k together saves 1.8% of tokens.

## Domain matters

Characters per token, higher is better:

| Tokenizer | *Pride and Prejudice* | Rust source |
| --- | ---: | ---: |
| Trained on the English books, 32k | 4.19 | 2.55 |
| Trained on the Rust source (reached 7.8k) | 2.74 | 3.75\* |
| GPT-2, 50k, trained on WebText | 3.81 | 2.08 |

\*Measured on its own training text, so flattering. The Rust source is only 0.78 MB, which is also why it stopped at 7,776 entries.

A 32k vocabulary trained on the right kind of text beats GPT-2's 50k by 10% on the novel. GPT-2 does worst of the three on Rust.

## What a bigger vocabulary costs

A bigger vocabulary means a bigger embedding table: with untied input and output embeddings at `d_model` 4096, that is 268M parameters at 32k and 537M at 64k. It also means fewer tokens for the same text, so less compute in the rest of the model. Plugging the curve into compute ≈ 6 × parameters × tokens for a 10¹²-character corpus, relative to the cheapest option for each model size:

| Body parameters | 4k | 8k | 16k | 32k | 64k | 76k |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1B | 1.070 | **1.000** | **1.000** | 1.078 | 1.288 | 1.360 |
| 7B | 1.179 | 1.072 | 1.018 | **1.000** | 1.022 | 1.032 |
| 17B | 1.201 | 1.090 | 1.029 | **1.000** | 1.001 | 1.004 |
| 70B | 1.228 | 1.112 | 1.047 | 1.012 | 1.001 | **1.000** |
| 400B | 1.237 | 1.119 | 1.053 | 1.016 | 1.002 | **1.000** |

Going from 32k to 64k breaks even at 18.5B body parameters. That counts both embedding matrices as full matrix multiplies. The input embedding is a table lookup in practice, and counting only the output projection moves the break-even to about 9B.

Two things temper the result. The optimum is flat — at 17B, 32k and 64k differ by 0.1% — so compute alone barely decides it. And real vocabularies are chosen with more than English prose in mind: Llama 2 used 32k at 7B and at 70B, while Llama 3 moved every size, 8B included, to 128k, adding tokens specifically for non-English text. An English-only experiment can't see that benefit.

## Where glitch tokens live

The last few thousand slots in GPT-2's vocabulary are ordinary words — `ĠProtective`, `Ġcaregivers`, `Congratulations`. The notorious glitch tokens sit mid-vocabulary: `ĠSolidGoldMagikarp` is id 43453, `Ġdavidjl` 23282, `embedreportprint` 30898. Several are Reddit usernames. They were frequent in the text the tokenizer was trained on and nearly absent from the models' training text, so their embeddings got almost no gradient signal.

## Files

- [step7_training.py](step7_training.py) — the vocab-size sweep, corpus-size cap, merge ranks, and domain tables
- [step7b_vocab_economics.py](step7b_vocab_economics.py) — the compute trade-off and the glitch-token check

`step7b` needs only `pip install tokenizers`. `step7_training.py` must run from the root of a [`huggingface/tokenizers`](https://github.com/huggingface/tokenizers) checkout, which supplies the Rust source. It also expects Project Gutenberg plain-text books saved as `learning/data/book_<id>.txt`, for ids 11, 16, 84, 98, 120, 158, 161, 174, 219, 345, 768, 1260, 1342, 1399, 1400, 1661, 1727, 2554, 2600, 2701, 2814, 3207, 4300, and 6130. Book 1342 is held out.
