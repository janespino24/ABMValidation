import os
import argparse
import math
import time
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from .config import ITERATIONS
from .environment import load_data, setup_environment, value_clean
from .simulation import SimulationStats, run_iteration

# Re-implement strength calc for Servers to avoid heavy refactoring
def update_server_strength(agent, val_override):
    # Set attributes
    agent.patch = val_override
    agent.ports = val_override
    agent.AV = val_override
    
    # Recalculate Strength
    # strength = (patch * ports * AV * net_strength) ^ 1/4
    nst = getattr(agent, 'net_strength', 10)
    
    # Logic from environment.py
    val = agent.patch * agent.ports * agent.AV * nst
    strength = round(math.pow(value_clean(val), 0.25))
    agent.strength = int(strength)

def run_sweep(data_path, runs=1000, days=365):
    print(f"LOADING DATA: {data_path}")
    df = load_data(data_path)
    
    # Baseline Environment
    agent_registry, device_agents, sigma_value = setup_environment(df)
    
    # Scenarios to run
    scenarios = [20, 40, 60, 80, 99]
    
    results = []
    
    max_workers = os.cpu_count() or 4
    
    for server_val in scenarios:
        print(f"\n--- SCENARIO: Server Values = {server_val} ---")
        
        # 1. Apply Override
        servers = agent_registry["by_type"].get("Server", [])
        print(f"Updating {len(servers)} servers...")
        for s in servers:
            update_server_strength(s, server_val)
            
        # 2. Run Simulation Batch (Parallel)
        stats = SimulationStats(runs, days)
        
        print(f"Starting {runs} runs on {max_workers} cores...")
        start_t = time.time()
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(runs):
                futures.append(
                    executor.submit(
                        run_iteration, 
                        i, agent_registry, device_agents, sigma_value, days
                    )
                )
            
            for future in as_completed(futures):
                res = future.result()
                idx = res['idx']
                stats.data_loss[idx] = res['data_loss']
                stats.repair_cost[idx] = res['repair']
                stats.hack_Server[idx] = res['hack_server']
                # We can track others if needed, but primary impact should be on servers/data
        
        duration = time.time() - start_t
        print(f"Completed in {duration:.2f}s")
        
        # 3. Store Result Summary
        summary = {
            "Server_Value": server_val,
            "Avg_Data_Loss": stats.data_loss.mean(),
            "Avg_Repair_Cost": stats.repair_cost.mean(),
            "Avg_Server_Hacks": stats.hack_Server.mean(),
            "Total_Data_Loss": stats.data_loss.sum()
        }
        results.append(summary)
        print(f"Result: Avg Data Loss = {summary['Avg_Data_Loss']:,.0f}")

    # 4. Final Report
    print("\n=== SWEEP RESULTS ===")
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    
    # Save to CSV
    res_df.to_csv("outputs/sweep_results.csv", index=False)
    print("\nSaved to outputs/sweep_results.csv")

if __name__ == "__main__":
    import sys
    # Default to data5 if not provided
    dpath = "data/Data5 (typical) - 20 server.csv"
    if len(sys.argv) > 1:
        dpath = sys.argv[1]
        
    run_sweep(dpath)
