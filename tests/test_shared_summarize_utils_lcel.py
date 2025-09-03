
from utils.common.shared_summarize_utils import create_chain_lcel


class DummyLLM:
    """Minimal chat model that echoes the prompt string for tests."""
    def invoke(self, prompt: str):
        # return a simple deterministic message for assertions
        return f"ECHO: {prompt[:30]}"


def test_create_chain_lcel_with_none_llm_echo():
    chain = create_chain_lcel(llm=None)
    out = chain.invoke({"context": "hello world"})
    assert out.startswith("### Summary of Part X")
    assert "hello world" in out


def test_create_chain_lcel_runs_with_dummy_llm():
    chain = create_chain_lcel(llm=DummyLLM())
    out = chain.invoke({"context": "abcdef"})
    assert isinstance(out, str)
    assert out.startswith("ECHO:")
