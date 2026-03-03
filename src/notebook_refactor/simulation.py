import random
import numpy as np
from datetime import time
from .config import *
from .environment import set_nearby_agents

def random_gen(sigma_value, low=1, high=100, mu=50):
    while True:
        x = random.gauss(mu, sigma_value)
        if low <= x <= high:
            return int(round(x))

class SimulationStats:
    def __init__(self, iterations, days):
        self.spam_mob = np.zeros(iterations)
        self.spam_PC = np.zeros(iterations)
        self.hack_FW = np.zeros(iterations)
        self.hack_Server = np.zeros(iterations)
        self.hack_Internet = np.zeros(iterations)
        self.data_loss = np.zeros(iterations)
        self.repair_cost = np.zeros(iterations)
        self.periods = np.zeros(iterations)

def run_iteration(iteration_idx, agent_registry, device_agents, sigma_value, days=DAYS):
    
    # 1. DEEP COPY / RESET for independent run
    # Since we are in a process (potentially), the memory is separate. 
    # But we explicitly reset logic to ensure clean state.
    for agent in agent_registry["all"]:
        agent.Status = 0
        agent.time_infected = 0
        agent.nearby = 0

    # Local accumulators 
    total_data_val = 0
    total_repair_val = 0
    
    count_spam_mob = 0
    count_spam_pc = 0
    count_hack_fw = 0
    count_hack_server = 0
    count_hack_net = 0
    
    total_periods = 0

    for day in range(days):
        for hour in range(START_HOUR, END_HOUR, 1):
            for minute in range(0, 60, PERIOD_IN_MINS):
                
                total_periods += 1
                current_time = time(hour, minute)

                for agent_type, agents in device_agents.items():
                    for agent in agents:
                        if agent.is_active(current_time):
                            
                            attack = random_gen(sigma_value)
                            
                            # Random chance to clear nearby threat
                            if agent.nearby == 1 and random_gen(sigma_value) <= agent.strength:
                                agent.nearby = 0

                            # LOGIC BRANCHES
                            if agent.type == "Server":
                                if agent.Status == 0:
                                    if attack > agent.strength or agent.nearby == 1:
                                        agent.Status = 1
                                        agent.time_infected = 0
                                        count_hack_server += 1
                                        total_data_val += (agent.Data_Value * PERIOD_IN_MINS / TIME_TO_EXFIL)
                                        set_nearby_agents(agent, agent_registry["all"])
                                
                                elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.AV:
                                    agent.Status = 0
                                    agent.time_infected = 0
                                    total_repair_val += agent.Repair_Value
                                else:
                                    agent.time_infected += PERIOD_IN_MINS
                                    total_data_val += (agent.Data_Value * PERIOD_IN_MINS / TIME_TO_EXFIL)

                            elif agent.type == "Firewall":
                                if agent.Status == 0:
                                    if attack > agent.strength or agent.nearby == 1:
                                        agent.Status = 1
                                        agent.time_infected = 0
                                        count_hack_fw += 1
                                        set_nearby_agents(agent, agent_registry["all"])
                                elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.strength:
                                    agent.Status = 0
                                    agent.time_infected = 0
                                    total_repair_val += agent.Repair_Value
                                else:
                                    agent.time_infected += PERIOD_IN_MINS

                            elif agent.type == "Mobile":
                                if agent.Status == 0:
                                    user_act = random_gen(sigma_value)
                                    if attack > agent.strength and (user_act > agent.vulnerability or agent.nearby == 1):
                                        agent.Status = 1
                                        agent.time_infected = 0
                                        count_spam_mob += 1
                                        total_data_val += (agent.Data_Value * PERIOD_IN_MINS / TIME_TO_EXFIL)
                                        set_nearby_agents(agent, agent_registry["all"])
                                elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.AV:
                                    agent.Status = 0
                                    agent.time_infected = 0
                                    total_repair_val += agent.Repair_Value
                                else:
                                    agent.time_infected += PERIOD_IN_MINS
                                    total_data_val += (agent.Data_Value * PERIOD_IN_MINS / TIME_TO_EXFIL)

                            elif agent.type == "PC":
                                if agent.Status == 0:
                                    user_act = random_gen(sigma_value)
                                    if attack > agent.strength and (user_act > agent.vulnerability or agent.nearby == 1):
                                        agent.Status = 1
                                        agent.time_infected = 0
                                        count_spam_pc += 1
                                        total_data_val += (agent.Data_Value * PERIOD_IN_MINS / TIME_TO_EXFIL)
                                        set_nearby_agents(agent, agent_registry["all"])
                                elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.AV:
                                    agent.Status = 0
                                    agent.time_infected = 0
                                    total_repair_val += agent.Repair_Value
                                else:
                                    agent.time_infected += PERIOD_IN_MINS
                                    total_data_val += (agent.Data_Value * PERIOD_IN_MINS / TIME_TO_EXFIL)
                                    
                            else: # Internet/Other
                                if agent.Status == 0:
                                    if attack > agent.strength:
                                        agent.Status = 1
                                        agent.time_infected = 0
                                        count_hack_net += 1
                                        set_nearby_agents(agent, agent_registry["all"])
                                elif agent.time_infected > VIRUS_CLEANED and random_gen(sigma_value) < agent.strength:
                                    agent.Status = 0
                                    agent.time_infected = 0
                                else:
                                    agent.time_infected += PERIOD_IN_MINS

    # Return Result Dict
    return {
        'idx': iteration_idx,
        'spam_mob': count_spam_mob,
        'spam_pc': count_spam_pc,
        'hack_fw': count_hack_fw,
        'hack_server': count_hack_server,
        'hack_net': count_hack_net,
        'repair': total_repair_val,
        'data_loss': total_data_val,
        'periods': total_periods
    }

