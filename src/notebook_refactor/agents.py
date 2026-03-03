import random
import math
from datetime import datetime

class Agent:
    def __init__(self, name, agent_type, attributes):
        self.name = name
        self.type = agent_type
        # Set all attributes dynamically
        for key, value in attributes.items():
            setattr(self, key, value)
            
        # Initialize simulation state attributes if not present
        if not hasattr(self, 'Status'): self.Status = 0
        if not hasattr(self, 'time_infected'): self.time_infected = 0
        if not hasattr(self, 'nearby'): self.nearby = 0
        
        # Ensure strength/vuln exist with defaults (will be recalculated)
        if not hasattr(self, 'strength'): self.strength = 10
        if not hasattr(self, 'vulnerability'): self.vulnerability = 0
        
        # Data/Repair values need default 0 if missing
        if not hasattr(self, 'Data_Value'): self.Data_Value = 0.0
        if not hasattr(self, 'Repair_Value'): self.Repair_Value = 0.0
        if not hasattr(self, 'AV'): self.AV = 0
        if not hasattr(self, 'patch'): self.patch = 0
        if not hasattr(self, 'ports'): self.ports = 0
        if not hasattr(self, 'Filtering'): self.Filtering = 0

    def __repr__(self):
        return f"{self.type}Agent(name={self.name})"

    def is_active(self, current_time):
        try:
            # Handle HH:MM string, HHMM int, or time object
            s_val = self.hours_start
            e_val = self.hours_end
            
            # Helper to convert to time
            def to_time(val):
                if isinstance(val, int): # e.g. 900 -> 09:00
                    h, m = divmod(val, 100)
                    return datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M").time()
                elif isinstance(val, str):
                    if ':' in val:
                        return datetime.strptime(val, "%H:%M").time()
                    else:
                        return datetime.strptime(val, "%H:%M:%S").time() # Fallback
                return None

            start = to_time(s_val)
            end = to_time(e_val)
            
            if start and end:
                if start <= end:
                    return start <= current_time <= end
                else:  # overnight shifts
                    return current_time >= start or current_time <= end
                    
            return True # Default active
        except Exception:
            return True  # Default: always active if no time info

# Define explicit classes so pickle can find them
class UserAgent(Agent): pass
class PCAgent(Agent): pass
class MobileAgent(Agent): pass
class ServerAgent(Agent): pass
class FirewallAgent(Agent): pass
class InternetAgent(Agent): pass
class NetworkAgent(Agent): pass
class VLANAgent(Agent): pass
class GlobalAgent(Agent): pass
class RouterAgent(Agent): pass

# Function to map string to class
def get_agent_class(agent_type):
    # Map known types
    mapping = {
        'User': UserAgent,
        'PC': PCAgent,
        'Mobile': MobileAgent,
        'Server': ServerAgent,
        'Firewall': FirewallAgent,
        'Internet': InternetAgent,
        'Network': NetworkAgent,
        'VLAN': VLANAgent,
        'Global': GlobalAgent,
        'Router': RouterAgent
    }
    return mapping.get(agent_type, Agent)

