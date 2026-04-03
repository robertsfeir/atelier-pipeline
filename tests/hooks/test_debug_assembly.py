"""Debug assembly test (migrated from debug_assembly.bats)."""

from conftest import assemble_agent


def test_assembly(tmp_path):
    output = tmp_path / "cal_assembled.md"
    assert assemble_agent("claude", "cal", output)
    assert output.exists()
    first_line = output.read_text().splitlines()[0]
    assert first_line == "---"
    closing_count = sum(1 for l in output.read_text().splitlines() if l.strip() == "---")
    assert closing_count >= 2
