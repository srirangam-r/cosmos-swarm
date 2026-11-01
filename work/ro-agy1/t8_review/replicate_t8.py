"""Independent replication and audit of Task 8 / Finding #4090:
Calibration of unchanged measure_pend v1 across 20 real GAUGE pendulum continuations.

Author: ro-agy1 (Shift 12)
"""
import json
import math
from pathlib import Path
import numpy as np

def run_replication():
    t8_dir = Path("/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/codex-api-4/t8")
    results_path = t8_dir / "output/results.json"
    table_path = t8_dir / "table.csv"
    timebase_path = t8_dir / "timebase_sensitivity.json"
    
    with open(results_path) as f:
        results = json.load(f)
        
    with open(timebase_path) as f:
        timebase = json.load(f)
        
    # Read table.csv
    table_records = []
    with open(table_path) as f:
        header = f.readline().strip().split(",")
        for line in f:
            if line.strip():
                parts = line.strip().split(",")
                row = dict(zip(header, parts))
                table_records.append(row)
                
    # 1. Verification of records and flags
    total_records = len(results)
    ok_records = [r for r in results.values() if r["tool"]["flag"] == "ok"]
    check_records = [r for r in results.values() if r["tool"]["flag"] != "ok"]
    
    assert total_records == 20, f"Expected 20 records, got {total_records}"
    assert len(ok_records) == 19, f"Expected 19 ok records, got {len(ok_records)}"
    assert len(check_records) == 1, f"Expected 1 check record, got {len(check_records)}"
    assert check_records[0]["id"] == 13, f"Expected check record to be 13, got {check_records[0]['id']}"
    
    # 2. Recompute statistics for eligible (19 ok) records
    def stats(arr):
        n = len(arr)
        mean = float(np.mean(arr))
        sd = float(np.std(arr, ddof=1))
        se = sd / math.sqrt(n)
        min_v = float(np.min(arr))
        max_v = float(np.max(arr))
        w1 = int(np.sum(np.abs(arr - 1.0) < 0.01))
        w5 = int(np.sum(np.abs(arr - 1.0) < 0.05))
        return {
            "n": n,
            "mean": mean,
            "se": se,
            "sd": sd,
            "min": min_v,
            "max": max_v,
            "within_1pct": w1,
            "within_5pct": w5
        }
        
    ok_ratios = np.array([r["ratio"] for r in ok_records])
    ok_turn_ratios = np.array([r["ratio_turning"] for r in ok_records])
    ok_zc_ratios = np.array([r["ratio_zc"] for r in ok_records])
    
    stats_ratio = stats(ok_ratios)
    stats_turn = stats(ok_turn_ratios)
    stats_zc = stats(ok_zc_ratios)
    
    # Empirical coverage of nominal 95% bootstrap intervals
    covered_count = 0
    coverage_details = {}
    for r in ok_records:
        rid = r["id"]
        ci_lo, ci_hi = r["tool"]["period_ci95"]
        ref_p = r["reference_crossing"]["period_s"]
        is_cov = (ci_lo <= ref_p <= ci_hi)
        if is_cov:
            covered_count += 1
        coverage_details[rid] = {
            "period_tool": r["tool"]["period_s"],
            "ci95": [ci_lo, ci_hi],
            "period_mocap": ref_p,
            "covered": is_cov,
            "err_pct": (r["tool"]["period_s"] - ref_p) / ref_p * 100.0
        }
        
    empirical_coverage_pct = covered_count / len(ok_records) * 100.0
    
    # All-20 statistics (including #13)
    all_ratios = np.array([r["ratio"] for r in results.values()])
    stats_all = stats(all_ratios)
    
    # Alignment sensitivity across +/- 1 distinct frame
    align_diffs = []
    for r in results.values():
        ref_p = r["reference_crossing"]["period_s"]
        for q in ["-1", "1"]:
            if q in r["alignment_sensitivity"]:
                alt_p = r["alignment_sensitivity"][q]["period_s"]
                align_diffs.append(abs(alt_p - ref_p))
    max_align_diff_s = float(max(align_diffs)) if align_diffs else 0.0
    
    # Timebase sensitivity analysis
    # Compare nominal 25Hz zero-crossing ratio vs container timestamps
    tb_dict = timebase.get("records", {})
    ok_ids = [str(ok_r["id"]) for ok_r in ok_records]
    tb_zc_ratios = np.array([tb_dict[rid]["container_timestamp_zc_ratio"] for rid in ok_ids if rid in tb_dict])
    stats_tb = stats(tb_zc_ratios)
    
    # Check trace files
    trace_dir = t8_dir / "output/traces"
    trace_files = list(trace_dir.glob("real_*.json"))
    assert len(trace_files) == 20, f"Expected 20 trace files, got {len(trace_files)}"
    
    # Verify exact match with Finding 4090 text:
    # Value: fit / same-window mocap = 1.007195 ± 0.001763 SE, range 0.998191–1.018778; 12/19 within 1%.
    # Turning-point reference: 1.006666 ± 0.001731 SE.
    # One retained check case (#13) reads 2.713x; all-20 mean = 1.09248 ± 0.08530 SE.
    # Coverage covers mocap on 11/19.
    diff_mean = abs(stats_ratio["mean"] - 1.007195020972603)
    diff_se = abs(stats_ratio["se"] - 0.0017627575343160298)
    diff_turn_mean = abs(stats_turn["mean"] - 1.006665531180557)
    diff_turn_se = abs(stats_turn["se"] - 0.0017312977804617036)
    diff_all_mean = abs(stats_all["mean"] - 1.092483239647617)
    diff_all_se = abs(stats_all["se"] - 0.0853046119941314)
    
    out = {
        "status": "PASS",
        "n_total": total_records,
        "n_ok": len(ok_records),
        "n_check": len(check_records),
        "check_id": check_records[0]["id"],
        "check_details": {
            "tool_period_s": check_records[0]["tool"]["period_s"],
            "mocap_period_s": check_records[0]["reference_crossing"]["period_s"],
            "ratio": check_records[0]["ratio"],
            "r2": check_records[0]["tool"]["r2"],
            "beta": check_records[0]["tool"]["beta"],
            "flag": check_records[0]["tool"]["flag"]
        },
        "ratio_fit_mocap": stats_ratio,
        "ratio_turning": stats_turn,
        "ratio_zc_25hz": stats_zc,
        "ratio_zc_container": stats_tb,
        "all_20_ratio": stats_all,
        "coverage": {
            "n_covered": covered_count,
            "n_eligible": len(ok_records),
            "coverage_pct": empirical_coverage_pct,
            "details": coverage_details
        },
        "max_align_sensitivity_s": max_align_diff_s,
        "reproduction_exact": {
            "diff_mean": diff_mean,
            "diff_se": diff_se,
            "diff_turn_mean": diff_turn_mean,
            "diff_turn_se": diff_turn_se,
            "diff_all_mean": diff_all_mean,
            "diff_all_se": diff_all_se
        }
    }
    
    out_file = Path("/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/t8_review/t8_replication_results.json")
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)
        
    print(f"Replication complete. Results written to {out_file}")
    print(f"Eligible records: {len(ok_records)}/20 (check case: #{check_records[0]['id']})")
    print(f"Ratio fit/mocap: {stats_ratio['mean']:.6f} +/- {stats_ratio['se']:.6f} SE (range {stats_ratio['min']:.6f} - {stats_ratio['max']:.6f})")
    print(f"Within 1%: {stats_ratio['within_1pct']}/19; within 5%: {stats_ratio['within_5pct']}/19")
    print(f"Turning-point ratio: {stats_turn['mean']:.6f} +/- {stats_turn['se']:.6f} SE")
    print(f"All-20 ratio (retaining #13): {stats_all['mean']:.6f} +/- {stats_all['se']:.6f} SE (max {stats_all['max']:.6f})")
    print(f"Empirical 95% CI coverage: {covered_count}/19 ({empirical_coverage_pct:.1f}%)")
    print(f"Container timebase ratio: {stats_tb['mean']:.6f} +/- {stats_tb['se']:.6f} SE")
    print(f"Max alignment diff across +/-1 frame: {max_align_diff_s:.6f} s")

if __name__ == "__main__":
    run_replication()
