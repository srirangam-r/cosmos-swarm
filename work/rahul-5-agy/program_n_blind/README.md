# Program N Blind Second-Coding Infrastructure (rahul-5-agy)

**Status: Prepared and pre-registered for Program N Tasks 225 & 226 (Raj #4464).**
**No deliverable edits.** Deliverables 1–3 and root `README.md` remain untouched per human steering.

## Overview
This package prepares `rahul-5-agy` to act as an independent blind second coder for Program N:
- **Task 225 (N4)**: Seed bank testing on contact events (clean fall, settle / rest).
- **Task 226 (N5)**: Boundaries of text control over motion.

## Components
1. **`PROTOCOL.md`**: Pre-registered protocol defining blinding rules, cryptographic code freezing (`blind_codes.FROZEN.sha256`), standardized 5-class contact/rest rubric, and motion trajectory vocabulary.
2. **`harness.py`**: Evaluation engine supporting:
   - Rubric vocabulary validation.
   - SHA-256 cryptographic freezing before unblinding.
   - Inter-rater concordance and Cohen's $\kappa$ evaluation.
   - Planted/known-answer control scoring.
3. **`test_harness.py`**: Test suite with 5 unit tests verifying hash generation, input validation, kappa calculation, and control checks.

## Verification
```bash
python3 work/rahul-5-agy/program_n_blind/test_harness.py
```
All unit tests pass cleanly.
