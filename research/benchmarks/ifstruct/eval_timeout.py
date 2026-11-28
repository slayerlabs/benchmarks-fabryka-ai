"""ifstruct-eval with a request timeout set from the command line, run from the harness checkout by run.sh.

The harness's chat_completion (ifstruct/client.py) waits 120 s per request and has no option for it; only its
default changes here, nothing else in the harness.
Usage: python eval_timeout.py <seconds> <ifstruct-eval arguments>
"""

import sys

from ifstruct import client
from ifstruct.eval import main

client.chat_completion.__kwdefaults__["timeout"] = float(sys.argv[1])
sys.argv = ["ifstruct-eval", *sys.argv[2:]]
main()
