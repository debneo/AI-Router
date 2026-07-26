from dotenv import load_dotenv

load_dotenv()  # Ensures env vars are loaded whenever this module is imported
from orchestration import parallel,sequential
from solutions.qa.agents.answer_agent import retrieve_agent, answer_agent, followups_agent


# Read as a sentence:
# First retrieve chunks. Then at the same time, write an answer.
# AND suggest followup questions. Each sees what the previous ones wrote into state.
# Every Orchestrator MUST export a variable named `root` ( golden rule ).

root = sequential(
    retrieve_agent,
    parallel(answer_agent, followups_agent)
)