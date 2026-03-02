from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit

from .model_factory import create_model_and_formatter


class MinimalAgent(ReActAgent):
    def __init__(self, name: str = "nanoCoPaw", sys_prompt: str = "You are a helpful assistant."):
        model, formatter = create_model_and_formatter()
        super().__init__(
            name=name,
            model=model,
            sys_prompt=sys_prompt,
            toolkit=Toolkit(),
            memory=InMemoryMemory(),
            formatter=formatter,
            max_iters=8,
        )
