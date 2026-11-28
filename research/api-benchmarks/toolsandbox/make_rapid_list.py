"""Rebuilds rapid_api_scenarios.txt and rapid_api_kept_bases.txt from the pinned ToolSandbox harness.

python make_rapid_list.py            # check: rebuild and compare with the committed files, exit 1 on a difference
python make_rapid_list.py --write    # (re)write both files

Run it with the harness venv that run.sh builds (`.venv/bin/python make_rapid_list.py`); no network, no API key.

Rule. A base scenario (the scenario of the NO_DISTRACTION_TOOLS category) whose `tool_allow_list` contains one of the
five tools that call RapidAPI (`search_lat_lon`, `search_location_around_lat_lon`, `search_weather_around_lat_lon`,
`search_stock`, `convert_currency`) needs `RAPID_API_KEY` to be answered, except the `*_insufficient_information*`
scenarios, which have no milestones (the agent must not do something) and stay in the evaluated set. All 8 variants of
a base scenario are excluded together (variants add distraction tools or scramble text, they do not change the base's
allow-list). `rapid_api_kept_bases.txt` lists the kept bases with the tool their minefield forbids and whether that
tool is itself a RapidAPI tool.
"""
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
from tool_sandbox.common.tool_discovery import ToolBackend
from tool_sandbox.scenarios import named_scenarios

HERE = Path(__file__).resolve().parent
RAPID = {"search_lat_lon", "search_location_around_lat_lon", "search_weather_around_lat_lon", "search_stock",
         "convert_currency"}
SUFFIXES = ["_3_distraction_tools_arg_description_scrambled", "_3_distraction_tools_arg_type_scrambled",
            "_3_distraction_tools_tool_description_scrambled", "_3_distraction_tools_tool_name_scrambled",
            "_10_distraction_tools", "_3_distraction_tools", "_all_tools"]


def base_of(name):
    for s in SUFFIXES:
        if name.endswith(s):
            return name[: -len(s)]
    return name


def build():
    scen = named_scenarios(preferred_tool_backend=ToolBackend.DEFAULT)
    groups = {}
    for n in scen:
        groups.setdefault(base_of(n), []).append(n)
    assert len(scen) == 1032 and all(len(v) == 8 for v in groups.values()) and len(groups) == 129
    excluded, kept = [], []
    for b, members in sorted(groups.items()):
        allow = set(scen[b].starting_context.tool_allow_list or []) & RAPID
        if not allow:
            continue
        if "insufficient_information" not in b:
            excluded += members
            continue
        mine = []
        for node in scen[b].evaluation.minefield_matcher.milestones:
            for sc in node.snapshot_constraints:
                mine += [d["content"] for d in sc.target_dataframe.to_dicts()]
        assert len(mine) == 1, (b, mine)
        kept.append((b, mine[0], "yes" if mine[0] in RAPID else "no"))
    assert all(len(scen[b].evaluation.milestone_matcher.milestones) == 0 for b, _, _ in kept)
    return sorted(excluded), kept


def main():
    excluded, kept = build()
    ex_txt = "\n".join(excluded) + "\n"
    kept_txt = "# base scenario <TAB> tool its minefield forbids <TAB> that tool is a RapidAPI tool\n" + "".join(
        f"{b}\t{t}\t{r}\n" for b, t, r in kept)
    if "--write" in sys.argv:
        (HERE / "rapid_api_scenarios.txt").write_text(ex_txt)
        (HERE / "rapid_api_kept_bases.txt").write_text(kept_txt)
        print(f"wrote {len(excluded)} excluded scenarios and {len(kept)} kept bases")
        return 0
    ok = (HERE / "rapid_api_scenarios.txt").read_text() == ex_txt and (HERE / "rapid_api_kept_bases.txt").read_text() == kept_txt
    print(f"{len(excluded)} excluded ({len(excluded) // 8} bases x 8), {len(kept)} kept bases: "
          + ("matches the committed files" if ok else "DIFFERS from the committed files"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
