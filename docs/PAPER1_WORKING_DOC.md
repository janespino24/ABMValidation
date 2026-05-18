# Paper 1 — Working Document

**Author:** Jan-Michael B. Espino
**Last updated:** 18 May 2026
**Status:** Active — three-week submission timeline to SIMPAT
**Purpose:** Consolidate the full state of Paper 1's planning, framing, and submission strategy in one place. This document is the working reference; manuscript drafting, pre-registration, and experimental work all key off it.

---

## 1. Decisions locked in

### 1.1 The three-paper dissertation structure

The dissertation comprises three papers, not four. The decision to keep the count at three (rather than splitting Paper 1 into "1a methodology" + "1b security finding") was made deliberately to avoid self-overlap with Paper 2.

- **Paper 1 — ABM Validation Methodology.** Target venue: *Simulation Modelling Practice & Theory* (SIMPAT). Methodology-only paper. The demonstration ABM is the case study; the contribution is the six-tier validation framework.
- **Paper 2 — Calibrated Agent-Based Cyber Risk Model.** Target venue: *Computers & Security* (C&S) or *IEEE TDSC*. Empirical calibration, extended experiments, and the Sobol control-prioritization findings (server controls dominate breach-cost variance under realistic asset concentration). Builds on Paper 1's validated framework as a citable foundation.
- **Paper 3 — DistinctD: Streaming Anomaly Detection.** Target venue: *IEEE TIFS* or *IEEE TNSM*. Scalable streaming algorithms for real-time detection.

The Sobol/control-prioritization finding lives entirely in Paper 2. Paper 1 references it as a forthcoming application, not a contribution it owns.

### 1.2 Why this structure (and not the alternative)

The original draft tried to do both methodology and security finding in one paper. Two problems with that:

1. **Venue mismatch.** A combined paper pleased neither C&S reviewers (who want sharper security claims) nor V&V-literate reviewers (who want sharper methodology). Splitting by audience is the right move.
2. **FABRICS occupies the practitioner-deployment niche.** The Slapničar & Joshi 2026 paper in C&S already covers organization-specific cyber risk quantification using Bayesian fault trees. The methodology niche — cross-organizational, generalizable validation — remains open. Paper 1 occupies it.

A briefly-considered alternative ("Paper 1a methodology + Paper 1b security finding") was rejected because 1b would have duplicated Paper 2's natural territory and created self-overlap between two C&S-tier submissions. The current structure has clean dependency: Paper 1 → SIMPAT → cited by Paper 2 → C&S/TDSC. No cross-submission risk.

### 1.3 FABRICS positioning (for the manuscript and any committee questions)

The FABRICS paper is *not* a direct competitor to Paper 1 on three grounds, each of which FABRICS's own authors support:

1. **Different scope of claim.** FABRICS §5.2.7 explicitly disclaims cross-organizational generalization: *"The probability estimates generated through FABRICS should not be interpreted as empirical frequencies or as values that can be generalised across organisations."* Paper 1's methodology occupies exactly the cross-organizational space FABRICS rules out.
2. **Different novelty claim.** FABRICS's contribution is the CLUE elicitation protocol (how to extract collective uncertainty from a group of experts). Fault-tree quantification is presented as standard. Paper 1's contribution is on the validation layer, not the elicitation layer.
3. **Different validation depth.** FABRICS §5.2.9 is a half-paragraph reviewing extreme expert estimates; there is no Sobol, no ablation, no falsification thresholds, no structural validation. Paper 1's six-tier framework directly addresses this gap.

The framing for the SCR presentation and the manuscript: *"FABRICS occupies the practitioner-deployment niche; Paper 1 occupies the methodology niche. Complementary, not competing."* Do not frame any communication as "Paper 1 is better than FABRICS." The authors may be reviewers; Slapničar & Joshi's scope disclaimer does the positioning work without antagonism.

---

## 2. Paper 1: what it is and is not

### 2.1 Contribution

A six-tier validation framework for agent-based cyber risk models, demonstrated on a configurable ABM with two contrasting model candidates. The four explicit contributions:

