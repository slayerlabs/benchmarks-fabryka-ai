export interface BenchmarkDefinition {
  id: string;
  name: string;
  purpose: string;
  task: string;
  metrics: string;
  protocol: string;
  dataset: { id: string; revision: string | null; sha256: string | null; access: string; license: string | null };
  code: string;
  evidence: string;
  reproduction: string;
}
const track = "https://github.com/slayerlabs/fabryka-track/blob/73026f45a5350b15e006c15d4341805a73f568e4/";
const docs = track + "docs/leaderboard-benchmarks.md";
export const benchmarkCatalog: readonly BenchmarkDefinition[] = [
  { id: "blimp-en", name: "BLiMP", purpose: "English grammatical minimal-pair discrimination across 67 phenomena.", task: "Sentence-pair likelihood",
    metrics: "Accuracy (%), higher is better; native summary macro-averages subtasks.",
    protocol: "Native Tiny-ML: tiny-ml-en-v2-byte-sliding-aci; lm-eval 0.4.13 task definitions.",
    dataset: { id: "nyu-mll/blimp · all configurations · train", revision: "877fba0801ffb7cbd8c39c1ff314a46f053f6036", sha256: null, access: "Public HF source documented; access not tested here.", license: null },
    code: track + "src/fabryka_track/benchmark_worker.py", evidence: "Track worker and pinned benchmark map reviewed read-only.",
    reproduction: "Use the same model/checkpoint, byte adapter, harness task definitions and dataset revisions. No independent runner is implemented here." },
  { id: "arc-easy-en", name: "ARC-Easy (EN)", purpose: "English elementary science multiple-choice questions.", task: "Zero-shot choice likelihood",
    metrics: "Raw accuracy (%), higher is better; acc_norm is a separate diagnostic.",
    protocol: "Native Tiny-ML: tiny-ml-en-v2-byte-sliding-aci; do not assume parity with historical owner prompts.",
    dataset: { id: "allenai/ai2_arc · ARC-Easy · test", revision: "210d026faf9955653af8916fad021475a3f00453", sha256: null, access: "Public HF source documented; access not tested here.", license: null },
    code: track + "src/fabryka_track/benchmark_worker.py", evidence: "Track worker and pinned benchmark map reviewed read-only.",
    reproduction: "Freeze exact prompts, candidate order, tokenization, checkpoint and lm-eval 0.4.13. This frontend cannot execute the task." },
  { id: "wikitext-en", name: "WikiText-2 byte perplexity", purpose: "English text next-byte prediction; lower perplexity indicates better fit under the stated instrument.", task: "Document likelihood",
    metrics: "Byte-PPL and bits per byte, lower is better.",
    protocol: "Native Tiny-ML byte sliding and wikitext2-v1-lmeval0413-byte-rolling are distinct protocols.",
    dataset: { id: "EleutherAI/wikitext_document_level · wikitext-2-raw-v1 · test (Tiny-ML)", revision: "647234772b9554e208af6c826f23b99e3cac88c8", sha256: null, access: "Public HF source documented; access not tested here.", license: null },
    code: track + "src/fabryka_track/wikitext_suite.py", evidence: "Suite, adapter and document-byte accounting reviewed read-only.",
    reproduction: "Pin split, detokenizer, byte denominator, window policy and document boundaries. Rolling and sliding results must not be relabeled as equivalent." },
  { id: "multiblimp-pl", name: "MultiBLiMP-PL", purpose: "Polish grammatical agreement through minimal sentence pairs.", task: "Sentence-pair likelihood",
    metrics: "Accuracy (%), higher is better; exact ties do not count as correct.",
    protocol: "Native byte sliding differs from prototype space-prefix-sum-loglikelihood-v1 (legacy-v1).",
    dataset: { id: "jumelet/multiblimp · pol/train; prototype uses pol/data.tsv", revision: null, sha256: null, access: "Public HF source documented. Native/prototype revision resolves per job; none is pinned for a result here.", license: null },
    code: track + "src/fabryka_track/benchmark_worker.py", evidence: "Native worker and uploaded multiblimp.py / engine/model.py inspected. Uploaded files have no confirmed Git revision; numerical parity is unverified.",
    reproduction: "Retain the actual dataset revision, checksum, parsed pair order, tokenizer and context policy. A current repository name is not a frozen evaluation input." },
  { id: "arc-easy-pl", name: "ARC-Easy-PL", purpose: "Polish science questions, with EU20 as the primary translation and ddudek as a separate control.", task: "Full-text likelihood difference",
    metrics: "EU20 and ddudek accuracy (%), higher is better; no combined translation score.",
    protocol: "Prototype glint-eu20-ddudek-v1: LL(q+' '+a) − LL(q), raw argmax, first tie, 256-token crop. Equivalence remains unverified.",
    dataset: { id: "Eurolingua/arcx · arc_easy_PL_test.jsonl (EU20)", revision: "f2e35fbebdb572a9653eda706b00083b0892ed43", sha256: "c6732eeba3b2f3cfda95d65d42fb9d4e0f10edc1b9e6c8582d46c069b6706186", access: "Pinned public source in uploaded scorer. ddudek control: ddudek/ai2_arc_translated_pol @ e61110df4097ca5f5284a62e60d01d8f80d15069.", license: null },
    code: "https://github.com/slayerlabs/Probierz/tree/47cee070f47fab4b52f144daf0531419d7dd0072/benchmarks/zewnetrzne/arc-easy-pl",
    evidence: "Uploaded arc_easy_pl.py inspected; pinned external scorer is a documented reference, not executed or independently verified here.",
    reproduction: "Follow the pinned scorer instructions; retain both data hashes, tokenizer postprocessing, dtype, model revision and truncation behavior. See the calibration reference before claiming parity." },
  { id: "w-pl", name: "Polish W byte perplexity", purpose: "Language-model likelihood on the frozen Polish Wikipedia W selection.", task: "Reset-window text likelihood",
    metrics: "Byte-PPL and BPB, lower is better; training-data overlap must be disclosed.",
    protocol: "Historical owner W instrument, documented standalone scorer at Probierz 2af7b868; not the native PL automatic path.",
    dataset: { id: "SlayerLab/fabryka-track-w-pl · w_final.jsonl · 463 articles", revision: "b25c13a445ba8639759264654f37295ebe08871c", sha256: "234e7ec21bf2236bc74425591531f2c4772f8c49ff853d57f6fa16f33ee90ac7", access: "Published as an evaluation set on 2026-10-25 according to Track documentation; public availability is not proof of held-out training data.", license: "CC BY-SA 4.0 per the pinned dataset documentation; retain attribution." },
    code: "https://github.com/slayerlabs/Probierz/tree/2af7b8688452964a10e1cc2251a3787e32ce45fa/benchmarks/zewnetrzne/byte-ppl-w-pl",
    evidence: "Pinned Track methodology reviewed; external scorer linked by that documentation was not run here.",
    reproduction: "Follow pinned W instructions: distinguish file bytes, joined text bytes, all tokens and predicted targets. Retain its model-specific calibration and window contract." },
  { id: "aci", name: "Attention Clarity Index (ACI)", purpose: "Attention-gradient saliency alignment with relevant and distractor spans.", task: "Gradient-times-attention analysis",
    metrics: "ACI (0–100), higher is better; valid coverage gates native Tiny-ML eligibility, not its average score.",
    protocol: "native-byte-eager-attention-gradient-v1; ACI-Bench reference revision pinned with the data.",
    dataset: { id: "AxiomicLabs/ACI-Bench · test/test-00000-of-00001.parquet", revision: "eaf77566763d6a924692d011499908cf05201941", sha256: "76d892d2c3295af87f4bbfef50344901b5f3526f4efee7dcc75b9c1aab5e04d8", access: "Pinned HF source documented; Track per-item results are private. Public dataset access and result publication are different policies.", license: null },
    code: track + "src/fabryka_track/aci_suite.py", evidence: "Pinned implementation/source metadata reviewed; no evaluation performed.",
    reproduction: "Requires the reviewed eager model adapter, gradients, byte-span mapping, context and coverage accounting. It is not ordinary forward-only accuracy." },
];
export const evaluationSuiteCatalog = [
  { id: "tiny-ml-en-v2-byte-sliding-aci", name: "Native Tiny-ML EN", components: ["blimp-en", "arc-easy-en", "wikitext-en", "aci"], note: "Historical Track suite. Three-axis scoring plus ACI eligibility; not an executable service in this app.", reference: track + "src/fabryka_track/tiny_ml_suite.py" },
  { id: "all-v1", name: "Prototype PL benchmark bundle", components: ["multiblimp-pl", "arc-easy-pl"], note: "Uploaded registry runs these sequentially and retains separate results. It does not calculate a new composite. Test/registry snapshot mismatch remains unresolved.", reference: docs },
] as const;
export const benchmarkMapReference = docs;
