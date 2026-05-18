# VIVAMACS Offline Project Status

**Last updated:** 2026-05-18 10:01 Asia/Manila  
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

## Immediate Next Steps

1. Push local commits to remote from an authenticated GitHub terminal:

   ```bash
   cd /fast/users/kobe/Projects/VIVAMACS
   git push origin main
   ```

2. Verify the candidate data/config files:

   - Candidate A exact file path/name.
   - Candidate B1 exact file path/name or generation script.
   - Candidate B3 exact file path/name or generation script.

3. Run smoke tests only after preregistration is pushed:

   - Load each candidate.
   - Run one short simulation seed or tiny Monte Carlo run.
   - Confirm outputs include data loss and repair cost.

4. Prepare/verify the Sobol pipeline:

   - N = 1024 base samples.
   - k = 3 parameters: `patch`, `AV`, `awareness`.
   - 8,192 model evaluations per candidate.
   - 200 Monte Carlo iterations per evaluation.
   - Three candidates A, B1, B3.

5. Launch long-running experiments only after smoke tests pass.

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
- Do not run experiments until the preregistration commits are pushed or the user explicitly accepts local-only timestamping.
- Do not deploy, touch Vercel/GCP, or modify the SaaS project during this offline-paper workstream.

