from src.reasoning.llm_runtime import LLMRuntime
from pathlib import Path
import yaml

def test_stub_is_default_and_adapter_flags():
    rt = LLMRuntime()
    assert rt.use_stub is True
    assert rt.adapter_available("k999") is False
