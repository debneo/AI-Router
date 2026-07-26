import importlib
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["Solutions"])

class SolutionRequest(BaseModel):
    """Pydantic validates the request body at the door.
    If 'question' is missing, FastAPI returns a clear 422 automatically."""

    question: str = Field(..., description="User's question")
    session_id: str = Field(default="default", description="which conversation this belongs to")

def _make_endpoint(root_fn):
    """Given a root orchestrator function, return a FastAPI endpoint function that runs it.
    Factory: freeze THIS root_fn into a closure, so FastAPI can call it later with just the request body.
    Without """

    def endpoint(req: SolutionRequest):
        return root_fn({"question": req.question, "session_id": req.session_id})
    return endpoint

def register_solution_routes():
    base = Path(__file__).resolve().parent.parent # backend/
    solutions_dir = base / "solutions"
    for solution in solutions_dir.iterdir():
        orch_dir = solution / "orchestrators"
        if not orch_dir.is_dir():
            continue
        for orch_file in orch_dir.iterdir():
            if not orch_dir.is_dir():
                continue
            for orch_file in orch_dir.glob("*.py"):
                if orch_file.stem == "__init__":
                    continue
                module_path = f"solutions.{solution.name}.orchestrators.{orch_file.stem}"
                module = importlib.import_module(module_path)
                if not hasattr(module, "root"): # golden rule enforced
                    continue
                route = f"/{solution.name}/{orch_file.stem}"
                router.add_api_route(route, _make_endpoint(module.root), methods=["POST"])


register_solution_routes()