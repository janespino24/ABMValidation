import os
import argparse
import glob
from .config import ITERATIONS
from .environment import load_data, setup_environment
from .simulation import SimulationStats, run_iteration

def main():
    parser = argparse.ArgumentParser(description="Run VIVAMACS Notebook Simulation Logic")
    parser.add_argument("--data", default="data/Data2 (Good).csv", help="Path to CSV data")
    parser.add_argument("--runs", type=int, default=ITERATIONS, help="Number of Monte Carlo iterations")
    parser.add_argument("--days", type=int, default=365, help="Days per iteration") # Default 365, but might want smaller for tests
    args = parser.parse_args()

    # 1. Load Data
    path = args.data
    if not os.path.exists(path):
        # Fallback logic from notebook
        csv_files = glob.glob("*.csv")
        if csv_files:
            path = max(csv_files, key=os.path.getmtime)
            print(f"Auto-detected CSV: {path}")
        else:
            print(f"File not found: {path} and no CSV in cwd.")
            return

    print(f"Loading {path}...")
    df = load_data(path)
    
    # 2. Setup Environment (Agents, Links, Strengths)
    print("Setting up agents and network...")
    agent_registry, device_agents, sigma_value = setup_environment(df)
    print(f"Sigma Value initialized to: {sigma_value}")
    
    # 3. Initialize Stats
    print(f"Starting Simulation: {args.runs} runs, {args.days} days each.")
    stats = SimulationStats(args.runs, args.days)
    
    # 4. Run Loop (Parallelized)
    import time
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from functools import partial
    
    start_t = time.time()
    
    # We need to use ProcessPoolExecutor. 
    # Note: 'run_iteration' needs to be picklable.
    
    max_workers = os.cpu_count() or 4
    print(f"Running on {max_workers} cores...")
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # We pass the SAME agent_registry to all.
        # Multiprocessing will pickle it, so each worker gets a copy.
        # This effectively gives each worker an independent environment.
        
        # fix arguments using partial or lambda? No, assume map logic.
        futures = []
        for i in range(args.runs):
            futures.append(
                executor.submit(
                    run_iteration, 
                    i, agent_registry, device_agents, sigma_value, args.days
                )
            )
            
        for future in as_completed(futures):
            res = future.result()
            idx = res['idx']
            # Aggregate
            stats.spam_PC[idx] = res['spam_pc']
            stats.spam_mob[idx] = res['spam_mob']
            stats.hack_FW[idx] = res['hack_fw']
            stats.hack_Server[idx] = res['hack_server']
            stats.hack_Internet[idx] = res['hack_net']
            stats.repair_cost[idx] = res['repair']
            stats.data_loss[idx] = res['data_loss']
            stats.periods[idx] = res['periods']
            
            if (idx + 1) % 10 == 0 or idx == 0:
                 print(f"Completed Run {idx+1}/{args.runs}")

    end_t = time.time()
    print(f"Completed in {end_t - start_t:.2f} seconds.")
    
    # 5. Report Results
    # Print average or total as per notebook
    # Notebook prints stats for the LAST iteration only in the loop, 
    # but accumulates into arrays.
    
    print("\n=== Simulation Results (Average per Run) ===")
    print(f"Avg PC Spam: {stats.spam_PC.mean():.2f}")
    print(f"Avg Mobile Spam: {stats.spam_mob.mean():.2f}")
    print(f"Avg FW Hacks: {stats.hack_FW.mean():.2f}")
    print(f"Avg Server Hacks: {stats.hack_Server.mean():.2f}")
    print(f"Avg Internet Hacks: {stats.hack_Internet.mean():.2f}")
    print(f"Avg Repair Cost: {stats.repair_cost.mean():,.2f}")
    print(f"Avg Data Loss: {stats.data_loss.mean():,.2f}")

if __name__ == "__main__":
    main()
