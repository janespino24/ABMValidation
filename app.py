#!/usr/bin/env python3
"""VIVAMACS - Streamlit Control Panel"""
import os
import sys
import json
import time
import math
import subprocess
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from glob import glob

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIRS = {
    "outputs_new": PROJECT_ROOT / "outputs_new",
    "outputs (validation_high)": PROJECT_ROOT / "outputs" / "validation_high",
    "outputs (legacy)": PROJECT_ROOT / "outputs",
}
CONFIGS = {
    "Best": DATA_DIR / "Data_Best.csv",
    "Good": DATA_DIR / "Data2 (Good).csv",
    "Typical": DATA_DIR / "Data_Typical.csv",
    "Worst": DATA_DIR / "Data_Worst.csv",
    "Config A (20-server)": DATA_DIR / "Data_ConfigA_20Server.csv",
    "Config B (5-server SMB)": DATA_DIR / "Data_ConfigB_5Server_SMB.csv",
}
NETWORK_STRENGTH_MAP = {1: 94, 2: 98, 3: 90, 4: 96, 5: 100}
PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
HELPER = str(PROJECT_ROOT / "run_sim_helper.py")

LOGO_PATH = PROJECT_ROOT / "VIVAMACS.png"
st.set_page_config(page_title="VIVAMACS", page_icon=str(LOGO_PATH), layout="wide")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_config_df(path):
    return pd.read_csv(path, thousands=',')


def compute_strength(row):
    """Compute agent strength using the same formulas as environment.py."""
    agent_type = row.get('type', '')
    patch = float(row.get('patch', 0) or 0)
    ports = float(row.get('ports', 0) or 0)
    av = float(row.get('AV', 0) or 0)
    filt = float(row.get('Filtering', 0) or 0)
    try:
        net_level = int(float(row.get('Network', 5) or 5))
    except (TypeError, ValueError):
        net_level = 5
    nst = NETWORK_STRENGTH_MAP.get(net_level, 100)

    val = 0
    if agent_type == 'Server':
        val = max(0, patch * ports * av * nst)
        return round(math.pow(val, 0.25)) if val > 0 else 0
    elif agent_type == 'Firewall':
        val = max(0, patch * filt * nst)
        return round(math.pow(val, 1/3)) if val > 0 else 0
    elif agent_type in ('PC', 'Mobile'):
        val = max(0, patch * av * nst)
        return round(math.pow(val, 1/3)) if val > 0 else 0
    elif agent_type == 'Internet':
        val = max(0, filt * nst)
        return round(math.pow(val, 0.5)) if val > 0 else 0
    return 0


def compute_vulnerability(aware, access):
    """Compute user vulnerability: (aware * (101 - access))^0.5"""
    val = max(0, float(aware or 0) * (101 - float(access or 0)))
    return round(math.pow(val, 0.5)) if val > 0 else 0


def find_csvs(directory):
    """Find all CSV files in directory (non-temp)."""
    if not directory.exists():
        return []
    return sorted([p for p in directory.glob("*.csv") if not p.name.startswith("temp_") and not p.name.startswith("config_")])


def find_pngs(directory):
    """Find all PNG files in directory."""
    if not directory.exists():
        return []
    return sorted(directory.glob("*.png"))


# ---------------------------------------------------------------------------
# PAGE: Dashboard
# ---------------------------------------------------------------------------
def page_dashboard():
    st.title("VIVAMACS Control Panel")
    st.markdown("Agent-Based Cyber Risk Modeling Simulation")
    st.divider()

    # Available configs
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Available Configurations")
        for name, path in CONFIGS.items():
            exists = "available" if path.exists() else "missing"
            st.markdown(f"- **{name}**: `{path.name}` ({exists})")

    with col2:
        st.subheader("Output Directories")
        for name, path in OUTPUTS_DIRS.items():
            if path.exists():
                csvs = list(path.rglob("*.csv"))
                pngs = list(path.rglob("*.png"))
                st.markdown(f"- **{name}**: {len(csvs)} CSVs, {len(pngs)} PNGs")
            else:
                st.markdown(f"- **{name}**: not yet created")

    # Show latest results if available
    st.divider()
    st.subheader("Latest Results Preview")

    for out_name, out_path in OUTPUTS_DIRS.items():
        table1 = out_path / "main" / "table1_scenario_comparison.csv"
        if table1.exists():
            st.markdown(f"**From {out_name}:**")
            df = pd.read_csv(table1)
            st.dataframe(df, use_container_width=True)
            break
    else:
        st.info("No results found yet. Run a simulation or wait for the background rerun to complete.")

    # Check if rerun is in progress
    log_file = PROJECT_ROOT / "rerun_log_v2.txt"
    if log_file.exists():
        st.divider()
        st.subheader("Background Rerun Status")
        try:
            lines = log_file.read_text().strip().split('\n')
            last_lines = lines[-5:] if len(lines) >= 5 else lines
            st.code('\n'.join(last_lines), language='text')
        except Exception:
            pass


