# Section X. Synthetic Ground Truth Validation

*Manuscript scaffold — Paper 1 (SIMPAT submission)*
*Generated: 18 May 2026*

> **How to use this file.** This is a drafting scaffold for the synthetic ground truth section of the manuscript. Prose is written at submission quality. Placeholders marked `[TBD-Sobol]`, `[TBD-Cost]`, etc. are filled in after the experimental runs complete. Tables are structured but values are placeholders. Replace the markdown headings with your manuscript's section numbering and adapt the citation style to SIMPAT's house format (Elsevier numeric).

---

## X.1 Motivation

Empirical validation of an agent-based cyber risk model against held-out data is constrained by a fundamental observability problem: ground truth for cyber-risk outcomes — which assets compromise, in what order, with what loss — is rarely available at the granularity the model produces, and never for the counterfactuals the model is intended to inform. We address this by constructing a synthetic truth process whose structural properties are known by design, and evaluating whether the proposed validation framework correctly recovers those properties.

This approach inverts the conventional validation question. Rather than asking "does the model match the world?", which requires assumptions about which features of the world the data captures, we ask "does the validation framework correctly identify a model whose generative structure is fully specified?" If the framework correctly distinguishes a model that encodes a known truth from a model that lacks the relevant structural features, the framework has demonstrated discriminative validity on a controlled test. This is a necessary, though not sufficient, condition for trusting the framework's verdicts on models whose ground truth is uncertain.

The synthetic ground truth experiment is structured around three commitments specified prior to execution: a documented truth process, a set of pre-registered predictions about what the framework should detect, and one or more candidate models that vary in whether they encode the truth process's structural properties.

## X.2 The truth process

The truth process is the agent-based model documented in Section [REF-METHODS] configured with parameter file `Data5_typical.csv`. The configuration specifies a stylized organizational network with the following asset structure:

| Asset class | Count | Data_Value share | Repair_Value share |
|---|---:|---:|---:|
| Servers | 3 | 95.4% | 90.9% |
| PCs | 4 | 2.3% | 2.9% |
| Mobiles | 4 | 2.3% | 5.1% |
| Firewalls | 3 | 0% | 1.1% |
| Routers, internet, users | 7 | 0% | 0% |

Two cost mechanisms operate concurrently. Data loss accrues at rate `Data_Value / 12` per five-minute infected period for servers, PCs, and mobile devices. Repair cost is charged once per recovery event at the asset's `Repair_Value` and applies additionally to firewalls and routers. The two streams have structurally different generators: data loss is *duration-driven* and concentrated at high-value servers, while repair cost is *event-driven* and distributed across a broader set of devices.

Sensitivity analysis varies three control parameters globally over [0, 100]: `patch`, `AV`, and `awareness`. These enter the model's defensive strength formulas with structurally distinct reach. `patch` enters the strength formula for all defended agent classes. `AV` enters strength for servers, PCs, and mobiles and is the recovery threshold for those same classes. `awareness` enters the user-driven vulnerability term, which affects only PCs and mobile devices. The parameter `awareness` is therefore structurally locked out of affecting servers, firewalls, and routers — a property of the truth process that the validation framework is required to recover.

## X.3 Pre-registered predictions

Predictions and their quantitative thresholds were specified prior to execution of the Sobol runs and committed to the project repository (Appendix [REF-PREREG]) on 18 May 2026. Predictions fall into three groups: Sobol-based parameter attribution, realized-cost-share asset attribution, and distributional/structural patterns. Two predictions (P6, P8) are deliberately included as **null-control predictions** — they test mechanisms that are not varied between candidate models and are expected to hold across all candidates. Spurious differences in these predictions would indicate that the framework is detecting variation that does not exist.

The full pre-registration table appears as Table X.1.

**Table X.1.** Pre-registered predictions and thresholds. ✓ denotes expected pass; ✗ expected fail; ~ indicates a null-control prediction expected to hold across all candidates.

