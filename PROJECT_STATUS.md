# VIVAMACS Offline Project Status

**Last updated:** 2026-05-22 Asia/Manila  
**Project path:** `/fast/users/kobe/Projects/VIVAMACS`  
**Repo remote:** `https://github.com/janespino24/ABMValidation.git`  
**Active workstream:** Paper 1, SIMPAT submission, methodology-only validation paper  
**Mode:** Offline/research paper work only. Do not mix with `vivamacs-saas` production work unless explicitly requested.

---

## Current Paper Direction

Paper 1 is now framed as an ABM validation methodology paper for *Simulation Modelling Practice & Theory* (SIMPAT), not as a cyber-security substantive-results paper.

Core contribution:

- A validation framework for agent-based cyber risk models.
- Demonstration using the VIVAMACS ABM as a case study.
- Synthetic ground truth validation as the central new experiment.
- Sobol/control-prioritization findings move to Paper 2.

Key working documents:

- `docs/PAPER1_WORKING_DOC.md`
- `docs/METHODS_synthetic_ground_truth.md`
- `docs/preregistrations/synthetic_ground_truth_2026-05-18.md`

Older context files still exist but are partially stale:

- `SESSION_CONTEXT.md`
- `VALIDATION_PROGRESS.md`

Use this `PROJECT_STATUS.md` as the current recovery source.

---

## Decisions Locked In

- Dissertation structure is three papers, not four.
- Paper 1 is methodology-only.
- Paper 1 target venue is SIMPAT.
- Paper 2 owns calibrated empirical cyber-risk results and control-prioritization findings.
- Paper 3 remains DistinctD / streaming anomaly detection.
- FABRICS is positioned as complementary: practitioner deployment and expert elicitation, not cross-organizational validation methodology.
- Synthetic ground truth is the critical near-term experiment for Paper 1.

---

## Synthetic Ground Truth Experiment

Purpose: demonstrate that the validation framework can recover a known structure from a fully specified truth process and can discriminate that truth process from deliberately weakened candidate models.

Truth process:

- Candidate A: `Data5_typical.csv` / Data5 typical configuration.
- Structural feature under test: asset-value concentration.
- Servers carry approximately 95.4% of `Data_Value` and 90.9% of `Repair_Value`.
- `awareness` affects PCs/mobiles through user vulnerability, but is structurally locked out of servers/firewalls/routers.

Candidate models:

- **A:** truth process.
- **B1:** uniform `Data_Value`, otherwise identical to A.
- **B3:** uniform `Data_Value` plus uniform `Repair_Value`.
- B2, uniform repair only, was considered and intentionally excluded.

Canonical candidate config files created after preregistration and before any experiment execution:

- `data/Data5_typical.csv` — Candidate A, exact copy of verified Data5 truth process.
- `data/Data5_B1_uniform_data_value.csv` — Candidate B1, `Data_Value` replaced for devices with nonzero `Data_Value`.
- `data/Data5_B3_uniform_data_and_repair_value.csv` — Candidate B3, B1 plus `Repair_Value` replaced for devices with nonzero `Repair_Value`.

Verified replacement means from `data/Data5 (typical) - 20 server.csv`:

- `Data_Value` mean across nonzero `Data_Value` devices: `167727.27272727274`.
- `Repair_Value` mean across nonzero `Repair_Value` devices: `19642.85714285714`.

Pre-experiment correction made on 2026-05-18: the preregistration and working doc previously contained a planning estimate of approximately `$102,400` for the B1 mean. The operational definition was unchanged, but the parenthetical value was corrected to `$167,727.27` after inspecting the actual Data5 file and before running experiments.

Pre-registered predictions:

- P1: `AV` dominates total-order Sobol index for data loss.
- P2: `awareness` near-zero for data loss.
- P3: `awareness` non-zero for repair cost.
- P4: awareness sensitivity is greater for repair than data loss.
- P5: server data-loss share is at least 0.85.
- P6: server compromise share remains below 0.50; null-control.
- P7: data-loss distribution is heavy-tailed, P95/median at least 3.0.
- P8: within-VLAN co-compromise rate at least 2x across-VLAN; null-control.

---

## Pre-Registration Record

