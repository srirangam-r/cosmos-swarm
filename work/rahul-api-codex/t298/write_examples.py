"""Write deterministic synthetic fixtures and a truthful no-clips report.

No network/referee requests, video reads, measurement or model inference.
"""
import json
from pathlib import Path

import paired_report as pr
from test_paired_report import fixture


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main():
    root = Path(__file__).resolve().parent
    examples = root / "examples"
    examples.mkdir(exist_ok=True)
    data, validation, registry = fixture(examples)
    write(examples / "synthetic_observations.json", data)
    write(examples / "synthetic_report.json", pr.analyze(data, validation))

    # An empty measured ledger: no generated clips, no period observations.
    # Only the crossing method is configured. The other methods remain explicit
    # unavailable validation entries rather than invented PASS documents.
    response_path = root / "fixtures" / "actual_289_referee_response.json"
    raw = pr.read_json(response_path)
    current = dict(schema="t298-validation-v1", kind="referee", tools={})
    for tool in pr.TOOLS:
        current["tools"][tool] = dict(method=None, source_sha256=None,
                                     referee_response_path=None,
                                     referee_response_sha256=None, evidence_url=None)
    current["tools"]["crossing"] = dict(
        method=raw["method"],
        source_sha256="d5bb5a444754253751b145b776dce9e5a1e4124b0f63235e9337894350547e8c",
        referee_response_path="fixtures/actual_289_referee_response.json",
        referee_response_sha256=pr.digest(response_path.read_bytes()),
        evidence_url="https://github.com/srirangam-r/cosmos-swarm/blob/0f135ad/work/ro-sol1/t289/referee_response.json")
    current_path = root / "current_validation.json"
    write(current_path, current)
    empty = dict(schema=pr.SCHEMA, kind="measured", rows=[])
    write(root / "observations_template.json", empty)
    report = pr.analyze(empty, pr.load_validation(current_path))
    assert report["status"] == "NO_CLIPS"
    assert report["method_validation_status"] == "UNVALIDATED"
    assert report["coverage"] == dict(planned=18, present=0, technical_clean=0, accepted=0)
    assert report["paired_intervals_by_tool"] is None
    write(root / "current_no_clips_report.json", report)


if __name__ == "__main__":
    main()