| # | Prediction (truth process: Data5) | Threshold | Cand. A | Cand. B1 | Cand. B3 |
|---|---|---|:---:|:---:|:---:|
| P1 | `AV` dominates S_T for data loss | S_T(AV) ≥ 0.50 and largest of the three | ✓ | ✗ | ✗ |
| P2 | `awareness` has near-zero S_T for data loss | S_T(awareness) ≤ 0.10 | ✓ | ✗ | ✗ |
| P3 | `awareness` has non-zero S_T for repair cost | S_T(awareness) ≥ 0.05 | ✓ | ✓ | ✗ |
| P4 | Differential: S_T(awareness, repair) > S_T(awareness, data) | difference > 0.03 | ✓ | ✗ | ✗ |
| P5 | Server data-loss share | ≥ 0.85 | ✓ | ✗ | ✗ |
| P6 | Server compromise share | < 0.50 | ~ | ~ | ~ |
| P7 | Heavy-tailed loss (P95 / median) | ≥ 3.0 | ✓ | partial | partial |
| P8 | Lateral-movement clustering (within/across-VLAN ratio) | ≥ 2× | ~ | ~ | ~ |

Three features of this design merit emphasis. First, **P4 is a differential prediction** — it asserts not merely that `awareness` has a small effect on data loss, but that its effect on data loss is smaller than its effect on repair cost by a specified margin. Differential predictions are harder to satisfy by chance than single-magnitude predictions and provide stronger evidence of mechanism recovery. Second, **P5 and P6 are jointly informative** — high data-loss share *combined with* low compromise share at servers is the structural signature of asset-value concentration, the mechanism that motivates Paper 2's substantive finding. Third, **the null-control predictions P6 and P8** test whether the framework's pattern detectors exhibit spurious sensitivity to factors not varied between candidates. Their inclusion follows the recommendation of [CITE: Augusiak et al. 2014] that pattern-oriented validation requires explicit consideration of false-positive risk.

## X.4 Candidate models

Three model configurations are compared:

**Candidate A (truth process):** the model as configured by `Data5_typical.csv`. This is the reference against which the validation framework's outputs are evaluated.

**Candidate B1 (uniform data value):** identical to Candidate A in network topology, control levels, repair values, threat parameters, and recovery logic, but with `Data_Value` replaced by its mean across all asset classes that currently carry nonzero data value. This represents the implicit assumption — common in unweighted control frameworks such as NIST CSF 2.0 Profiles, CIS Controls v8 Implementation Groups, and ISO/IEC 27001:2022 Annex A — that asset categories carry equivalent data exposure. Candidate B1 tests whether the validation framework correctly identifies the *absence* of asset-value concentration when concentration is removed.

**Candidate B3 (uniform both):** Candidate B1 with the additional modification that `Repair_Value` is replaced by its mean across cost-incurring asset classes. This represents complete decoupling of cost outcomes from asset-class structure and provides the strongest contrast against the truth process.

Candidate B1 is selected as the primary alternative because it isolates the data-value concentration mechanism — the specific structural feature the framework is intended to detect — without confounding it with repair-cost effects. Candidate B3 is included as a stronger-contrast secondary alternative. A third logically possible candidate (uniform repair value with intact data value) was considered and excluded as testing a less mechanism-relevant alternative.

Candidates B1 and B3 are deliberately *plausible* rather than obviously broken. Both reproduce the network topology, agent behaviour, threat parameterization, and control structure of Candidate A. They differ only in the asset-valuation assumption — an assumption that is empirically defensible but, we contend, structurally inadequate for cyber risk quantification in environments with realistic asset concentration. The framework's discriminative claim is precisely the ability to flag this inadequacy through quantitative pattern detection rather than ex-ante design judgement.

## X.5 Methods: two complementary attribution paths

Two distinct attributional analyses are applied to each candidate, addressing complementary questions.

