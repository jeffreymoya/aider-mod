from typing import List
from pydantic import BaseModel
from adrm.core.models import Step

class Workflow(BaseModel):
    name: str
    description: str
    steps: List[Step]
    
    def validate_steps(self) -> bool:
        # Validate step dependencies and requirements
        return all(step.files for step in self.steps)

class WorkflowRunner:
    def __init__(self, step_runner: StepRunner):
        self.step_runner = step_runner
    
    async def execute_workflow(self, workflow: Workflow) -> None:
        if not workflow.validate_steps():
            raise ValueError("Invalid workflow configuration")
            
        for step in workflow.steps:
            await self.step_runner.run_step(step) 