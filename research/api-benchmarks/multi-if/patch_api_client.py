"""Two minimal edits to Multi-IF's api_client.py (facebookresearch/Multi-IF @ 1cdb53ed), applied by run.sh:

1. The Anthropic, Gemini and Mistral client libraries are imported inside their own backends instead of at module
   top. Our models use only the OpenAI-compatible backend, and the Gemini and Mistral packages conflict with the
   vLLM environment; no backend's behaviour changes.
2. "bielik" and "slayer" are added to the list of model names served by the OpenAI-compatible backend (OpenAIBot), next
   to 'gpt-4o-2024-08-06'; without this the harness stops with "The model ... is not supported yet".

Every edit must match its pattern exactly once, or the script stops. Running it twice changes nothing.
Usage: python patch_api_client.py <path to api_client.py>
"""

import sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
EDITS = [
    (
        "import anthropic\nimport google.generativeai as genai\nfrom google.generativeai.types import HarmCategory, HarmBlockThreshold\n"
        "from mistralai import Mistral\n",
        "",
    ),
    (
        "        self.client = anthropic.Anthropic()\n",
        "        import anthropic\n        self.client = anthropic.Anthropic()\n",
    ),
    (
        "        genai.configure(api_key=os.environ['GEMINI_API_KEY'])\n",
        "        import google.generativeai as genai\n        genai.configure(api_key=os.environ['GEMINI_API_KEY'])\n",
    ),
    (
        "        chat =  self.model.start_chat(history=history)\n",
        "        from google.generativeai.types import HarmCategory, HarmBlockThreshold\n"
        "        chat =  self.model.start_chat(history=history)\n",
    ),
    (
        "        self.client = Mistral(api_key=api_key)\n",
        "        from mistralai import Mistral\n        self.client = Mistral(api_key=api_key)\n",
    ),
    ("'gpt-4o-2024-08-06'\n", "'gpt-4o-2024-08-06', 'bielik', 'slayer'\n"),
]
if "'bielik', 'slayer'" not in s:
    for old, new in EDITS:
        if s.count(old) != 1:
            sys.exit(f"patch_api_client.py: pattern found {s.count(old)} times: {old[:40]!r}")
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8", newline="\n").write(s)
print("patch_api_client.py: OK")