# ---------------------------------------------------------------------------
# PAGE: Configuration Editor
# ---------------------------------------------------------------------------
def page_config_editor():
    st.title("Configuration Editor")

    # Select base config
    config_name = st.selectbox("Base Configuration", list(CONFIGS.keys()))
    config_path = CONFIGS[config_name]

    if not config_path.exists():
        st.error(f"Config file not found: {config_path}")
        return

    df = load_config_df(str(config_path))

    # Bulk parameter overrides
    st.subheader("Bulk Parameter Overrides")
    st.caption("Adjust sliders to override parameters for all agents of that type. Leave at 0 to keep original values.")

    modifications = {}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Users**")
        user_aware = st.slider("User Awareness", 0, 100, 0, key="user_aware", help="0 = keep original")
        user_access = st.slider("User Access Level", 0, 100, 0, key="user_access", help="0 = keep original")

        st.markdown("**Servers**")
        srv_patch = st.slider("Server Patch", 0, 100, 0, key="srv_patch")
        srv_av = st.slider("Server AV", 0, 100, 0, key="srv_av")
        srv_ports = st.slider("Server Ports", 0, 100, 0, key="srv_ports")

    with col2:
        st.markdown("**PCs & Mobiles**")
        pc_patch = st.slider("PC Patch", 0, 100, 0, key="pc_patch")
        pc_av = st.slider("PC AV", 0, 100, 0, key="pc_av")
        mob_patch = st.slider("Mobile Patch", 0, 100, 0, key="mob_patch")
        mob_av = st.slider("Mobile AV", 0, 100, 0, key="mob_av")

        st.markdown("**Network & Global**")
        fw_patch = st.slider("Firewall Patch", 0, 100, 0, key="fw_patch")
        fw_filt = st.slider("Firewall Filtering", 0, 100, 0, key="fw_filt")
        isp_filt = st.slider("ISP Filtering", 0, 100, 0, key="isp_filt")
        target = st.slider("Target Level (Attack Intensity)", 0, 100, 0, key="target_level", help="0 = keep original")

    # Build modifications dict
    if user_aware > 0:
        modifications.setdefault('aware', {})['User'] = user_aware
    if user_access > 0:
        modifications.setdefault('access', {})['User'] = user_access
    if srv_patch > 0:
        modifications.setdefault('patch', {})['Server'] = srv_patch
    if srv_av > 0:
        modifications.setdefault('AV', {})['Server'] = srv_av
    if srv_ports > 0:
        modifications.setdefault('ports', {})['Server'] = srv_ports
    if pc_patch > 0:
        modifications.setdefault('patch', {})['PC'] = pc_patch
    if pc_av > 0:
        modifications.setdefault('AV', {})['PC'] = pc_av
    if mob_patch > 0:
        modifications.setdefault('patch', {})['Mobile'] = mob_patch
    if mob_av > 0:
        modifications.setdefault('AV', {})['Mobile'] = mob_av
    if fw_patch > 0:
        modifications.setdefault('patch', {})['Firewall'] = fw_patch
    if fw_filt > 0:
        modifications.setdefault('Filtering', {})['Firewall'] = fw_filt
    if isp_filt > 0:
        modifications.setdefault('Filtering', {})['Internet'] = isp_filt
    if target > 0:
        modifications.setdefault('Target_Level', {})['Global'] = target

    # Apply modifications to preview
    df_mod = df.copy()
    for col, val_map in modifications.items():
        for agent_type, value in val_map.items():
            mask = df_mod['type'] == agent_type
            if mask.any():
                df_mod.loc[mask, col] = value

    # Show the config with computed strengths
    st.divider()
    st.subheader("Agent Configuration Preview")

    # Add strength column for preview
    device_types = ['Server', 'Firewall', 'PC', 'Mobile', 'Internet']
    preview_rows = []
    for _, row in df_mod.iterrows():
        r = {'Name': row['name'], 'Type': row['type']}
        if row['type'] in device_types:
            r['Patch'] = row.get('patch', '')
            r['AV'] = row.get('AV', '')
            r['Ports'] = row.get('ports', '')
            r['Filtering'] = row.get('Filtering', '')
            r['Strength'] = compute_strength(row)
            r['Data Value'] = row.get('Data_Value', '')
            r['Repair Value'] = row.get('Repair_Value', '')
        elif row['type'] == 'User':
            r['Awareness'] = row.get('aware', '')
            r['Access'] = row.get('access', '')
            r['Vulnerability'] = compute_vulnerability(row.get('aware', 0), row.get('access', 0))
        elif row['type'] == 'Global':
            r['Target Level'] = row.get('Target_Level', '')
            r['Sigma'] = round(float(row.get('Target_Level', 50) or 50) / 3, 1)
        preview_rows.append(r)

    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)

    # Save button
    st.divider()
    save_name = st.text_input("Save as", value="custom_config.csv")
    if st.button("Save Configuration", type="primary"):
        save_path = DATA_DIR / save_name
        df_mod.to_csv(save_path, index=False)
        st.success(f"Saved to `{save_path}`")


