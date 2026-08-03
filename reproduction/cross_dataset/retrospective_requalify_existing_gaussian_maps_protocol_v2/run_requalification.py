from __future__ import annotations
import argparse
from requalification_core import classify, manifest, run_all_evidence

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("evidence", "classify", "finalize", "all"), default="all")
    args = parser.parse_args()
    if args.phase in ("evidence", "all"):
        run_all_evidence()
    if args.phase in ("classify", "all"):
        classify()
    if args.phase in ("finalize", "all"):
        from generate_figures import main as figures
        from build_report import main as report
        figures(); report(); manifest()
    print("REQUALIFICATION_PHASE_COMPLETE", args.phase)

if __name__ == "__main__": main()
