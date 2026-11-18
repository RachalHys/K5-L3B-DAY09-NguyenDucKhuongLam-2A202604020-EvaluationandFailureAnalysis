"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
from statistics import mean

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item
from lab9.graders import GRADERS


def _finite_score(value) -> bool:
    return isinstance(value, int) or (isinstance(value, float) and isfinite(value))


def _gate_rules(spec: dict) -> dict[str, dict]:
    rules = {m["id"]: {**m.get("threshold", {}), "blocking": m.get("blocking")}
             for m in spec["metrics"]}
    rules.update({f"slice:{s['name']}/{s['metric']}": s for s in spec.get("slices", [])})
    return rules


def _ratchet_problems(spec: dict, base_spec: dict) -> list[str]:
    current = _gate_rules(spec)
    problems = []
    for name, previous in _gate_rules(base_spec).items():
        if name not in current:
            problems.append(f"ratchet: removed {name}")
            continue
        updated = current[name]
        for bound in ("min", "max", "max_increase"):
            if bound not in previous:
                continue
            old, new = previous[bound], updated.get(bound)
            if not _finite_score(new) or (new < old if bound == "min" else new > old):
                problems.append(f"ratchet: {name} {bound} weakened ({old} -> {new})")
        for flag in ("blocking", "no_significant_drop"):
            if previous.get(flag) and not updated.get(flag):
                problems.append(f"ratchet: {name} disabled {flag}")
    return problems


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """Validate trial coverage, grader results and same-version rules before scoring."""
    problems = [f"metric {name} must be finite" for name, value in pr["metrics"].items()
                if value is not None and not _finite_score(value)]
    if pr.get("evaluator_failures"):
        problems.append(f"evaluator_failures: {len(pr['evaluator_failures'])}")

    rows, manifest = pr["rows"], pr["manifest"]
    seeds = set(manifest["seeds"])
    expected = manifest["items"] * len(manifest["seeds"])
    if len(rows) != expected:
        problems.append(f"expected {expected} trial rows, got {len(rows)}")
    trial_keys = {(r["item_id"], r["seed"]) for r in rows}
    if len(trial_keys) != len(rows):
        problems.append("duplicate (item_id, seed) rows")
    if (len(seeds) != len(manifest["seeds"]) or {seed for _, seed in trial_keys} != seeds
            or len({item for item, _ in trial_keys}) != manifest["items"]):
        problems.append("trial items or seeds differ from the manifest")

    base_slices = {(r["item_id"], r["seed"]): set(r.get("slices") or []) for r in base["rows"]}
    if trial_keys != base_slices.keys():
        problems.append("(item_id, seed) pairs differ from the baseline")
    else:
        for row in rows:
            item, seed = row["item_id"], row["seed"]
            if set(row.get("slices") or []) != base_slices[item, seed]:
                problems.append(f"slice tags differ from the baseline at {item}@{seed}")
                break

    for metric in spec["metrics"]:
        name = metric["id"]
        if name not in GRADERS:
            continue
        for row in rows:
            if not _finite_score(row.get(name)):
                problems.append(f"missing or invalid grader result for {name} at {row['item_id']}@{row['seed']}")
                break

    if base_spec is not None and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        problems.extend(_ratchet_problems(spec, base_spec))
    return problems


def _paired_change(current: dict, baseline: dict, bootstrap: dict) -> tuple[float, str]:
    keys = sorted(current.keys() & baseline.keys())
    delta, lo, hi = stats.paired_bootstrap(
        [current[k] for k in keys], [baseline[k] for k in keys],
        n_resamples=bootstrap.get("n_resamples", 1000), rng=bootstrap.get("rng", 2027),
        confidence=bootstrap.get("confidence", 0.95),
    )
    return hi, f"Δ {delta:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        key = f"slice:{name}/{metric}"
        current = per_item(pr, metric, slice_name=name)
        value = mean(current.values()) if current else None
        failed = value is None or ("min" in rule and value < rule["min"])
        detail = "missing" if value is None else f"{value:.4f}"
        if rule.get("no_significant_drop") and current:
            baseline = per_item(base, metric, slice_name=name)
            if current.keys() != baseline.keys():
                failed = True
                detail += " (unpaired items)"
            else:
                hi, note = _paired_change(current, baseline, spec.get("bootstrap", {}))
                failed = failed or hi < 0
                detail += f" {note}"
        verdict = "ok"
        if failed:
            verdict = "warn"
            if rule.get("blocking"):
                blocked.append(key)
                verdict = "BLOCK"
        lines.append(f"  {key} {detail} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            hi, note = _paired_change(a, b, bs)
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
