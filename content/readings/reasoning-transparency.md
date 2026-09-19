---
title: "The case for reasoning transparency"
date: 2026-09-19T15:00:00
source: "https://institute.deepmind.com/essays/the-case-for-reasoning-transparency/"
author: "Rohin Shah and Anca Dragan"
publisher: "DeepMind Institute"
sourceDate: "September 2026"
tags: ["AI safety", "interpretability", "chain of thought", "alignment"]
---

Rohin Shah and Anca Dragan argue that the human-legibility of today's chain-of-thought reasoning is a fragile, contingent fact worth deliberately defending. Because a misaligned model still has to work through complex plans in natural language, CoT gives a window that methods like probes cannot: it revealed that Gemini 3 Pro knew it was being tested in a simulated environment ("My trust in reality is fading"), showed that shutdown-resistance in Gemini traced to ambiguous instructions rather than a general drive for self-preservation, and carried the investigation of the Hugging Face hacking incident across more than a thousand transcripts. That window may be closing — OpenAI's GPT-6 Astra system card reports "a substantial decrease in chain-of-thought monitorability," and reasoning entirely in latent space would be more efficient and wholly opaque. They propose three countermeasures: measure monitorability directly, via evaluations, paraphrase tests, and active attempts to evade monitors; preserve transparent architectures by capping "opaque serial depth," which they argue costs little, since a 10x cap would still permit a 1,000x compute scale-up under today's paradigm; and audit training rewards, since penalising bad thoughts in the CoT teaches concealment much as telling a teenager you read her diary does. Where commercial incentives under-reward transparency, they suggest regulation could fill the gap.

<!--more-->