# ---------------------------------------------------------------------------
# PAGE: Run Simulation
# ---------------------------------------------------------------------------
def page_run_simulation():
    st.title("Run Simulation")

    # Config selection
    all_csvs = list(DATA_DIR.glob("*.csv"))
    config_options = {p.stem: str(p) for p in sorted(all_csvs)}
    selected = st.selectbox("Configuration", list(config_options.keys()))
    config_path = config_options[selected]

    col1, col2 = st.columns(2)
    with col1:
        runs = st.slider("Monte Carlo Runs", 10, 2000, 200, step=10)
    with col2:
        days = st.slider("Simulation Days", 30, 730, 365, step=30)

    st.caption(f"Estimated time: ~{runs * days / 365 * 0.05:.0f} seconds on 32 cores (very rough)")

    # Run button
    if st.button("Run Simulation", type="primary"):
        run_id = f"run_{int(time.time())}"
        output_dir = str(PROJECT_ROOT / "outputs_gui" / run_id)
        progress_file = str(PROJECT_ROOT / "outputs_gui" / run_id / "progress.json")
        os.makedirs(output_dir, exist_ok=True)

        # Launch subprocess
        cmd = [PYTHON, HELPER,
               "--config", config_path,
               "--runs", str(runs),
               "--days", str(days),
               "--output", output_dir,
               "--progress", progress_file]

        proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        st.session_state['sim_proc'] = proc
        st.session_state['sim_progress_file'] = progress_file
        st.session_state['sim_output_dir'] = output_dir
        st.session_state['sim_run_id'] = run_id

    # Show progress if running
    if 'sim_progress_file' in st.session_state:
        progress_file = st.session_state['sim_progress_file']
        output_dir = st.session_state['sim_output_dir']

        progress_bar = st.progress(0)
        status_text = st.empty()
        results_area = st.container()

        # Poll progress
        while True:
            time.sleep(1)
            if not os.path.exists(progress_file):
                status_text.text("Starting simulation...")
                continue

            try:
                with open(progress_file) as f:
                    prog = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                continue

            status = prog.get("status", "unknown")
            completed = prog.get("completed", 0)
            total = prog.get("total", 1)
            eta = prog.get("eta_min", 0)

            if status == "loading":
                status_text.text("Loading configuration...")
            elif status == "running":
                pct = completed / total if total > 0 else 0
                progress_bar.progress(pct)
                status_text.text(f"Running: {completed}/{total} ({pct*100:.0f}%) - ETA: {eta:.1f} min")
            elif status == "done":
                progress_bar.progress(1.0)
                status_text.text("Simulation complete!")

                # Load and display results
                results_path = prog.get("results")
                if results_path and os.path.exists(results_path):
                    with open(results_path) as f:
                        results = json.load(f)
                    _show_sim_results(results_area, results)

                # Cleanup session state
                for key in ['sim_proc', 'sim_progress_file', 'sim_output_dir', 'sim_run_id']:
                    st.session_state.pop(key, None)
                break
            elif status == "error":
                status_text.error(f"Error: {prog.get('error', 'Unknown')}")
                for key in ['sim_proc', 'sim_progress_file', 'sim_output_dir', 'sim_run_id']:
                    st.session_state.pop(key, None)
                break

    # Show past GUI runs
    gui_outputs = PROJECT_ROOT / "outputs_gui"
    if gui_outputs.exists():
        past_runs = sorted(gui_outputs.iterdir(), reverse=True)
        past_runs = [p for p in past_runs if (p / "results.json").exists()]
        if past_runs:
            st.divider()
            st.subheader("Past Runs")
            for run_dir in past_runs[:10]:
                with st.expander(run_dir.name):
                    try:
                        with open(run_dir / "results.json") as f:
                            results = json.load(f)
                        _show_sim_results(st, results, compact=True)
                    except Exception as e:
                        st.error(str(e))