1. **Four-tier credibility architecture.** Eleven validation techniques organized into implementation, structural, empirical, and robustness tiers, each with explicit acceptance criteria.
2. **Operationalized pattern-oriented validation.** Four documented cyber-risk regularities specified as quantitative validation patterns with falsification thresholds.
3. **Validation-technique ablation.** Systematically remove each technique and re-score credibility to identify which carry distinct information vs. redundancy.
4. **Reproducible reference implementation.** Configuration files, simulation engine, and validation harness for independent replication.

### 2.2 What Paper 1 does NOT claim

- It does not validate the ABM against empirical breach data. The ABM is the *case study* for demonstrating the framework, not the object of the validation claim.
- It does not claim cross-organizational predictive accuracy. That belongs to Paper 2.
- It does not claim the framework catches every form of model misspecification. The synthetic ground truth experiment tests a specific form (asset-value concentration); other misspecifications are acknowledged as untested.
- It does not propose any new individual validation technique. Sargent 2013 + Grimm et al. 2005 + Saltelli et al. 2008 cover the components. The contribution is the *integration*, the *operationalization with falsification thresholds*, and the *synthetic-ground-truth approach* — not the constituent methods.

### 2.3 Why SIMPAT is the right venue

- Reviewers are V&V-literate and accept "synthesis + domain adaptation" as a genuine contribution.
- Natural home for ABM verification & validation methodology.
- Q1 (impact factor ~4.6–6.0), faster turnaround than C&S.
- Estimated acceptance probability after the planned revisions: 45–55%.
- Risk Analysis (Wiley/SRA, IF ~3.0) is the strongest fallback if SIMPAT declines.

---

## 3. The six mandatory fixes — status as of 18 May 2026

| # | Fix | Status | Notes |
|---|---|---|---|
| 1 | Sobol re-run at N ≥ 1024 base samples (~1.84M sims) | **CRITICAL PATH** | Launches in Week 1. Tightens S₁ CIs from ±0.30 to ~±0.10. |
| 2 | Bounded-calibration table vs Verizon DBIR / IBM 2024 / Ponemon | DEFERRED to revisions | Out of scope for three-week timeline. |
| 3 | Cost-magnitude rescaling (×~0.004) | DEFERRED to Paper 2 | Less aggressive than originally planned given FABRICS precedent. |
| 4 | Face validation → reframe as expert structural review | **IN PROGRESS** | One-week edit, scoped. |
| 5 | Adversarial-adaptation gap → reframe to "strategic opacity" | SCOPED | Limitations-section addition. |
| 6 | Pattern falsification thresholds in §5.3 | **IN PROGRESS** | Lift from appendix A6 of SCR deck into manuscript text. |

The Sobol re-run and the synthetic ground truth experiment are running in parallel. Fix 4 (face validation rewrite) and Fix 6 (falsification thresholds) are quick edits that happen during Week 2 of the timeline below.

---

## 4. The synthetic ground truth experiment

This is the single most important new piece of work for the three-week submission. It directly addresses the April SCR feedback ("simulation should be used to create evaluable ground truth") and provides the strongest pillar of Paper 1's validation argument.

### 4.1 The core idea

Build a simulated world where the truth process is fully specified by configuration. Pre-register predictions about what the validation framework should detect. Run the framework against the truth process (Candidate A) and against deliberately weakened candidates (B1, B3). Demonstrate that the framework discriminates correctly.

This inverts conventional validation: rather than asking "does the model match the world?", we ask "does the framework correctly recover a known structure?" The advantage is no measurement noise — the truth is what we defined.

### 4.2 The truth process

The ABM as configured by `Data5_typical.csv`. Asset concentration is the key structural feature:

| Asset class | Data_Value share | Repair_Value share |
|---|---:|---:|
| Servers (3) | 95.4% | 90.9% |
| PCs (4) | 2.3% | 2.9% |
| Mobiles (4) | 2.3% | 5.1% |
| Firewalls (3) | 0% | 1.1% |

Two cost mechanisms operate concurrently:

- **Data loss** accrues at rate `Data_Value / 12` per 5-minute infected period; servers, PCs, mobiles only. *Duration-driven, concentrated at servers.*
- **Repair cost** charged once per recovery event at `Repair_Value`; servers, PCs, mobiles, firewalls, routers. *Event-driven, distributed broadly.*

