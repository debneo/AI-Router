from typing import Callable

# An "agent" here is just a function : (state:dict) -> dict
# It reads what it needs from the state and returns new keys to merge in

Agent = Callable[[dict], dict]

def sequential(*agents: Agent) -> Agent:
    """Run a sequence of agents, merging their outputs into the state. Each sees what the previous ones wrote into state."""

    def run(state: dict) -> dict:
        for agent in agents:
            new_state = agent(state)
            state.update(new_state)
        return state
    return run

def parallel(*agents: Agent) -> Agent:
    """Run a sequence of agents in parallel, merging their outputs into the state. Each sees only the original state."""

    def run(state: dict) -> dict:
        merged = dict(state)  # Start with a copy of the original state
        for agent in agents:
            new_state = agent(state)
            merged.update(new_state)
        return merged
    return run