def _show_sim_results(container, results, compact=False):
    """Display simulation results."""
    mean = results['mean_cost']
    std = results['std_cost']

    col1, col2, col3, col4 = container.columns(4)
    col1.metric("Mean Breach Cost", f"${mean/1e6:,.1f}M")
    col2.metric("Std Dev", f"${std/1e6:,.1f}M")
    col3.metric("95th Percentile", f"${results['p95']/1e6:,.1f}M")
    col4.metric("CV", f"{results['cv']:.3f}")

    if not compact:
        col1, col2, col3, col4, col5 = container.columns(5)
        col1.metric("Server Hacks", f"{results['mean_hack_server']:,.0f}")
        col2.metric("FW Hacks", f"{results['mean_hack_fw']:,.0f}")
        col3.metric("Internet Hacks", f"{results['mean_hack_internet']:,.0f}")
        col4.metric("PC Spam", f"{results['mean_spam_pc']:,.0f}")
        col5.metric("Mobile Spam", f"{results['mean_spam_mob']:,.0f}")

    # Histogram
    if 'total_breach_costs' in results:
        costs = np.array(results['total_breach_costs']) / 1e6
        fig = px.histogram(x=costs, nbins=50, labels={'x': 'Total Breach Cost ($M)'},
                          title=f"Breach Cost Distribution ({results['runs']} runs, {results['days']} days)")
        fig.update_layout(showlegend=False, height=350)
        container.plotly_chart(fig, use_container_width=True)

    container.caption(f"Config: {results['config']} | Duration: {results['duration_sec']:.0f}s | Runs: {results['runs']} | Days: {results['days']}")


