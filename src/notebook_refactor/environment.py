import pandas as pd
import numpy as np
import math
import random
from .agents import Agent, get_agent_class

def load_data(path, thousands=','):
    return pd.read_csv(path, thousands=thousands)

def create_agent(row):
    agent_type = row['type']
    name = row['name']
    
    # Exclude name/type from attributes dict
    attributes = row.drop(labels=['name', 'type']).dropna().to_dict()

    # Parse VLAN field
    raw_vlan = row.get('VLAN', '')
    parsed_vlans = []
    if isinstance(raw_vlan, str):
        # Handle both comma and semicolon
        vlan_str = raw_vlan.replace(';', ',')
        parsed_vlans = [v.strip() for v in vlan_str.split(',') if v.strip().startswith("VLAN")]
    attributes['VLAN'] = parsed_vlans

    # Network Strength Map
    network_strength_map = {
        1: 94, 2: 98, 3: 90, 4: 96, 5: 100
    }

    try:
        network_level = int(float(str(row.get('Network', 1)))) # Handle '1' or 1.0
    except (TypeError, ValueError):
        network_level = 1

    attributes['net_strength'] = network_strength_map.get(network_level, 10)

    AgentClass = get_agent_class(agent_type)
    agent = AgentClass(name=name, agent_type=agent_type, attributes=attributes)
    return agent

def set_nearby_agents(source_agent, agent_registry_all):
    # Get the VLAN(s) of the target agent
    target_vlans = getattr(source_agent, 'VLAN', [])
    if not isinstance(target_vlans, list):
        target_vlans = [target_vlans]

    for agent in agent_registry_all:
        if agent.name == source_agent.name:
            continue

        agent_vlans = getattr(agent, 'VLAN', [])
        if not isinstance(agent_vlans, list):
            agent_vlans = [agent_vlans]

        # Check for VLAN overlap
        if any(vlan in target_vlans for vlan in agent_vlans):
            setattr(agent, 'nearby', 1)

def setup_environment(df):
    agent_registry = {
        "all": [],
        "by_type": {},
        "by_name": {}
    }
    
    # Create Agents
    for _, row in df.iterrows():
        agent = create_agent(row)
        agent_registry["all"].append(agent)
        agent_registry["by_name"][agent.name] = agent
        
        atype = agent.type
        if atype not in agent_registry["by_type"]:
            agent_registry["by_type"][atype] = []
        agent_registry["by_type"][atype].append(agent)
        
    # Assign Users to Devices (PC/Mobile)
    for device_type in ['PC', 'Mobile']:
        for device_agent in agent_registry["by_type"].get(device_type, []):
            assigned_user = getattr(device_agent, 'User', None) # Note: CSV col is 'User'
            if assigned_user:
                user_agent = agent_registry["by_name"].get(assigned_user)
                if user_agent:
                    if not hasattr(user_agent, 'devices'):
                        setattr(user_agent, 'devices', [])
                    user_agent.devices.append(device_agent.name)
                    
    # Network Agent Logic
    # 1. Map VLAN -> Agents
    vlan_to_agents = {}
    for agent in agent_registry["all"]:
        vlan_list = getattr(agent, 'VLAN', [])
        for vlan in vlan_list:
            vlan_to_agents.setdefault(vlan, []).append(agent.name)
            
    # 2. Assign members to Network agents
    for net_agent in agent_registry["by_type"].get("Network", []):
        vlan_id = net_agent.name
        members = vlan_to_agents.get(vlan_id, [])
        setattr(net_agent, 'members', members)
        
    # 3. Recalculate net_strength for Agents based on Network Agent strength
    # (If Network agents define strength dynamically?)
    # Notebook: "network_agents = {na.name: na ...}"
    # "Set to max strength across VLANs"
    network_agents_map = {na.name: na for na in agent_registry["by_type"].get("Network", [])}
    
    for agent in agent_registry["all"]:
        vlans = getattr(agent, 'VLAN', [])
        strengths = [
            getattr(network_agents_map[vlan], 'net_strength', 100)
            for vlan in vlans 
            if vlan in network_agents_map
        ]
        # If agent is linked to a VLAN, take max strength of that VLAN (if defined in 'Network' rows)
        # Else keep existing (from map in create_agent)
        if strengths:
            setattr(agent, 'net_strength', max(strengths))

    # Calculate Strengths & Vulnerabilities
    device_agents = {
        agent_type: agents
        for agent_type, agents in agent_registry["by_type"].items()
        if agent_type not in ("User", "Network", "Global")
    }

    for agent_type, agents in device_agents.items():
        for agent in agents:
            agent.nearby = 0
            
            # Helper: get numeric val
            patch = getattr(agent, 'patch', 0)
            ports = getattr(agent, 'ports', 0)
            av = getattr(agent, 'AV', 0)
            nst = getattr(agent, 'net_strength', 10)
            filt = getattr(agent, 'Filtering', 0)
            
            if agent.type == "Server":
                # strength = (patch * ports * AV * net_strength) ^ 1/4
                val = patch * ports * av * nst
                strength = round(math.pow(value_clean(val), 0.25))
                setattr(agent, "strength", strength)

            elif agent.type == "Firewall":
                val = patch * filt * nst
                strength = round(math.pow(value_clean(val), 1/3))
                setattr(agent, "strength", strength)

            elif agent.type in ["Mobile", "PC"]:
                val = patch * av * nst
                strength = round(math.pow(value_clean(val), 1/3))
                setattr(agent, "strength", strength)
                
                # Vulnerability
                username = getattr(agent, "User", None)
                user = agent_registry["by_name"].get(username)
                
                vul = 0
                if user:
                    u_aware = getattr(user, "aware", 0)
                    u_access = getattr(user, "access", 0)
                    # (aware * (101 - access)) ^ 1/2
                    vul_val = u_aware * (101 - u_access)
                    vul = round(math.pow(value_clean(vul_val), 0.5))
                
                setattr(agent, "vulnerability", vul)

            else:
                # Internet/Other
                val = filt * nst
                strength = round(math.pow(value_clean(val), 0.5))
                setattr(agent, "strength", strength)

            setattr(agent, "time_infected", 0)

    # Calculate Sigma
    all_agents = agent_registry["all"]
    try:
        target = next(a for a in all_agents if a.name == "Target")
        sigma_val = getattr(target, 'Target_Level', 81) / 3.0
    except StopIteration:
        sigma_val = 10.0 # Default
        
    return agent_registry, device_agents, sigma_val

def value_clean(v):
    return max(0, v)
