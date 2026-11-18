"""python -m leadengine demo      run the synthetic batch twice, print results, build the site
python -m leadengine run FILE.csv [--hubspot] [--claude]   one batch against a real CRM or real drafts"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .crm import FakeCRM, HubSpotCRM
from .dedupe import load_rows
from .pipeline import ROOT, demo, run


def table(result: dict) -> None:
    print(f"{'lead':<7}{'score':>6}  {'status':<17}{'owner':<10} reason")
    for r in result["results"]:
        reason = r["score"]["disqualified"][0] if r["score"]["disqualified"] else r["route"]["reason"]
        print(f"{r['id']:<7}{r['score']['score']:>6}  {r['status']:<17}{r['route']['owner'] or '-':<10} {reason[:60]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="leadengine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo")
    d.add_argument("--out", default="out")
    d.add_argument("--site", default="site/index.html")
    r = sub.add_parser("run")
    r.add_argument("csv")
    r.add_argument("--hubspot", action="store_true", help="write to HubSpot (needs HUBSPOT_TOKEN)")
    r.add_argument("--claude", action="store_true", help="draft emails with Claude (needs ANTHROPIC_API_KEY)")
    args = ap.parse_args(argv)
    if args.cmd == "demo":
        out = Path(args.out)
        res = demo(out)
        print("lead engine demo: synthetic leads, fake HubSpot, recorded drafts\n")
        table(res["first"])
        print("\nrun 1:", json.dumps(res["first"]["summary"]["crm"]), "| run 2 (same batch):", json.dumps(res["second"]["summary"]["crm"]))
        (out / "report.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
        if args.site:
            from .site import build
            print("site:", build(res, Path(args.site)))
        return 0
    crm = HubSpotCRM() if args.hubspot else FakeCRM(seed=ROOT / "data" / "crm_seed.json", state=Path("out/crm_state.json"))
    drafter = None
    if args.claude:
        from .drafts import ClaudeDrafter
        drafter = ClaudeDrafter()
    res = run(load_rows(Path(args.csv)), crm, drafter=drafter)
    table(res)
    print(json.dumps(res["summary"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
