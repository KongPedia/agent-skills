"""JSONL framing must not split legal Unicode inside JSON string values."""
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eval_jsonl_runner", ROOT / "scripts/run_evals.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_trace_preserves_unicode_string_values_with_lf_or_crlf_framing(separator, ending):
    message = "first" + separator + "second"
    records = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": message}},
        {"type": "item.completed", "item": {"type": "command_execution", "command": "test-command",
                                           "exit_code": 0, "aggregated_output": message}},
        {"type": "turn.completed", "usage": {"input_tokens": 7}},
    ]
    trace = ending.join(json.dumps(record, ensure_ascii=False) for record in records) + ending

    result = runner.parse_trace(trace, {})

    assert result["completed"] is True
    assert result["errors"] == []
    assert result["events"] == [
        {"type": "message", "text": message},
        {"type": "command", "command": "test-command", "exit_code": 0, "output": message},
    ]
    assert result["usage"] == {"input_tokens": 7}


@pytest.mark.parametrize("separator", ["\u0085", "\u2028", "\u2029"])
@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_archive_redacts_nested_secret_keys_in_unicode_jsonl(tmp_path, separator, ending):
    message = "first" + separator + "second"
    credentials = {"OPENAI_API_KEY": "openai-test-secret", "codex_api_key": "codex-test-secret",
                   "anthropic_api_key": "anthropic-test-secret"}
    record = {"type": "item.completed", "item": {"type": "agent_message", "text": message},
              "nested": {"credentials": [credentials]}}
    content = ending.join(json.dumps(item, ensure_ascii=False) for item in
                          [record, {"type": "turn.completed"}]) + ending
    result = {"stdout": content, "stderr": content}

    runner.archive(tmp_path / "trace", result)

    for field in ("stdout", "stderr"):
        archived = (tmp_path / ("trace." + field)).read_bytes().decode()
        assert archived == result[field]
        assert not any(secret in archived for secret in credentials.values())
        records = [json.loads(line) for line in archived.split("\n") if line.strip()]
        assert len(records) == 2
        assert records[0]["item"]["text"] == message
        assert records[0]["nested"]["credentials"] == [{key: "[REDACTED]" for key in credentials}]
        assert runner.parse_trace(archived, {})["completed"] is True


def test_trace_rejects_actual_lf_inside_a_json_string():
    trace = ('{"type":"item.completed","item":{"type":"agent_message","text":"first\n'
             'second"}}\n{"type":"turn.completed"}\n')

    result = runner.parse_trace(trace, {})

    assert result["completed"] is False
    assert len(result["errors"]) == 2
    assert result["errors"][0].startswith("Line 1:")
    assert result["errors"][1].startswith("Line 2:")


@pytest.mark.parametrize("key", ["access_token", "refresh_token", "id_token", "api_key",
                               "openai_api_key", "codex_api_key", "anthropic_api_key"])
def test_archive_redacts_all_sensitive_keys_in_prefixed_json_logs(tmp_path, key):
    secret = "synthetic-secret-for-" + key
    content = "diagnostic: " + json.dumps({"nested": {key.upper(): secret}}) + "\n"
    result = {"stdout": content, "stderr": content}

    runner.archive(tmp_path / "trace", result)

    for field in ("stdout", "stderr"):
        archived = (tmp_path / ("trace." + field)).read_bytes().decode()
        assert archived == result[field]
        assert secret not in archived
        assert "[REDACTED]" in archived