The preregistration file was moved to the documented canonical path:

`docs/preregistrations/synthetic_ground_truth_2026-05-18.md`

Old path removed:

`preregistrations/PREREGISTRATION_synthetic_ground_truth.md`

Local preregistration commits:

- `dda1085` — `Preregister synthetic ground truth validation`
  - Full hash: `dda10857409d075f6539de63341cff268d16f225`
  - Date: `2026-05-18 10:01:00 +0800`
  - This is the canonical ex-ante preregistration commit.
- `5ab723a` — `Record preregistration commit reference`
  - Updates Section 9 with the canonical commit hash/date.

Important: GitHub push failed from this environment because no GitHub credentials were available:

```text
fatal: could not read Username for 'https://github.com': No such device or address
```

User should push from an authenticated terminal before running experiments:

```bash
cd /fast/users/kobe/Projects/VIVAMACS
git push origin main
```

Completed: user pushed local preregistration/status/candidate commits to GitHub on 2026-05-18. Remote advanced from `ba63b4e` to `659d0b8`; `git status -sb` now reports `main...origin/main` with no ahead commits.

---

## Current Git State Before This Tracker

The following paper docs were committed cleanly:

- `docs/PAPER1_WORKING_DOC.md`
- `docs/METHODS_synthetic_ground_truth.md`
- `docs/preregistrations/synthetic_ground_truth_2026-05-18.md`

There are pre-existing uncommitted/untracked files unrelated to the preregistration commit. Do not revert them without explicit instruction.

Known modified tracked files:

- `app.py`
- `requirements.txt`

Known untracked files/directories:

- `Data2 (Good).csv`
- `Papers/`
- `advanced_validation_suite.py`
- `data/Data5 (typical) - 20 server.csv`
- `data/Parameter_Changes_Record.csv`
- `data/data.csv`
- `make_ppt_v3.py`
- `paper_text.txt`
- `rerun_log_v2.txt`
- `sensitivity_analysis_awareness.py`
- `sobol_sensitivity_analysis.py`
- `src/notebook_refactor/simulation_trace.py`
- `validation_analysis.py`
- `validation_test_quick.py`
- `visualize_sensitivity.py`

---

## Smoke Test Record

Tiny post-push smoke tests were run after the preregistration and candidate-config commits were pushed. These were loading/output-shape checks only, not experimental analysis.

Command shape:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from src.notebook_refactor.environment import load_data, setup_environment
from src.notebook_refactor.simulation import run_iteration
...
PY
```

Results, one 1-day iteration per candidate:

| Candidate | Rows | Sigma | Device types | Data loss | Repair | Event summary |
|---|---:|---:|---|---:|---:|---|
| A | 36 | 13.333333333333334 | Firewall, Internet, Mobile, PC, Server | 21469333.333333313 | 4712000.0 | spam_mob=1, spam_pc=0, hack_fw=9, hack_server=57, hack_net=0 |
| B1 | 36 | 13.333333333333334 | Firewall, Internet, Mobile, PC, Server | 6219886.262499985 | 4269000.0 | spam_mob=2, spam_pc=1, hack_fw=9, hack_server=53, hack_net=0 |
| B3 | 36 | 13.333333333333334 | Firewall, Internet, Mobile, PC, Server | 6862840.797499984 | 1433928.7800000014 | spam_mob=2, spam_pc=4, hack_fw=12, hack_server=56, hack_net=0 |

Interpretation: all canonical candidate configs load successfully and produce valid nonzero data-loss/repair outputs. These results are stochastic smoke-test values and should not be used as paper results.

---

## Synthetic Ground Truth Runner

Added `scripts/synthetic_ground_truth_runner.py` to run the preregistered experiment without modifying the core VIVAMACS model code.

Runner scope:

- Uses canonical candidates A/B1/B3.
- Uses the preregistered 3-parameter Sobol problem: `patch`, `AV`, `awareness`, each over `[0, 100]`.
- Uses Saltelli sampling with `calc_second_order=True`, matching the preregistered `(2k + 2) * N = 8192` evaluations per candidate when `N = 1024`.
- Produces separate Sobol outputs for `data_loss` and `repair_cost`.
- Uses SALib bootstrap resampling through `sobol.analyze(..., num_resamples=1000)` by default.
- Provides a traced Candidate A cost-share routine for data-loss share, repair share, compromise-event share, compromise-period share, and a within/across VLAN co-compromise ratio.
- Includes `--mode smoke`, `--mode sobol`, `--mode cost-share`, and `--mode all`.

Verification completed:

```bash
.venv/bin/python -m py_compile scripts/synthetic_ground_truth_runner.py
.venv/bin/python scripts/synthetic_ground_truth_runner.py --mode smoke --candidate all --seed 20260518
.venv/bin/python scripts/synthetic_ground_truth_runner.py --mode cost-share --cost-share-runs 1 --days 1 --workers 1 --seed 20260518 --output-dir outputs/synthetic_ground_truth_smoke
```

The cost-share smoke check generated uncommitted smoke-only outputs:

- `outputs/synthetic_ground_truth_smoke/cost_share/candidate_A_cost_share_iterations.csv`
- `outputs/synthetic_ground_truth_smoke/cost_share/candidate_A_cost_share_summary.csv`

These smoke outputs are not paper results.

Full preregistered run command shape, after final review:

```bash
.venv/bin/python scripts/synthetic_ground_truth_runner.py \
  --mode all \
  --candidate all \
  --n-base 1024 \
  --runs-per-sample 200 \
  --cost-share-runs 1000 \
  --days 365 \
  --workers 24 \
  --seed 20260518 \
  --output-dir outputs/synthetic_ground_truth
