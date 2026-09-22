import json, time, urllib.request, regex as re
from tokenizers import Tokenizer
raw    = json.load(urllib.request.urlopen("https://huggingface.co/gpt2/resolve/main/tokenizer.json"))
vocab  = raw["model"]["vocab"]
RANKS  = {tuple(m) if isinstance(m,list) else tuple(m.split(" ")): i for i,m in enumerate(raw["model"]["merges"])}
hf     = Tokenizer.from_pretrained("gpt2")
def apply_merge(s,p):
    a,b=p; out,i=[],0
    while i<len(s):
        if i<len(s)-1 and s[i]==a and s[i+1]==b: out.append(a+b); i+=2
        else: out.append(s[i]); i+=1
    return out
def bpe(w):
    s=list(w)
    while len(s)>1:
        best,br=None,None
        for i in range(len(s)-1):
            r=RANKS.get((s[i],s[i+1]))
            if r is not None and (br is None or r<br): best,br=(s[i],s[i+1]),r
        if best is None: break
        s=apply_merge(s,best)
    return s
def b2u():
    bs=list(range(33,127))+list(range(161,173))+list(range(174,256)); cs=bs[:]; n=0
    for b in range(256):
        if b not in bs: bs.append(b); cs.append(256+n); n+=1
    return dict(zip(bs,(chr(c) for c in cs)))
B2U=b2u()
PAT=re.compile(r"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+")
def enc(t):
    ids=[]
    for c in PAT.findall(t):
        for s in bpe("".join(B2U[b] for b in c.encode())): ids.append(vocab[s])
    return ids
text=urllib.request.urlopen("https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt").read().decode()
print(f"corpus: {len(text.encode())/1e6:.2f} MB")
t0=time.perf_counter(); a=enc(text); tm=time.perf_counter()-t0
t0=time.perf_counter(); b=hf.encode(text, add_special_tokens=False).ids; th=time.perf_counter()-t0
n=len(text.encode())
print(f"identical output: {a==b}   ({len(a):,} tokens)")
print(f"yours (Python): {tm:7.2f} s   {n/tm/1e6:7.2f} MB/s")
print(f"HF    (Rust)  : {th:7.2f} s   {n/th/1e6:7.2f} MB/s")
print(f"speedup: {tm/th:.0f}x")