# ---------------------------------------------------------------------------
# PAGE: Results Explorer
# ---------------------------------------------------------------------------
def page_results_explorer():
    st.title("Results Explorer")

    # Select output directory
    available = {}
    for name, path in OUTPUTS_DIRS.items():
        if path.exists():
            available[name] = path
    # Also check for GUI outputs
    gui_dir = PROJECT_ROOT / "outputs_gui"
    if gui_dir.exists():
        for d in sorted(gui_dir.iterdir(), reverse=True):
            if d.is_dir() and (d / "results.json").exists():
                available[f"GUI: {d.name}"] = d

    if not available:
        st.info("No output directories found.")
        return

    selected_name = st.selectbox("Output Directory", list(available.keys()))
    base_dir = available[selected_name]

    # Check subdirectories
    main_dir = base_dir / "main" if (base_dir / "main").exists() else base_dir
    adv_dir = base_dir / "advanced" if (base_dir / "advanced").exists() else None
    sobol_dir = base_dir / "sobol" if (base_dir / "sobol").exists() else None

    tabs = ["Scenario Comparison", "Control Effectiveness", "Sensitivity Curve"]
    if adv_dir:
        tabs += ["Temporal Stability", "Seed Robustness", "Extreme Parameters", "Convergence", "Interactions"]
    if sobol_dir:
        tabs += ["Sobol Analysis"]

    tab_objs = st.tabs(tabs)
    tab_idx = 0

    # --- Tab: Scenario Comparison ---
    with tab_objs[tab_idx]:
        tab_idx += 1
        csv_path = main_dir / "table1_scenario_comparison.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            st.dataframe(df, use_container_width=True)

            # Bar chart
            if 'Mean Breach Cost' in df.columns:
                costs = df['Mean Breach Cost'].str.replace(r'[\$M,]', '', regex=True).astype(float)
                fig = px.bar(x=df['Configuration'], y=costs, labels={'x': 'Configuration', 'y': 'Mean Breach Cost ($M)'},
                            title="Scenario Comparison", color=df['Configuration'],
                            color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

            # Statistical tests
            stat_path = main_dir / "table1_statistical_tests.txt"
            if stat_path.exists():
                st.text(stat_path.read_text())

            st.download_button("Download CSV", csv_path.read_bytes(), csv_path.name, "text/csv")
        else:
            st.info("table1_scenario_comparison.csv not found")

        # Distribution plot
        dist_png = main_dir / "figure2_distributions.png"
        if dist_png.exists():
            st.image(str(dist_png), caption="Breach Cost Distributions")

    # --- Tab: Control Effectiveness ---
    with tab_objs[tab_idx]:
        tab_idx += 1
        csv_path = main_dir / "table2_control_effectiveness.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            st.dataframe(df, use_container_width=True)

            if 'Mean Breach Cost' in df.columns and len(df) > 1:
                costs = df['Mean Breach Cost'].str.replace(r'[\$M,]', '', regex=True).astype(float)
                fig = px.bar(x=df['Control Modified'], y=costs,
                            labels={'x': 'Control', 'y': 'Mean Breach Cost ($M)'},
                            title="Control Effectiveness", color_discrete_sequence=['steelblue'])
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            st.download_button("Download CSV", csv_path.read_bytes(), csv_path.name, "text/csv")
        else:
            st.info("table2_control_effectiveness.csv not found")

    # --- Tab: Sensitivity Curve ---
    with tab_objs[tab_idx]:
        tab_idx += 1
        csv_path = main_dir / "figure1_data.csv"
        png_path = main_dir / "figure1_sensitivity_curve.png"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            st.dataframe(df, use_container_width=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['level'], y=df['mean'] / 1e6, mode='lines+markers',
                                     name='Mean Cost', line=dict(width=2)))
            fig.add_trace(go.Scatter(x=df['level'], y=(df['mean'] + df['std']) / 1e6,
                                     mode='lines', line=dict(width=0), showlegend=False))
            fig.add_trace(go.Scatter(x=df['level'], y=(df['mean'] - df['std']) / 1e6,
                                     mode='lines', line=dict(width=0), fill='tonexty',
                                     fillcolor='rgba(0,100,255,0.15)', name='Std Dev'))
            fig.update_layout(title='Server Patching Sensitivity Curve',
                            xaxis_title='Server Patch/AV Level', yaxis_title='Mean Breach Cost ($M)',
                            height=450)
            st.plotly_chart(fig, use_container_width=True)

            # Marginal reduction
            if 'marginal_reduction' in df.columns:
                fig2 = px.bar(df[df['marginal_reduction'].notna()], x='level', y='marginal_reduction',
                             title='Marginal Risk Reduction per Increment',
                             labels={'level': 'Patch Level', 'marginal_reduction': 'Marginal Reduction (%)'})
                fig2.update_layout(height=350)
                st.plotly_chart(fig2, use_container_width=True)

            st.download_button("Download CSV", csv_path.read_bytes(), csv_path.name, "text/csv")
        elif png_path.exists():
            st.image(str(png_path))
        else:
            st.info("Sensitivity data not found")

    # --- Advanced Validation Tabs ---
    if adv_dir:
        # Temporal Stability
        with tab_objs[tab_idx]:
            tab_idx += 1
            _show_adv_csv(adv_dir / "exp1_temporal_stability.csv", adv_dir / "exp1_temporal_stability.png",
                         "Temporal Stability")

        # Seed Robustness
        with tab_objs[tab_idx]:
            tab_idx += 1
            _show_adv_csv(adv_dir / "exp2_seed_robustness.csv", adv_dir / "exp2_seed_robustness.png",
                         "Seed Robustness")
            ks_path = adv_dir / "exp2_ks_tests.csv"
            if ks_path.exists():
                st.markdown("**Kolmogorov-Smirnov Tests:**")
                st.dataframe(pd.read_csv(ks_path), use_container_width=True)

        # Extreme Parameters
        with tab_objs[tab_idx]:
            tab_idx += 1
            _show_adv_csv(adv_dir / "exp3_extreme_parameters.csv", adv_dir / "exp3_extreme_parameters.png",
                         "Extreme Parameter Testing")

        # Convergence
        with tab_objs[tab_idx]:
            tab_idx += 1
            csv_path = adv_dir / "exp4_convergence.csv"
            png_path = adv_dir / "exp4_convergence.png"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                st.dataframe(df, use_container_width=True)
                if 'CI_Width_Pct' in df.columns or 'CI % of Mean' in df.columns:
                    ci_col = 'CI_Width_Pct' if 'CI_Width_Pct' in df.columns else 'CI % of Mean'
                    n_col = 'Sample_Size' if 'Sample_Size' in df.columns else 'N Runs'
                    if ci_col in df.columns and n_col in df.columns:
                        ci_vals = df[ci_col].astype(str).str.replace('%', '').astype(float)
                        fig = px.line(x=df[n_col], y=ci_vals, markers=True,
                                     labels={'x': 'Sample Size', 'y': 'CI Width (% of Mean)'},
                                     title='Monte Carlo Convergence')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
            if png_path.exists():
                st.image(str(png_path))

        # Interactions
        with tab_objs[tab_idx]:
            tab_idx += 1
            _show_adv_csv(adv_dir / "exp5_interactions.csv", adv_dir / "exp5_interactions.png",
                         "Parameter Interactions")

    # --- Sobol Analysis ---
    if sobol_dir:
        with tab_objs[tab_idx]:
            tab_idx += 1
            csv_path = sobol_dir / "sobol_indices.csv"
            png_path = sobol_dir / "sobol_results.png"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                st.dataframe(df, use_container_width=True)

                # Plot S1 and ST
                s1_col = [c for c in df.columns if 'S1' in c and 'conf' not in c.lower()]
                st_col = [c for c in df.columns if 'ST' in c and 'conf' not in c.lower()]
                param_col = df.columns[0]

                if s1_col and st_col:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(name='First Order (S1)', x=df[param_col], y=df[s1_col[0]]))
                    fig.add_trace(go.Bar(name='Total Order (ST)', x=df[param_col], y=df[st_col[0]]))
                    fig.update_layout(barmode='group', title='Sobol Sensitivity Indices',
                                     xaxis_title='Parameter', yaxis_title='Index Value', height=450)
                    st.plotly_chart(fig, use_container_width=True)

                st.download_button("Download CSV", csv_path.read_bytes(), csv_path.name, "text/csv")
            if png_path.exists():
                st.image(str(png_path), caption="Sobol Analysis")