**Sobol sensitivity analysis** decomposes the variance in each cost outcome (data loss, repair cost) across the three globally varying parameters (`patch`, `AV`, `awareness`). This answers the question: *which control type, varied uniformly across all defended agents, explains the most variance in each cost stream?* Indices are computed using the Saltelli sampling scheme with N = 1024 base samples following [CITE: Saltelli et al. 2008], yielding (2k + 2) × N = 8,192 parameter combinations per candidate, each averaged over 200 Monte Carlo iterations of the underlying simulation. The Saltelli design is generated with second-order sampling enabled to preserve this pre-registered sample count; the manuscript reports first-order and total-order indices. Total simulation count per candidate is approximately 1.64 × 10⁶. Bootstrap confidence intervals (B = 1000 resamples) are reported alongside point estimates.

**Realized-cost-share analysis** decomposes simulated cost outcomes by asset class, conditional on compromise. This answers a complementary question: *given the realized trajectory of compromise events, what share of each cost stream accrues to which asset class?* For 1,000 Monte Carlo iterations of Candidate A at default parameter values, the cost contribution of each asset class to total data loss and to total repair cost is recorded. Mean shares and 95% bootstrap confidence intervals are reported across iterations.

For P8, the within-VLAN co-compromise rate is operationalized as the number of infected device-pair periods among device pairs that share at least one VLAN, divided by the number of possible same-VLAN device-pair periods over the simulation horizon. The across-VLAN rate is computed analogously for device pairs with no shared VLAN. The lateral-clustering statistic is the ratio of these two rates, with the pre-registered pass threshold set at within/across >= 2.

The two analyses are complementary rather than redundant. Sobol indices identify *which control parameter* moves the cost outcome most when varied; realized cost shares identify *which asset class* the cost actually accrues to. The combination is necessary to support the structural claim that motivates Paper 2: that variance in cost is driven by AV-class controls *and* that variance manifests disproportionately at high-value servers, jointly implying that asset-weighted control prioritization is the optimal investment strategy.

We note here a deliberate scope limitation: the Sobol decomposition reported in this paper varies parameters globally rather than per asset class. An asset-class-specific Sobol decomposition (e.g., separating server AV from endpoint AV as independent parameters) would more directly support an asset-weighted prioritization claim. Such an analysis requires k ≥ 9 dimensions in the Saltelli sample and is reserved for the calibrated-model analysis in Paper 2 [CITE-FORTHCOMING]. The realized-cost-share statistics provide a complementary, model-internal route to asset-class attribution sufficient for the discriminative claim of the present paper.

## X.6 Results

*[Subsection to be completed after experimental runs]*

Table X.2 reports Sobol total-order indices for each candidate against each cost outcome, with bootstrap 95% confidence intervals.

**Table X.2.** Sobol total-order sensitivity indices (point estimate [95% CI]). *Values are placeholders pending experimental completion.*

| Outcome | Parameter | Candidate A | Candidate B1 | Candidate B3 |
|---|---|---|---|---|
| Data loss | `patch` | [TBD-Sobol] | [TBD-Sobol] | [TBD-Sobol] |
| Data loss | `AV` | [TBD-Sobol] | [TBD-Sobol] | [TBD-Sobol] |
| Data loss | `awareness` | [TBD-Sobol] | [TBD-Sobol] | [TBD-Sobol] |
| Repair cost | `patch` | [TBD-Sobol] | [TBD-Sobol] | [TBD-Sobol] |
| Repair cost | `AV` | [TBD-Sobol] | [TBD-Sobol] | [TBD-Sobol] |
| Repair cost | `awareness` | [TBD-Sobol] | [TBD-Sobol] | [TBD-Sobol] |

Table X.3 reports realized cost shares by asset class for Candidate A, with bootstrap 95% confidence intervals over Monte Carlo iterations.

**Table X.3.** Realized cost share by asset class, Candidate A. *Values are placeholders pending experimental completion.*