Sobol varies three parameters globally over [0, 100]: `patch`, `AV`, `awareness`. Critical structural fact: `awareness` only affects PCs and mobiles (via the user-vulnerability term); it is locked out of servers, firewalls, and routers. The framework must recover this.

### 4.3 Candidate models

- **Candidate A (truth):** Data5_typical.csv as supplied.
- **Candidate B1 (uniform data value):** identical to A except `Data_Value` replaced by its mean across devices with nonzero `Data_Value` ($167,727.27 in the verified Data5 configuration). Network topology, controls, threat parameters, repair values all unchanged. Tests whether the framework correctly identifies the *absence* of asset-value concentration.
- **Candidate B3 (uniform both):** B1 plus `Repair_Value` replaced by its mean. Strongest contrast.

Candidate B2 (uniform repair only) was considered and excluded — tests a less mechanism-relevant alternative.

### 4.4 Pre-registered predictions

Filed in `docs/preregistrations/synthetic_ground_truth_2026-05-18.md` (committed to repo). Eight predictions across three groups:

**Sobol parameter attribution:**
- P1: `AV` dominates S_T for data loss (≥ 0.50, largest of three)
- P2: `awareness` near-zero S_T for data loss (≤ 0.10)
- P3: `awareness` non-zero S_T for repair cost (≥ 0.05)
- P4: Differential — S_T(awareness, repair) > S_T(awareness, data) by ≥ 0.03

**Realized cost-share asset attribution:**
- P5: Server data-loss share ≥ 0.85
- P6: Server compromise share < 0.50 *(null-control — should hold across all candidates)*

**Distributional and structural:**
- P7: P95/median ≥ 3.0 for data loss
- P8: Lateral-movement clustering, within/across-VLAN ratio ≥ 2× *(null-control)*

P4 (differential prediction) is the strongest single piece of evidence for mechanism recovery — harder to satisfy by accident than headline-magnitude predictions.
P6 and P8 are deliberate null-controls: they test mechanisms that aren't varied between candidates and should produce similar values across A, B1, B3. Spurious differences would indicate the framework has false-positive sensitivity.

### 4.5 Two complementary attribution paths

The methods section explicitly distinguishes two analyses, both applied to each candidate:

- **Sobol sensitivity:** decomposes variance in cost outcomes across the three globally-varied parameters. Answers: *which control type, varied uniformly, explains the most variance?*
- **Realized cost-share:** decomposes simulated cost outcomes by asset class. Answers: *which asset class does cost actually accrue to?*

These are complementary, not redundant. Sobol identifies which parameter moves the outcome; cost-share identifies where the outcome lands. Together they support the structural argument: variance is driven by AV-class controls AND manifests primarily at servers, implying asset-weighted prioritization is optimal. This is what Paper 2 will eventually argue substantively.

**Explicit scope limitation in the paper:** Sobol indices in Paper 1 are computed over globally-varying parameters. Asset-class-specific Sobol (separating server AV from endpoint AV) requires k ≥ 9 dimensions and is reserved for Paper 2. State this explicitly in §X.5; it preempts the most likely methodological objection.

### 4.6 The honest limitation Paper 1 names

The synthetic ground truth experiment tests one specific form of misspecification: asset-value concentration. The framework's behaviour against other forms of misspecification (incorrect topology, missing lateral movement, misspecified threat distributions) is not tested here. This is acknowledged as a limitation, not hidden.

---

## 5. Three-week submission timeline

Roughly 15 working days. Aggressive scope cuts; defer everything non-essential to the revision round.

### Week 1 — Compute launch + synthetic ground truth foundation

- **Day 1:** Lock the eight predictions in writing. Commit `PREREGISTRATION_synthetic_ground_truth.md` to the repo. Push to remote. Record commit hash in §9 of the pre-registration file.
- **Day 1:** Verify Candidate B1 and B3 config files load and run a single seed each. ~20 minutes per config.
- **Day 1–7 (background):** Sobol re-run launches for all three candidates (A, B1, B3) concurrently if pipeline supports parallel; otherwise serialize and accept the extended Week 1.
- **Day 2–5 (foreground):** Build the synthetic ground truth section text (§X.1–§X.5). Use `METHODS_synthetic_ground_truth.md` as scaffold.
- **Day 6–7:** Face validation rewrite (Fix 4). Integrate Sobol results as they land.