def _show_adv_csv(csv_path, png_path, title):
    """Helper to show an advanced validation CSV + PNG."""
    st.subheader(title)
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        st.dataframe(df, use_container_width=True)
        st.download_button(f"Download {csv_path.name}", csv_path.read_bytes(), csv_path.name, "text/csv",
                          key=f"dl_{csv_path.stem}")
    if png_path.exists():
        st.image(str(png_path))
    if not csv_path.exists() and not png_path.exists():
        st.info(f"No data found for {title}")


# ---------------------------------------------------------------------------
# PAGE: Quick Compare
# ---------------------------------------------------------------------------
def page_quick_compare():
    st.title("Quick Compare")
    st.markdown("Compare multiple configurations with a quick simulation run.")

    # Select configs
    config_options = list(CONFIGS.keys())
    # Add custom configs
    for p in DATA_DIR.glob("custom*.csv"):
        config_options.append(p.stem)

    selected_configs = st.multiselect("Select 2-4 configurations to compare", config_options,
                                       default=["Best", "Typical", "Worst"] if len(config_options) >= 3 else config_options[:2])

    if len(selected_configs) < 2:
        st.warning("Select at least 2 configurations.")
        return

    col1, col2 = st.columns(2)
    with col1:
        runs = st.slider("Runs per config", 10, 500, 100, step=10, key="cmp_runs")
    with col2:
        days = st.slider("Days", 30, 365, 365, step=30, key="cmp_days")

    if st.button("Run Comparison", type="primary"):
        results_list = []
        progress = st.progress(0)
        status = st.empty()

        for i, name in enumerate(selected_configs):
            status.text(f"Running {name}... ({i+1}/{len(selected_configs)})")
            progress.progress(i / len(selected_configs))

            # Resolve config path
            if name in CONFIGS:
                path = str(CONFIGS[name])
            else:
                path = str(DATA_DIR / f"{name}.csv")

            # Run via subprocess (blocking for quick compare)
            run_id = f"compare_{name}_{int(time.time())}"
            output_dir = str(PROJECT_ROOT / "outputs_gui" / run_id)
            progress_file = str(Path(output_dir) / "progress.json")
            os.makedirs(output_dir, exist_ok=True)

            cmd = [PYTHON, HELPER,
                   "--config", path,
                   "--runs", str(runs),
                   "--days", str(days),
                   "--output", output_dir,
                   "--progress", progress_file]

            proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)

            if proc.returncode == 0:
                results_path = Path(output_dir) / "results.json"
                if results_path.exists():
                    with open(results_path) as f:
                        r = json.load(f)
                    r['name'] = name
                    results_list.append(r)
            else:
                st.error(f"Error running {name}: {proc.stderr[:200]}")

        progress.progress(1.0)
        status.text("Comparison complete!")

        if len(results_list) >= 2:
            st.session_state['compare_results'] = results_list

    # Display comparison results
    if 'compare_results' in st.session_state:
        results_list = st.session_state['compare_results']
        st.divider()

        # Summary table
        rows = []
        for r in results_list:
            rows.append({
                'Configuration': r['name'],
                'Mean Cost ($M)': round(r['mean_cost'] / 1e6, 1),
                'Std Dev ($M)': round(r['std_cost'] / 1e6, 1),
                '95th Pct ($M)': round(r['p95'] / 1e6, 1),
                'CV': round(r['cv'], 3),
                'Server Hacks': round(r['mean_hack_server']),
                'Duration (s)': round(r['duration_sec']),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        # Bar chart comparison
        df_cmp = pd.DataFrame(rows)
        fig = px.bar(df_cmp, x='Configuration', y='Mean Cost ($M)',
                    title='Mean Breach Cost Comparison',
                    color='Configuration', color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

        # Overlay histograms
        fig2 = go.Figure()
        for r in results_list:
            if 'total_breach_costs' in r:
                costs = np.array(r['total_breach_costs']) / 1e6
                fig2.add_trace(go.Histogram(x=costs, name=r['name'], opacity=0.6, nbinsx=40))
        fig2.update_layout(barmode='overlay', title='Breach Cost Distributions',
                          xaxis_title='Total Breach Cost ($M)', yaxis_title='Count',
                          height=400)
        st.plotly_chart(fig2, use_container_width=True)

        # Relative comparison
        worst_cost = max(r['mean_cost'] for r in results_list)
        if worst_cost > 0:
            pct_rows = []
            for r in results_list:
                pct_rows.append({
                    'Configuration': r['name'],
                    '% of Worst': round(r['mean_cost'] / worst_cost * 100, 1),
                })
            fig3 = px.bar(pd.DataFrame(pct_rows), x='Configuration', y='% of Worst',
                         title='Relative Risk (% of Worst Configuration)',
                         color='Configuration', color_discrete_sequence=px.colors.qualitative.Set2)
            fig3.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig3, use_container_width=True)


# ---------------------------------------------------------------------------
# MAIN - Sidebar Navigation
# ---------------------------------------------------------------------------
def main():
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=200)
        st.caption("Vendor-Independent Vulnerability Assessment Model with Actionable Insights")
        page = st.radio("Navigate", [
            "Dashboard",
            "Configuration Editor",
            "Run Simulation",
            "Results Explorer",
            "Quick Compare",
        ])

    if page == "Dashboard":
        page_dashboard()
    elif page == "Configuration Editor":
        page_config_editor()
    elif page == "Run Simulation":
        page_run_simulation()
    elif page == "Results Explorer":
        page_results_explorer()
    elif page == "Quick Compare":
        page_quick_compare()


if __name__ == "__main__":
    main()
