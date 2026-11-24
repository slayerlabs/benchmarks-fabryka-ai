# HLE (no tools) protocol decisions

## Subset

- **Decision:** Use the **text-only subset** of `cais/hle` `test` split: questions where `image` is empty/null.
- **Reason:** LFM3-1.7B is a text-only model. The reference score in issue #303 / LFM3-1.7B model card is for HLE (no tools); evaluating image questions through a text-only API is not equivalent to multimodal evaluation and may fail due to image payload handling. We make an explicit decision rather than silently shrinking.
- **Counts:** Full test split = 2,500 questions. Text-only = 2,158. Image = 342 (per NeMo Gym HLE README; confirm in run log).
- **Reporting:** Excluded image questions are reported/counted, not scored as zero. The chosen subset and counts are written in `README.md` and result metadata.

## Max output tokens

- **Decision:** `max_completion_tokens=8192` for all models.
- **Reason:** Official HLE README recommends not setting below 8192 for reasoning models and uses 8192 in examples. LFM3 card states "no output limit other than context length" generally; we record 8192 as an explicit, uniform deviation.

## Sampling

- `temperature=0.6`, `top_p=0.95`, single trial - from LFM3-1.7B card "Evaluation details" general default (HLE not listed as exception).

## Judge

- Official HLE judge: `o3-mini-2025-01-31`, `max_completion_tokens=4096`, 1 call/question. **Pending #bench-team access. No substitution.**

## Slayer 1B (opisowy / descriptive, prepared, not run)

- **Status:** Slayer 1B jest raportowany **opisowo** (descriptive), nie jako główny wynik porównywalny 1:1 z modelami instrukcyjnymi pod protokołem HLE. To model bazowy, bez dostrajania instrukcyjnego.
- **Odstępstwa od protokołu HLE (zapisane przed generacją):**
  - model bazowy, bez szablonu czatu (plain prompt: `SYSTEM_PROMPT + "\n\n" + question`, jak w `predict_slayer.py`);
  - okno kontekstu 4096 tokenów;
  - greedy decoding, `bf16`, batch, zamiast `temperature=0.6, top_p=0.95` — Slayer nie obsługuje losowania;
  - jedna reguła BOS jak w IFEval/SlayerLM (dokładnie jeden wiodący BOS na żądanie; obsłużone w `research/common/slayer_batch.py`);
  - tokenizer v6 (SHA `0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd`).
- **Ścieżka generacji:** lokalnie z wag przez `research/common/slayer_lm.py` / `research/common/slayer_batch.py` (te same co w SciCode, skopiowane z `research/scicode-slayer` @ `9c91a3a`), `predict_slayer.py`, `max_new_tokens = 4096 − prompt_tokens`.
- **Przepełnienie kontekstu (bez cięcia, reguła 8):** prompt tokens policzone tokenizerem Slayer v6 na podzbiorze text-only (2,158 pytań, `cais/hle` test @ `5a81a4c7271a2a2a312b9a690f0c2fde837e4c29`): **9/2158 (0.42%)** ma `prompt_tokens > 3840` (zostawia < 256 tokenów na odpowiedź). Te 9 pytań otrzymuje pustą odpowiedź z `slayer_unsupported=true` i jest liczonych jako złe w mianowniku. Lista ID (9): `672cba8ce9bdca604f9e0c12`, `672ce1d6ce33946794b97a88`, `66edd857a0ffa4c025458242`, `6720241e20239af7af582ae1`, `66ea12d21684c1846037a28d`, `673f2753312f953d9f7fc051`, `6725a933e10373a976b7e2a2`, `6736ecc681dc32f504545aae`, `67228ecf93273f2ea4d39e3e`.
- Przed pierwszym lokalnym uruchomieniem Slayera: stop i pytanie do właściciela (zasada ciężkich procesów na laptopie).
