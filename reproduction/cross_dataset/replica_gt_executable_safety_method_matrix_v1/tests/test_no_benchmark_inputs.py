from pathlib import Path


def test_directional_generator_has_no_reference_or_benchmark_imports():
    root = Path(__file__).resolve().parents[1] / "alternative_library"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = ("import reference", "from reference", "import oracle", "from oracle", "import benchmark", "from benchmark")
    assert not any(token in source for token in forbidden)
