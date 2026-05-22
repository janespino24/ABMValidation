# Pre-Registration: Synthetic Ground Truth Validation Experiment

**Author:** Jan-Michael B. Espino
**Date filed:** 18 May 2026
**Target paper:** Validation Methodologies for Agent-Based Cyber Risk Models (Paper 1, target venue: Simulation Modelling Practice & Theory)
**Pre-registration status:** Predictions and thresholds specified prior to execution of the experimental Sobol runs and Candidate B configurations. This document is committed to the project repository with a timestamp prior to results being available.

---

## 1. Purpose

This document pre-registers the predictions, thresholds, and analysis plan for the synthetic ground truth validation experiment described in §X of the manuscript. The purpose is to demonstrate that the proposed six-tier validation framework correctly identifies the structural properties of a known truth process, and correctly flags a deliberately weakened candidate model that lacks those properties. Pre-registration eliminates the risk that thresholds were tuned post hoc to match observed results.

## 2. The truth process

The truth process is the agent-based simulation model documented in `MODEL_ALGORITHM.md` configured with the parameter file `Data5_typical.csv`. The model simulates a stylized organizational network containing 8 users, 4 PCs, 4 mobile devices, 3 servers, 3 firewalls, 2 internet gateways, and 11 VLAN segments. Breach cost arises through two mechanisms:

- **Data loss** accrues at rate `Data_Value / 12` per 5-minute infected period for servers, PCs, and mobile devices.
- **Repair cost** is charged once per recovery event at the asset's `Repair_Value` and applies to servers, PCs, mobiles, firewalls, and routers.

Asset values in the Data5 configuration concentrate as follows:

| Asset class | Data_Value share | Repair_Value share |
|---|---:|---:|
| Servers (3) | 95.4% | 90.9% |
| PCs (4) | 2.3% | 2.9% |
| Mobiles (4) | 2.3% | 5.1% |
| Firewalls (3) | 0% | 1.1% |

The Sobol sensitivity analysis varies three parameters globally over [0, 100]: `patch`, `AV`, and `awareness`. These enter the model as follows:

- `patch` enters the strength formula for all defended agent classes (servers, firewalls, routers, PCs, mobiles).
- `AV` enters strength for servers, PCs, and mobiles, and is the recovery threshold for those classes.
- `awareness` enters the user-driven vulnerability term, which affects only PCs and mobiles.

Critically, `awareness` is structurally locked out of affecting servers, firewalls, and routers. The model thus encodes a specific structural relationship between parameter sensitivities and cost outcomes, which the validation framework is required to recover.

## 3. Candidate models

- **Candidate A (truth):** the model configured with `Data5_typical.csv` as supplied.
- **Candidate B1 (uniform data value):** identical to Candidate A in every respect except that `Data_Value` is replaced with its mean across every device that currently has a nonzero `Data_Value` ($167,727.27 in the verified Data5 configuration). Network topology, control levels, repair values, threat parameters, and all other configuration remain unchanged. This represents the implicit assumption — common in unweighted control frameworks — that all assets carry equivalent data exposure.
- **Candidate B3 (uniform both):** identical to B1 with the additional change that `Repair_Value` is replaced with its mean across all classes that incur repair cost. This represents complete decoupling of cost outcomes from asset-class structure.

Candidate B2 (uniform repair only) was considered and excluded; it tests a less mechanism-relevant alternative.

## 4. Pre-registered predictions and thresholds

The following predictions are specified before Sobol re-run results are available. The framework is judged to have correctly discriminated between truth (A) and weakened candidates (B1, B3) if Candidate A meets all predictions and Candidates B1/B3 fail at the predicted patterns.

### Sobol sensitivity predictions (parameter attribution)

| ID | Prediction | Threshold for Candidate A | Expected for B1 | Expected for B3 |
|---|---|---|---|---|
| **P1** | `AV` dominates Sobol S_T for data loss | S_T(AV) ≥ 0.50 and S_T(AV) > S_T(patch), S_T(awareness) | reduced; AV may no longer dominate | fails |
| **P2** | `awareness` has near-zero S_T for data loss | S_T(awareness) ≤ 0.10 | increases (awareness gains relative importance) | increases |
| **P3** | `awareness` has non-zero S_T for repair cost | S_T(awareness) ≥ 0.05 | unchanged (repair distribution unchanged in B1) | fails (uniform repair) |
| **P4** | Differential awareness sensitivity across cost streams | S_T(awareness, repair) − S_T(awareness, data) > 0.03 | differential shrinks or inverts | fails or undefined |

### Realized-cost-share predictions (asset attribution)

| ID | Prediction | Threshold for Candidate A | Expected for B1 | Expected for B3 |
|---|---|---|---|---|
| **P5** | Server data-loss share exceeds asset-value share | Server share of realized data loss ≥ 0.85 | fails (no concentration) | fails |
| **P6** | Server compromise share less than cost share | Server share of compromise events < 0.50 | unchanged | unchanged |

### Distributional and structural predictions

| ID | Prediction | Threshold for Candidate A | Expected for B1 | Expected for B3 |
|---|---|---|---|---|
| **P7** | Heavy-tailed data loss distribution | P95 / median ≥ 3.0 | likely holds but magnitude reduced | likely holds |
| **P8** | Lateral-movement clustering within VLANs | Within-VLAN co-compromise rate ≥ 2× across-VLAN | holds (mechanism unchanged) | holds |

### Summary of expected discrimination

A successful framework should produce the following pattern across the three candidates:

| Prediction | Candidate A | Candidate B1 | Candidate B3 |
|---|:-:|:-:|:-:|
| P1 | pass | partial / fail | fail |
| P2 | pass | fail (increases) | fail (increases) |
| P3 | pass | pass | fail |
| P4 | pass | fail | fail |
| P5 | pass | fail | fail |
| P6 | pass | pass | pass |
| P7 | pass | partial | partial |
| P8 | pass | pass | pass |

P6 and P8 are expected to pass for all candidates because they test mechanisms (compromise propagation and VLAN clustering) that are not modified between configurations. They are included as **null-control predictions** — if the framework reports differences here, that itself is evidence of spurious sensitivity and should be investigated.

The framework discriminates correctly if the pattern of passes and fails across the four substantive predictions (P1–P5) matches the expected discrimination above.

## 5. Analysis plan

### Sobol sensitivity computation

Sobol first-order (S_1) and total-order (S_T) indices are computed using the Saltelli sampling scheme with N = 1024 base samples, yielding (2k + 2) × N = 8,192 model evaluations per output, where k = 3 is the number of varied parameters. Each model evaluation is averaged over 200 Monte Carlo iterations of the underlying simulation. Total simulation count per candidate model is approximately 1,638,400.

Pre-run implementation clarification: the Saltelli design is generated with second-order sampling enabled because this is the SALib option that yields the pre-registered `(2k + 2) × N` sample count. The reported sensitivity statistics remain first-order and total-order indices.

Sobol indices are computed separately for two outputs:
- Total data loss across the simulation period
- Total repair cost across the simulation period

Confidence intervals on Sobol indices are computed by bootstrap resampling of the SALib output (B = 1000 resamples).

### Realized-cost-share computation

For 1,000 Monte Carlo iterations of Candidate A run at default parameters, the following statistics are computed and aggregated across iterations:

- Total data loss attributed to each asset class (server, PC, mobile)
- Total compromise-period count for each asset class
- Total repair events for each asset class

Statistics are reported as means with 95% bootstrap confidence intervals.

Pre-run implementation clarification: P8 is computed as a period-level device-pair statistic. The within-VLAN co-compromise rate equals infected device-pair periods among pairs sharing at least one VLAN divided by possible same-VLAN device-pair periods. The across-VLAN rate uses pairs with no shared VLAN. The lateral-clustering statistic is `within_rate / across_rate`.

### Pattern detection

The four pattern statistics (P5–P8) are computed as documented in §5.3 of the manuscript. Threshold comparisons are made using the point estimates with bootstrap confidence intervals reported alongside.

## 6. Stopping rule

Sobol runs are executed for all three candidates concurrently using the existing simulation infrastructure. No interim analysis is performed prior to completion of all three runs. Results are reported as committed in this document.

## 7. What would falsify the framework

The framework is considered to have failed the synthetic ground truth test under any of the following outcomes:

- **Failure mode 1:** Candidate A fails three or more of P1–P5 (the framework cannot recover the truth process).
- **Failure mode 2:** Candidate B1 or B3 passes both P1 and P5 (the framework cannot distinguish the weakened candidate from the truth).
- **Failure mode 3:** Any pattern statistic (P6, P8) shows large differences across candidates (the framework shows spurious sensitivity to factors not varied between configurations).

In the event of any failure mode, the result is reported as filed and discussed as a substantive finding about the framework's discriminative boundary, not as a defect of the experimental design.

## 8. Limitations explicitly acknowledged

- Sobol indices are computed over globally varying parameters. Asset-class-specific control attribution (e.g., separating server AV from endpoint AV) would require an expanded sensitivity analysis with k > 3 dimensions and is reserved for Paper 2.
- The truth process is a single network configuration. Cross-configuration generalization is not claimed in this experiment and is the subject of Paper 2's broader calibration.
- The Candidate B variants test asset-value uniformity specifically. Other forms of misspecification (e.g., incorrect topology, missing lateral movement) are not tested in this experiment.
- The pattern thresholds in P1–P8 reflect the truth process documented above. They are not universal constants and should not be applied to other ABM cyber risk models without re-derivation from the relevant data-generating process.

## 9. Repository commit reference

This document is committed to the project repository at the following location prior to execution of the Sobol runs for Candidates B1 and B3:

- File: `docs/preregistrations/synthetic_ground_truth_2026-05-18.md`
- Commit hash: `dda10857409d075f6539de63341cff268d16f225`
- Commit date: `2026-05-18 10:01:00 +0800`

The commit timestamp is the canonical evidence that predictions were specified ex-ante. Any modifications to this document after the commit are tracked via git history and disclosed in the manuscript.

Pre-experiment clarification: before any Candidate A/B1/B3 Sobol or smoke-test results were generated, the Data5 configuration file was inspected and the B1 parenthetical mean was corrected from the planning estimate to the verified value above. The operational candidate definition remains unchanged: uniform replacement across devices with nonzero `Data_Value`.

Pre-run implementation clarification added on 2026-05-22: before full experimental execution, the runner's Saltelli sample count, realized-cost-share iteration count, and P8 within/across-VLAN co-compromise operationalization were recorded here to remove ambiguity between the pre-registered threshold and executable analysis code.
Post-dry-run decision recorded on 2026-05-22: medium diagnostic dry runs indicated that P6 and P8 may fail under the current Data5 truth process and operational definitions. The thresholds and expected patterns are not revised. The full experiment will be run and reported as preregistered; any P6/P8 failures will be disclosed as null-control diagnostic findings rather than corrected post hoc.

---

**End of pre-registration.**