### Week 2 — Manuscript surgery

- **Day 8–10:** Pattern falsification thresholds into §5.3 (Fix 6). Lift from appendix A6 of the SCR deck.
- **Day 11–12:** Engage the UCL literature (Pym, Caulfield, Ilau 2025 papers in Journal of Cybersecurity). Pick one for deep engagement; cite the others more briefly.
- **Day 13–14:** Full-manuscript pass — internal consistency, terminology drift, integration seams after section edits.

### Week 3 — Polish and submit

- **Day 15–17:** SIMPAT-specific formatting, reproducibility statement, code availability statement. Elsevier author guidelines for SIMPAT.
- **Day 18:** Cover letter; suggested reviewers (3 names — V&V-literate ABM methodologists; *not* Slapničar or Joshi; conflict).
- **Day 19–20:** Final read-through. Buffer for last-minute issues.
- **Day 21:** Submit.

### What's deferred to the revision round

- Bounded-calibration table vs Verizon/IBM/Ponemon
- Framework naming (decide during revisions when reviewers signal what they see as the framework's identity)
- Pre-registration as separate OSF/AsPredicted artifact (commit-hash referencing suffices)
- Cost-magnitude rescaling (a Paper 2 issue, not Paper 1)
- Empirical leg of the equal-weight critique against NIST CSF / CIS / ISO (a Paper 2 issue)

---

## 6. Risk register for the three-week window

| Risk | Likelihood | Impact | Response |
|---|---|---|---|
| Sobol re-run CIs don't tighten as expected at N=1024 | Med | Low | Escalate to N=2048 in revisions; report directional rather than quantitative claim if needed. Pre-draft the limitation language. |
| Synthetic ground truth example reveals a framework problem | Low–Med | High | Scope down to "specified protocol with worked example in future work" rather than "demonstrated example." Build slack in Week 1. |
| Candidate B parallelism not supported by current pipeline | Med | Med | Run B1 first (the more important contrast); add B3 in revisions if time-constrained. |
| SIMPAT format requirements absorb more time than estimated | Low | Med | Day 15 read of author guidelines is the safety check. |
| Co-author/advisor review on last-minute draft | Variable | Med | Send draft earlier than feels comfortable; build in 2 days for response. |
| A new competitor paper surfaces during the three weeks | Low | Med | Standing literature monitoring continues; scope-check and adjust positioning only if the new paper materially changes the niche. |

Highest-residual risk after mitigation: the synthetic ground truth example failing to discriminate as predicted. Mitigation requires honest reporting and possibly scope adjustment — not concealment.

---

## 7. The SCR (15 May 2026) — outcome summary

*This section preserves the context of where the project stood entering the SCR and what was communicated to the committee.*

### 7.1 What the committee saw

A 16-slide main deck and 8-slide backup appendix. Main deck structure:

1. Title — SCR Update 14 May 2026
2. Progress since last review (April → May delta)
3. Updated three-paper roadmap — explicit "still three papers" framing
4. Section divider — Paper 1
5. The April SCR feedback on Paper 1
6. The novelty problem from the literature scan
7. Three findings that forced a rethink (FABRICS, UCL, AI/ML moratorium)
8. The strategic decision: reposition Paper 1
9. Paper 1 — the framework as the contribution
10. What moves into Paper 2: the security finding
11. The revised validation framework
12. Six mandatory fixes — status
13. Submission sequence: Paper 1, then Paper 2
14. Section divider — Paper 3
15. Paper 3 — toward measurable validation (DistinctD)
16. Cycle status and the decisions still open

Backup appendix:
- A1 divider
- A2 Sobol detail — current vs target CIs
- A3 Q1 venue comparison
- A4 The equal-weight critique evidence chain
- A5 FABRICS and Paper 2: three reasons they don't collide *(strongest positioning slide)*
- A6 Pattern falsification thresholds
- A7 Cost-rescaling rationale
- A8 Risk register

### 7.2 The three open decisions presented for committee discussion

1. Repositioning Paper 1 as methodology-only, with SIMPAT as the target venue
2. Consolidating the Sobol findings into Paper 2 (not a separate paper)
3. The equal-weight critique — whether the claim against NIST CSF / CIS / ISO is defensible enough

### 7.3 Outcomes to record

*[To be filled in after the SCR meeting]*

- Committee feedback on the repositioning: [TBD]
- Committee feedback on the synthetic ground truth approach: [TBD]
- Action items emerging from the discussion: [TBD]
- Changes to the three-week timeline based on committee input: [TBD]

---

## 8. Reference materials

These documents and decisions inform Paper 1's framing and should be kept accessible during writing.

### 8.1 Key citations to include

- **Sargent 2013** — canonical V&V framework reference
- **Grimm et al. 2005** — pattern-oriented modelling
- **Saltelli et al. 2008** — Sobol sampling scheme
- **Augusiak et al. 2014** — pattern-oriented validation, null-control rationale
- **Schmolke et al. 2010** — TRACE framework for model documentation
- **van Dam & Lukszo 2024** (JASSS) — ABM validation in socio-technical systems
- **ten Broeke et al. 2016** — sensitivity analysis in ABM
- **Slapničar & Joshi 2026** (FABRICS, C&S) — cite as complementary, not competing
- **Caulfield, Ilau, Pym 2025** (Journal of Cybersecurity, three papers) — engage UCL line of work
- **Kianpour & Franke 2025** — recent cyber-risk quantification
- **Gardner et al. 2019** — cyber-risk regularities
- **Żebrowski et al. 2022** — relevant prior ABM-based cyber-risk modelling

### 8.2 The four documented cyber-risk regularities (Paper 1's pattern-oriented validation)

These are the patterns Paper 1's framework validates against. Each has a pre-registered quantitative threshold:

1. **Heavy-tailed losses** — Breach losses are heavy-tailed. Threshold: P95 / median ≥ 3.0 in ≥ 3 of 4 scenarios.
2. **Lateral-movement clustering** — Compromise spreads within network segments. Threshold: mean intra-VLAN lag / inter-VLAN lag ≤ 0.1 (or relaxed to ≥ 2× within/across given the probabilistic mechanism).
3. **Nonlinear control effectiveness** — Diminishing returns; S-shaped curve. Threshold: S-shape fit with R² ≥ 0.95.
4. **Asset-value concentration** — Cost concentrates on high-value assets. Threshold: server cost share ≥ 0.7 AND server compromise share < 0.5.

### 8.3 Configuration files

- `Data5_typical.csv` — the truth process for Candidate A. 36 rows: 8 users, 4 PCs, 4 mobiles, 3 servers, 3 firewalls, 2 internet gateways, 11 VLANs, 1 Target row.
- `Data6_worst_test.csv` — alternate parameterization (low controls); not used in the synthetic ground truth experiment itself but available as additional reference.
- *To be created:* `Data7_uniform_data.csv` (Candidate B1) and `Data8_uniform_both.csv` (Candidate B3). Build these on Day 1 of Week 1.

### 8.4 Model algorithm reference

See `MODEL_ALGORITHM.md` in the repository for the full specification of:

- Time model (5-min periods, 0–24 hours, working-hours gating)
- Random attack pressure (truncated Gaussian, σ = Target_Level / 3)
- Strength formulas per agent class (different exponents for servers, firewalls/routers, PCs/mobiles, internet)
- User vulnerability formula for PCs/mobiles
- Breach simulation rules per agent class
- Propagation (nearby flag, VLAN-based, probabilistic clearing)
- Recovery logic (>30 min infected, AV-based for endpoints, strength-based for network devices)
- Cost accrual (data loss continuous; repair event-based)
- Monte Carlo aggregation and Sobol sensitivity

---

## 9. Document maintenance

This document is the working reference for Paper 1. Update it as decisions evolve. Specifically:

- After the SCR (15 May 2026): fill in §7.3 with outcomes.
- After Sobol runs complete: cross-reference the results in §6 risk register; note which risks materialized.
- After synthetic ground truth experiment completes: append a §10 summarizing the results table (passes/fails against pre-registered predictions). This is the bridge from this working doc to the manuscript's results section.
- After submission: archive a snapshot of this file as `PAPER1_WORKING_DOC_AT_SUBMISSION_[date].md` and continue updating the live version with reviewer feedback.

---

**End of working document.**
