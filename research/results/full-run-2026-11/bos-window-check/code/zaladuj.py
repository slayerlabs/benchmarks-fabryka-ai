"""Zaladowanie modelu na karcie przed kolejka: float32, jeden forward. python zaladuj.py SCIEZKA ETYKIETA. Kod 0 = dziala."""
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sciezka, etykieta = sys.argv[1], sys.argv[2]
tok = AutoTokenizer.from_pretrained(sciezka)
m = AutoModelForCausalLM.from_pretrained(sciezka, torch_dtype=torch.float32).to("cuda").eval()
ids = tok("The capital of France is", return_tensors="pt").input_ids.to("cuda")
with torch.no_grad():
    w = m(ids).logits[0, -1]
print(etykieta, "OK", "dtype", next(m.parameters()).dtype, "parametry", sum(p.numel() for p in m.parameters()),
      "nastepny token", repr(tok.decode(int(w.argmax()))), "bos", tok.bos_token_id,
      "vram_mib", torch.cuda.max_memory_allocated() // 2**20, flush=True)
