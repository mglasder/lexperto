import importlib
import sys
import types
from pathlib import Path

# Create dummy modules required by lexperto
agents_mod = types.ModuleType("agents")
class DummyAgent:
    def __init__(self, *args, **kwargs):
        pass
class DummyRunner:
    @staticmethod
    def run_sync(agent, prompt):
        return types.SimpleNamespace(final_output="")
agents_mod.Agent = DummyAgent
agents_mod.Runner = DummyRunner
sys.modules.setdefault("agents", agents_mod)

fpdf_mod = types.ModuleType("fpdf")
fpdf_mod.FPDF = object
sys.modules.setdefault("fpdf", fpdf_mod)

docx_mod = types.ModuleType("docx")
docx_mod.Document = lambda path: None  # will be monkeypatched in tests
sys.modules.setdefault("docx", docx_mod)

dotenv_mod = types.ModuleType("dotenv")
dotenv_mod.load_dotenv = lambda: None
sys.modules.setdefault("dotenv", dotenv_mod)

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

lexperto = importlib.import_module("lexperto")


def test_read_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("hello world", encoding="utf-8")
    assert lexperto.read_file(f) == "hello world"


def test_read_word(monkeypatch):
    fake_doc = types.SimpleNamespace(paragraphs=[
        types.SimpleNamespace(text="line1"),
        types.SimpleNamespace(text="line2"),
    ])
    def fake_document(path):
        return fake_doc
    monkeypatch.setattr(lexperto, "Document", fake_document)
    assert lexperto.read_word("dummy.docx") == "line1\nline2"