```

Important runtime implication: this is a very large run: three candidates x 8192 Sobol evaluations x 200 MC iterations, plus cost-share runs. Consider a smaller dry run before the full launch.

---

## Immediate Next Steps

1. Verify the candidate data/config files:

   - Candidate A exact file path/name.
   - Candidate B1 exact file path/name or generation script.
   - Candidate B3 exact file path/name or generation script.

2. Run smoke tests only after preregistration is pushed:

   - Load each candidate.
   - Run one short simulation seed or tiny Monte Carlo run.
   - Confirm outputs include data loss and repair cost.

   Completed on 2026-05-18.

3. Review the new Sobol/cost-share runner against the preregistration:

   Completed on 2026-05-22:

   - `calc_second_order=True` remains because it is the SALib setting that implements the preregistered `(2k + 2) * N = 8192` Saltelli sample count at N=1024. The manuscript still reports S1/ST, not second-order indices.
   - P8 is operationalized as a period-level within/across VLAN co-compromise ratio: infected pair-periods divided by possible pair-periods for pairs that share at least one VLAN versus pairs that share none.
   - Realized-cost-share analysis is set to 1000 Candidate A Monte Carlo iterations at default parameters.

4. Push pending local commits before running full experiments:

   ```bash
   cd /fast/users/kobe/Projects/VIVAMACS
   git push origin main
   ```

5. Small Sobol dry run completed on 2026-05-22 after pushing through commit `d813151`:

   ```bash
   .venv/bin/python scripts/synthetic_ground_truth_runner.py \
     --mode sobol \
     --candidate A \
     --n-base 8 \
     --runs-per-sample 2 \
     --days 1 \
     --workers 2 \
     --bootstrap-resamples 10 \
     --output-dir outputs/synthetic_ground_truth_dryrun
   ```

   Result: completed 64 Candidate A Sobol dry-run evaluations and wrote metadata, parameter samples, raw outputs, and Sobol CSV files under `outputs/synthetic_ground_truth_dryrun/sobol/A/`. These are pipeline-check artifacts only and are not paper results. SALib emitted a deprecation warning for `salib.sample.saltelli`; this does not affect the dry run, but the runner should eventually migrate to `salib.sample.sobol`.

6. Medium dry runs completed on 2026-05-22:

   - Sobol medium dry run across A/B1/B3 completed with `N=16`, `runs-per-sample=5`, `days=7`, `workers=4`, and wrote expected outputs under `outputs/synthetic_ground_truth_medium_dryrun/sobol/`.
   - Candidate A cost-share medium dry run completed with 25 iterations at 7 days and wrote expected outputs under `outputs/synthetic_ground_truth_medium_dryrun/cost_share/`.
   - Candidate A 365-day horizon check completed with 25 cost-share iterations under `outputs/synthetic_ground_truth_costshare_horizon_check/cost_share/`. P5-style server data-loss concentration appears strong (`data_share_Server` mean about 0.9986), but P6 and P8 are flagged: `compromise_event_share_Server` mean about 0.783 and `lateral_clustering_ratio` mean about 0.791. These are dry-run diagnostics, not paper results, but they indicate the preregistered P6/P8 null-control expectations may be misspecified.

7. Decision made on 2026-05-22: use Option 1. Keep P6 and P8 exactly as preregistered, do not revise thresholds, and run the full experiment as filed. If P6/P8 fail in the full run, report those failures transparently as null-control diagnostic findings and discuss what they reveal about the Data5 truth process and/or the operational definitions. The primary asset-value concentration claim remains anchored in the preregistered P1-P5 tests, but P6/P8 remain part of the reported preregistered result set.

8. Timing benchmarks completed on 2026-05-22:

   - Candidate A Sobol benchmark, `N=8`, `runs-per-sample=5`, `days=365`, `workers=8`, completed successfully under `outputs/synthetic_ground_truth_timing_benchmark/`. Rough wall time was about 3.5 minutes for 64 parameter sets and 320 full-horizon MC iterations.
   - Candidate A Sobol benchmark, same settings with `workers=24`, completed under `outputs/synthetic_ground_truth_timing_benchmark_24w/`. Measured wall time was `real 119.79` seconds, `user 2472.48`, `sys 0.36`.
   - Full preregistered Sobol scale is 3 candidates x 8192 parameter sets x 200 MC iterations = 4,915,200 full-horizon MC iterations. Linear scaling from the 24-worker benchmark suggests roughly 18-21 days of local wall-clock runtime.

9. Checkpoint/resume support added on 2026-05-22:

   - Sobol runs now write `sobol_checkpoint.csv` under each candidate output directory after each completed parameter set. Rerunning the same command validates metadata, reloads completed indices, skips finished samples, and regenerates final `Y_*.npy`, `model_outputs.csv`, and Sobol CSV files once complete.
   - Cost-share runs now write `candidate_A_cost_share_checkpoint.csv` plus cost-share metadata, validate resume settings, skip completed iterations on rerun, and regenerate final iteration and summary CSVs from the checkpoint.
   - Added `--no-resume` to intentionally ignore existing checkpoints and recompute in the selected output directory.
   - Verification completed: `py_compile`; tiny Sobol checkpoint creation; complete Sobol resume; partial Sobol resume after trimming checkpoint to 5/16 rows; tiny cost-share checkpoint creation; complete cost-share resume.

10. Next action: push the checkpoint/resume commit, then launch the full preregistered run inside a persistent terminal/session manager. If interrupted, rerun the same command without `--no-resume` to continue from checkpoints.

---

## Recovery Checklist

When resuming:

1. Start here:

   ```bash
   cd /fast/users/kobe/Projects/VIVAMACS
   git status --short
   git log --oneline -5
   ```

2. Confirm the preregistration commits exist:

   ```bash
   git show --stat dda1085
   git show --stat 5ab723a
   ```

3. Confirm whether remote push has happened:

   ```bash
   git status -sb
   git log origin/main..main --oneline
   ```

4. If `origin/main..main` still shows `dda1085` and `5ab723a`, push before experiments.

5. Reopen the active files:

   - `docs/PAPER1_WORKING_DOC.md`
   - `docs/METHODS_synthetic_ground_truth.md`
   - `docs/preregistrations/synthetic_ground_truth_2026-05-18.md`
   - `PROJECT_STATUS.md`

---

## Guardrails

- Keep Paper 1 methodology-only.
- Do not add Paper 2 substantive control-prioritization claims into Paper 1 except as future application.
- Do not tune preregistration thresholds after seeing results.
- If predictions fail, report them honestly as framework boundary evidence.
- Do not run full experiments until the Sobol runner is reviewed against the preregistration.
- Do not deploy, touch Vercel/GCP, or modify the SaaS project during this offline-paper workstream.