| Asset class | Data-loss share | Compromise-period share | Repair-event share |
|---|---|---|---|
| Servers | [TBD-Cost] | [TBD-Cost] | [TBD-Cost] |
| PCs | [TBD-Cost] | [TBD-Cost] | [TBD-Cost] |
| Mobiles | [TBD-Cost] | [TBD-Cost] | [TBD-Cost] |
| Firewalls | — | [TBD-Cost] | [TBD-Cost] |

Table X.4 reports the comparison of pre-registered predictions against observed outcomes across the three candidates.

**Table X.4.** Pre-registered predictions versus observed outcomes. *Values are placeholders pending experimental completion.*

| # | Prediction | Cand. A observed | Cand. A pass? | Cand. B1 pass? | Cand. B3 pass? | Matches pre-reg? |
|---|---|---|:---:|:---:|:---:|:---:|
| P1 | S_T(AV) ≥ 0.50 for data loss | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| P2 | S_T(awareness) ≤ 0.10 for data loss | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| P3 | S_T(awareness) ≥ 0.05 for repair | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| P4 | Differential S_T(awareness) | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| P5 | Server data-loss share ≥ 0.85 | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| P6 | Server compromise share < 0.50 | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| P7 | P95/median ≥ 3.0 | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| P8 | Lateral clustering ratio ≥ 2× | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

## X.7 Interpretation

*[Subsection to be completed after experimental runs. Suggested structure:]*

Pre-run diagnostic note: dry-run diagnostics conducted after preregistration, but before the full experiment, suggested that P6 and P8 may fail under the current Data5 truth process and operational definitions. We therefore retain P6 and P8 exactly as preregistered and report them transparently as null-control diagnostics. A failure of P6 or P8 in the full experiment is interpreted as evidence about the specificity of those null-control expectations, not as a reason to revise the thresholds post hoc.

- **Headline finding:** state whether the framework discriminated correctly between truth and weakened candidates. Frame as "the framework reproduces the pre-registered pattern of passes and fails across [N] of 8 predictions" rather than as a binary verdict.
- **Mechanism recovery:** discuss specifically whether P4 (differential awareness sensitivity) held, since this is the strongest single piece of evidence for mechanism-level recovery rather than headline-magnitude recovery.
- **Null-control behaviour:** confirm that P6 and P8 produced similar values across candidates, or discuss any spurious differences as a limitation of pattern detector specificity.
- **Surprises:** any prediction that failed unexpectedly is reported as a substantive finding about the framework's discriminative boundary, not as a failure of the experiment. If Candidate A unexpectedly fails a prediction, this is honest evidence about the framework's range of applicability.
- **What the experiment does not establish:** the discriminative power demonstrated here is specific to the contrast tested (asset-value concentration). The framework's behaviour against other forms of misspecification — incorrect topology, missing lateral-movement mechanisms, misspecified threat distributions — is not tested in this paper and is acknowledged as a limitation in Section [REF-LIMITATIONS].

## X.8 Threats to validity

Three principal threats to the validity of this experiment are acknowledged.

*Construct validity.* The pre-registered thresholds in P1–P8 reflect quantitative judgements about what counts as detection. Different thresholds would produce different pass/fail patterns. We mitigate this by deriving thresholds from the truth process where possible (e.g., the 0.85 threshold for P5 reflects the 95.4% Data_Value concentration documented in §X.2) and by reporting all underlying point estimates and confidence intervals so that readers can apply alternative thresholds.

*External validity.* The truth process is a single network configuration. Generalizability of the framework's discriminative behaviour to other configurations is not established by this experiment alone. We address this by deferring cross-configuration validation to the calibrated-model analysis in Paper 2 [CITE-FORTHCOMING] and by specifying in §X.3 that the present experiment establishes a *necessary* but not *sufficient* condition for framework trustworthiness.

*Researcher degrees of freedom.* The selection of Candidates B1 and B3, and the exclusion of an alternative (B2: uniform repair only), constitutes a researcher choice that could in principle have been made post hoc to produce favourable results. We mitigate this through pre-registration of the candidate set and rationale in Appendix [REF-PREREG], committed to the project repository on 18 May 2026.

---

**End of section scaffold.**
