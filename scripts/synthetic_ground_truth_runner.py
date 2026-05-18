#!/usr/bin/env python3
"""Run the preregistered synthetic-ground-truth validation analyses.

This script is intentionally separate from the original VIVAMACS simulation
engine. It applies candidate-level parameter changes in pandas, then calls the
existing model code without changing core model behavior.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import time as dt_time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from SALib.analyze import sobol
from SALib.sample import saltelli

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.notebook_refactor.config import (  # noqa: E402
    END_HOUR,
    PERIOD_IN_MINS,
    START_HOUR,
    TIME_TO_EXFIL,
    VIRUS_CLEANED,
)
from src.notebook_refactor.environment import (  # noqa: E402
    load_data,
    set_nearby_agents,
    setup_environment,
)
from src.notebook_refactor.simulation import run_iteration  # noqa: E402


CANDIDATES = {
    "A": PROJECT_ROOT / "data" / "Data5_typical.csv",
    "B1": PROJECT_ROOT / "data" / "Data5_B1_uniform_data_value.csv",
    "B3": PROJECT_ROOT / "data" / "Data5_B3_uniform_data_and_repair_value.csv",
}

PROBLEM = {
    "num_vars": 3,
    "names": ["patch", "AV", "awareness"],
    "bounds": [[0, 100], [0, 100], [0, 100]],
}


@dataclass(frozen=True)
class EvaluationResult:
    index: int
    data_loss: float
    repair_cost: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["smoke", "sobol", "cost-share", "all"],
        default="smoke",
        help="Analysis mode. Use smoke before any long run.",
    )
    parser.add_argument(
        "--candidate",
        choices=["A", "B1", "B3", "all"],
        default="all",
        help="Candidate to run.",
    )
    parser.add_argument("--n-base", type=int, default=1024, help="Saltelli base sample N.")
    parser.add_argument("--runs-per-sample", type=int, default=200, help="MC runs per Sobol parameter set.")
    parser.add_argument("--cost-share-runs", type=int, default=1000, help="MC runs for realized cost-share analysis.")
    parser.add_argument("--days", type=int, default=365, help="Simulation horizon in days.")
    parser.add_argument("--workers", type=int, default=max(1, min(os.cpu_count() or 1, 24)))
    parser.add_argument("--bootstrap-resamples", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260518)
    parser.add_argument("--output-dir", default="outputs/synthetic_ground_truth")
    return parser.parse_args()


def selected_candidates(candidate: str) -> dict[str, Path]:
    if candidate == "all":
        return CANDIDATES
    return {candidate: CANDIDATES[candidate]}


def apply_global_parameters(df: pd.DataFrame, params: np.ndarray) -> pd.DataFrame:
    patch_value, av_value, awareness_value = [float(value) for value in params]
    modified = df.copy(deep=True)

    patch_types = modified["type"].isin(["Server", "Firewall", "Router", "PC", "Mobile"])
    av_types = modified["type"].isin(["Server", "PC", "Mobile"])
    user_types = modified["type"] == "User"

    modified.loc[patch_types, "patch"] = patch_value
    modified.loc[av_types, "AV"] = av_value
    modified.loc[user_types, "aware"] = awareness_value
    return modified


def evaluate_parameter_set(
    candidate_path: str,
    params: np.ndarray,
    runs: int,
    days: int,
    seed: int,
    index: int,
) -> EvaluationResult:
    base_df = load_data(candidate_path)
    df = apply_global_parameters(base_df, params)
    agent_registry, device_agents, sigma_value = setup_environment(df)

    data_loss = np.zeros(runs)
    repair_cost = np.zeros(runs)
    for run_idx in range(runs):
        random.seed(seed + index * 1_000_003 + run_idx)
        result = run_iteration(run_idx, agent_registry, device_agents, sigma_value, days=days)
        data_loss[run_idx] = result["data_loss"]
        repair_cost[run_idx] = result["repair"]

    return EvaluationResult(
        index=index,
        data_loss=float(data_loss.mean()),
        repair_cost=float(repair_cost.mean()),
    )


def run_sobol_for_candidate(
    label: str,
    candidate_path: Path,
    args: argparse.Namespace,
    output_root: Path,
) -> None:
    candidate_dir = output_root / label
    candidate_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Sobol candidate {label} ===")
    print(f"Config: {candidate_path}")
    print(f"N={args.n_base}; runs/sample={args.runs_per_sample}; days={args.days}; workers={args.workers}")

    param_values = saltelli.sample(PROBLEM, args.n_base, calc_second_order=True)
    expected = args.n_base * (2 * PROBLEM["num_vars"] + 2)
    if len(param_values) != expected:
        raise RuntimeError(f"Unexpected Saltelli sample count: {len(param_values)} != {expected}")

    metadata = {
        "candidate": label,
        "candidate_path": str(candidate_path.relative_to(PROJECT_ROOT)),
        "problem": PROBLEM,
        "n_base": args.n_base,
        "sample_count": int(len(param_values)),
        "runs_per_sample": args.runs_per_sample,
        "days": args.days,
        "seed": args.seed,
        "bootstrap_resamples": args.bootstrap_resamples,
        "calc_second_order": True,
    }
    (candidate_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    np.save(candidate_dir / "saltelli_params.npy", param_values)

    data_loss_y = np.zeros(len(param_values))
    repair_y = np.zeros(len(param_values))
    start = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(
                evaluate_parameter_set,
                str(candidate_path),
                params,
                args.runs_per_sample,
                args.days,
                args.seed,
                index,
            )
            for index, params in enumerate(param_values)
        ]

        completed = 0
        for future in as_completed(futures):
            result = future.result()
            data_loss_y[result.index] = result.data_loss
            repair_y[result.index] = result.repair_cost
            completed += 1
            if completed == 1 or completed % 25 == 0 or completed == len(param_values):
                elapsed = max(time.time() - start, 1e-9)
                rate = completed / elapsed
                remaining = (len(param_values) - completed) / rate
                print(
                    f"{label}: {completed}/{len(param_values)} "
                    f"({completed / len(param_values):.1%}); ETA {remaining / 60:.1f} min",
                    flush=True,
                )

    np.save(candidate_dir / "Y_data_loss.npy", data_loss_y)
    np.save(candidate_dir / "Y_repair_cost.npy", repair_y)
    pd.DataFrame(
        {
            "data_loss": data_loss_y,
            "repair_cost": repair_y,
        }
    ).to_csv(candidate_dir / "model_outputs.csv", index=False)

    analyze_and_save_sobol(candidate_dir, "data_loss", data_loss_y, args)
    analyze_and_save_sobol(candidate_dir, "repair_cost", repair_y, args)


def analyze_and_save_sobol(
    candidate_dir: Path,
    outcome: str,
    values: np.ndarray,
    args: argparse.Namespace,
) -> None:
    indices = sobol.analyze(
        PROBLEM,
        values,
        calc_second_order=True,
        num_resamples=args.bootstrap_resamples,
        seed=args.seed,
        print_to_console=False,
    )
    rows = []
    for idx, name in enumerate(PROBLEM["names"]):
        rows.append(
            {
                "outcome": outcome,
                "parameter": name,
                "S1": float(indices["S1"][idx]),
                "S1_conf": float(indices["S1_conf"][idx]),
                "ST": float(indices["ST"][idx]),
                "ST_conf": float(indices["ST_conf"][idx]),
            }
        )
    pd.DataFrame(rows).to_csv(candidate_dir / f"sobol_{outcome}.csv", index=False)


def random_gen(sigma_value: float, low: int = 1, high: int = 100, mu: int = 50) -> int:
    while True:
        value = random.gauss(mu, sigma_value)
        if low <= value <= high:
            return int(round(value))


def agent_class(agent_type: str) -> str:
    if agent_type in {"Server", "PC", "Mobile", "Firewall", "Router"}:
        return agent_type
    return "Other"


def shares(values: dict[str, float]) -> dict[str, float]:
    total = float(sum(values.values()))
    if total <= 0:
        return {key: 0.0 for key in values}
    return {key: float(value) / total for key, value in values.items()}


def traced_iteration(
    iteration_idx: int,
    candidate_path: str,
    days: int,
    seed: int,
) -> dict[str, Any]:
    random.seed(seed + iteration_idx)
    df = load_data(candidate_path)
    agent_registry, device_agents, sigma_value = setup_environment(df)

    for agent in agent_registry["all"]:
        agent.Status = 0
        agent.time_infected = 0
        agent.nearby = 0

    data_by_class: dict[str, float] = {"Server": 0.0, "PC": 0.0, "Mobile": 0.0}
    repair_by_class: dict[str, float] = {"Server": 0.0, "PC": 0.0, "Mobile": 0.0, "Firewall": 0.0, "Router": 0.0}
    compromise_events: dict[str, float] = {"Server": 0.0, "PC": 0.0, "Mobile": 0.0, "Firewall": 0.0, "Router": 0.0, "Other": 0.0}
    compromise_periods: dict[str, float] = {"Server": 0.0, "PC": 0.0, "Mobile": 0.0, "Firewall": 0.0, "Router": 0.0, "Other": 0.0}

    within_infected_pair_periods = 0
    across_infected_pair_periods = 0
    possible_within_pair_periods = 0
    possible_across_pair_periods = 0
    all_devices = [agent for agents in device_agents.values() for agent in agents]
    pair_vlan_relation = compute_pair_vlan_relation(all_devices)

    for day in range(days):
        for hour in range(START_HOUR, END_HOUR, 1):
            for minute in range(0, 60, PERIOD_IN_MINS):
                current_time = dt_time(hour, minute)

                for agents in device_agents.values():
                    for agent in agents:
                        if not agent.is_active(current_time):
                            continue

                        attack = random_gen(sigma_value)
                        if agent.nearby == 1 and random_gen(sigma_value) <= agent.strength:
                            agent.nearby = 0

                        if agent.type == "Server":
                            if agent.Status == 0:
                                if attack > agent.strength or agent.nearby == 1:
                                    infect(agent, compromise_events, data_by_class, agent_registry)
                            elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.AV:
                                clean(agent, repair_by_class)
                            else:
                                accrue_infected_period(agent, data_by_class)

                        elif agent.type == "Firewall":
                            if agent.Status == 0:
                                if attack > agent.strength or agent.nearby == 1:
                                    infect(agent, compromise_events, data_by_class, agent_registry)
                            elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.strength:
                                clean(agent, repair_by_class)
                            else:
                                agent.time_infected += PERIOD_IN_MINS

                        elif agent.type == "Mobile":
                            if agent.Status == 0:
                                user_act = random_gen(sigma_value)
                                if attack > agent.strength and (user_act > agent.vulnerability or agent.nearby == 1):
                                    infect(agent, compromise_events, data_by_class, agent_registry)
                            elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.AV:
                                clean(agent, repair_by_class)
                            else:
                                accrue_infected_period(agent, data_by_class)

                        elif agent.type == "PC":
                            if agent.Status == 0:
                                user_act = random_gen(sigma_value)
                                if attack > agent.strength and (user_act > agent.vulnerability or agent.nearby == 1):
                                    infect(agent, compromise_events, data_by_class, agent_registry)
                            elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.AV:
                                clean(agent, repair_by_class)
                            else:
                                accrue_infected_period(agent, data_by_class)

                        else:
                            if agent.Status == 0:
                                if attack > agent.strength:
                                    infect(agent, compromise_events, data_by_class, agent_registry)
                            elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.strength:
                                agent.Status = 0
                                agent.time_infected = 0
                            else:
                                agent.time_infected += PERIOD_IN_MINS

                for device in all_devices:
                    if device.Status == 1:
                        compromise_periods[agent_class(device.type)] += 1

                infected = [device for device in all_devices if device.Status == 1]
                infected_names = {device.name for device in infected}
                for (left, right), same_vlan in pair_vlan_relation.items():
                    if same_vlan:
                        possible_within_pair_periods += 1
                    else:
                        possible_across_pair_periods += 1
                    if left in infected_names and right in infected_names:
                        if same_vlan:
                            within_infected_pair_periods += 1
                        else:
                            across_infected_pair_periods += 1

    total_data_loss = float(sum(data_by_class.values()))
    total_repair = float(sum(repair_by_class.values()))
    within_rate = within_infected_pair_periods / possible_within_pair_periods if possible_within_pair_periods else 0.0
    across_rate = across_infected_pair_periods / possible_across_pair_periods if possible_across_pair_periods else 0.0
    lateral_ratio = math.inf if across_rate == 0 and within_rate > 0 else (within_rate / across_rate if across_rate else 0.0)

    return {
        "iteration": iteration_idx,
        "data_loss": total_data_loss,
        "repair_cost": total_repair,
        "total_cost": total_data_loss + total_repair,
        "data_by_class": data_by_class,
        "repair_by_class": repair_by_class,
        "compromise_events": compromise_events,
        "compromise_periods": compromise_periods,
        "data_share": shares(data_by_class),
        "repair_share": shares(repair_by_class),
        "compromise_event_share": shares(compromise_events),
        "compromise_period_share": shares(compromise_periods),
        "within_pair_rate": within_rate,
        "across_pair_rate": across_rate,
        "lateral_clustering_ratio": lateral_ratio,
    }


def compute_pair_vlan_relation(agents: list[Any]) -> dict[tuple[str, str], bool]:
    relation: dict[tuple[str, str], bool] = {}
    for left_index, left in enumerate(agents):
        left_vlans = set(getattr(left, "VLAN", []) or [])
        for right in agents[left_index + 1 :]:
            right_vlans = set(getattr(right, "VLAN", []) or [])
            relation[(left.name, right.name)] = bool(left_vlans & right_vlans)
    return relation


def infect(
    agent: Any,
    compromise_events: dict[str, float],
    data_by_class: dict[str, float],
    agent_registry: dict[str, Any],
) -> None:
    agent.Status = 1
    agent.time_infected = 0
    compromise_events[agent_class(agent.type)] += 1
    if agent.type in data_by_class:
        data_by_class[agent.type] += agent.Data_Value * PERIOD_IN_MINS / TIME_TO_EXFIL
    set_nearby_agents(agent, agent_registry["all"])


def clean(agent: Any, repair_by_class: dict[str, float]) -> None:
    agent.Status = 0
    agent.time_infected = 0
    if agent.type in repair_by_class:
        repair_by_class[agent.type] += agent.Repair_Value


def accrue_infected_period(agent: Any, data_by_class: dict[str, float]) -> None:
    agent.time_infected += PERIOD_IN_MINS
    if agent.type in data_by_class:
        data_by_class[agent.type] += agent.Data_Value * PERIOD_IN_MINS / TIME_TO_EXFIL


def run_cost_share(candidate_path: Path, args: argparse.Namespace, output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    print(f"\n=== Cost-share Candidate A ===")
    print(f"Config: {candidate_path}")
    print(f"runs={args.cost_share_runs}; days={args.days}; workers={args.workers}")

    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(traced_iteration, idx, str(candidate_path), args.days, args.seed)
            for idx in range(args.cost_share_runs)
        ]
        for completed, future in enumerate(as_completed(futures), start=1):
            rows.append(flatten_trace_result(future.result()))
            if completed == 1 or completed % 25 == 0 or completed == len(futures):
                print(f"cost-share: {completed}/{len(futures)}", flush=True)

    df = pd.DataFrame(rows).sort_values("iteration")
    df.to_csv(output_root / "candidate_A_cost_share_iterations.csv", index=False)
    summary = summarize_cost_share(df)
    summary.to_csv(output_root / "candidate_A_cost_share_summary.csv", index=False)
    print(summary.to_string(index=False))


def flatten_trace_result(result: dict[str, Any]) -> dict[str, Any]:
    flat = {
        "iteration": result["iteration"],
        "data_loss": result["data_loss"],
        "repair_cost": result["repair_cost"],
        "total_cost": result["total_cost"],
        "within_pair_rate": result["within_pair_rate"],
        "across_pair_rate": result["across_pair_rate"],
        "lateral_clustering_ratio": result["lateral_clustering_ratio"],
    }
    for group in ["data_share", "repair_share", "compromise_event_share", "compromise_period_share"]:
        for key, value in result[group].items():
            flat[f"{group}_{key}"] = value
    return flat


def summarize_cost_share(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "data_loss",
        "repair_cost",
        "total_cost",
        "data_share_Server",
        "compromise_event_share_Server",
        "compromise_period_share_Server",
        "lateral_clustering_ratio",
    ]
    rows = []
    for metric in metrics:
        values = df[metric].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
        if len(values) == 0:
            rows.append({"metric": metric, "mean": np.nan, "p50": np.nan, "p95": np.nan})
            continue
        rows.append(
            {
                "metric": metric,
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "p25": float(np.percentile(values, 25)),
                "p50": float(np.percentile(values, 50)),
                "p75": float(np.percentile(values, 75)),
                "p95": float(np.percentile(values, 95)),
            }
        )
    return pd.DataFrame(rows)


def run_smoke(args: argparse.Namespace) -> None:
    print("Smoke test only; not a paper result.")
    for label, path in selected_candidates(args.candidate).items():
        df = load_data(str(path))
        agent_registry, device_agents, sigma_value = setup_environment(df)
        random.seed(args.seed)
        result = run_iteration(0, agent_registry, device_agents, sigma_value, days=1)
        print(
            label,
            {
                "rows": len(df),
                "sigma": sigma_value,
                "device_types": sorted(device_agents),
                "data_loss": result["data_loss"],
                "repair_cost": result["repair"],
            },
        )


def main() -> None:
    args = parse_args()
    output_root = PROJECT_ROOT / args.output_dir
    output_root.mkdir(parents=True, exist_ok=True)

    if args.mode in {"smoke", "all"}:
        run_smoke(args)

    if args.mode in {"sobol", "all"}:
        for label, path in selected_candidates(args.candidate).items():
            run_sobol_for_candidate(label, path, args, output_root / "sobol")

    if args.mode in {"cost-share", "all"}:
        run_cost_share(CANDIDATES["A"], args, output_root / "cost_share")


if __name__ == "__main__":
    main()

