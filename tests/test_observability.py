import asyncio
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from custom_components.openclaw_voice.observability import Diagnostics, failure_summary, safe_fields, observe
from custom_components.openclaw_voice.transport import VoiceTransportError


def test_paired_classification_contract_and_nested_failure_size_bound():
    cases = json.loads(Path(__file__).with_name("fixtures").joinpath("logging-contract-cases.json").read_text())
    for value in cases:
        error = VoiceTransportError(value["code"], diagnostic={"http_status": value.get("status"), "provider_code": value.get("provider_code")})
        assert failure_summary(error)["category"] == value["category"], value
    grouped = ExceptionGroup("PRIVATE", [ExceptionGroup("PRIVATE", [OSError(13, "PRIVATE") for _ in range(4)]) for _ in range(20)])
    assert len(json.dumps(failure_summary(grouped), separators=(",", ":")).encode()) <= 1024
    assert failure_summary(grouped)["truncated"] is True


def test_safe_fields_are_closed_and_nested_causes_do_not_leak_content():
    private = "PRIVATE_AUDIO_TEXT_TOKEN_URL"
    error = VoiceTransportError("backend_job_failed", diagnostic={"category": "authentication", "http_status": 401,
        "stage": "stt_transcription", "message": private})
    value = failure_summary(ExceptionGroup(private, [error, ValueError(private)]))
    assert value["category"] == "authentication"
    assert value["http_status"] == 401
    assert value["failure_count"] == 2
    assert private not in json.dumps(value)
    assert safe_fields({"reason": [], "mode": {}, "message": private, "provider_code": private}) == {}
    nested = {"causes": [{"message": private, "causes": [{"message": private}]}]}
    assert private not in json.dumps(safe_fields(nested))


def test_aiohttp_network_and_owned_timeout_classification_keeps_cause_without_private_data():
    import aiohttp
    import errno
    import socket
    from aiohttp.client_reqrep import ConnectionKey
    key = ConnectionKey("private.invalid", 443, True, True, None, None, None)
    unreachable = aiohttp.ClientConnectorError(key, OSError(errno.ENETUNREACH, "PRIVATE"))
    network = failure_summary(unreachable)
    assert network["category"] == "transport"
    assert network["system_code"] == "ENETUNREACH"
    dns = failure_summary(aiohttp.ClientConnectorDNSError(key, socket.gaierror(socket.EAI_AGAIN, "PRIVATE")))
    assert dns["category"] == "transport" and dns["system_code"] == "EAI_AGAIN"
    timeout = TimeoutError("PRIVATE")
    timeout.__cause__ = asyncio.CancelledError()
    outer = failure_summary(timeout)
    assert outer["category"] == "timeout" and outer["exception_type"] == "TimeoutError"
    assert failure_summary(asyncio.CancelledError())["category"] == "cancelled"
    assert "PRIVATE" not in json.dumps([network, dns, outer])


def test_polling_does_not_evict_voice_failures_and_availability_logs_are_transition_based():
    class Logger:
        def __init__(self):
            self.lines = []
        def debug(self, *args):
            self.lines.append(("debug", args))
        def info(self, *args):
            self.lines.append(("info", args))
        def warning(self, *args):
            self.lines.append(("warning", args))
    logger = Logger()
    diag = Diagnostics(logger=logger, limit=8, failure_limit=4)
    with pytest.raises(RuntimeError):
        with diag.start("tts", "pipeline"):
            raise RuntimeError("PRIVATE")
    for _ in range(300):
        with diag.start("connection", "refresh"):
            with diag.start("http", "control") as span:
                span.phase("response_headers", http_status=200)
            diag.poll_result()
    unavailable = VoiceTransportError("backend_unavailable", diagnostic={"system_code": "ENETUNREACH", "category": "transport"})
    for _ in range(200):
        with pytest.raises(VoiceTransportError):
            with diag.start("connection", "refresh"):
                with diag.start("http", "control"):
                    diag.poll_result(unavailable)
                    raise unavailable
    with diag.start("connection", "refresh"):
        diag.poll_result()
    data = diag.snapshot()
    assert any(e["component"] == "tts" for e in data["failures"])
    changes = [e for e in data["recent"] if e["operation"] == "availability"]
    assert [e["phase"] for e in changes] == ["ready", "failed", "restored"]
    assert changes[-1]["count"] == 200
    assert data["availability"]["failures"] == 200
    assert data["availability"]["consecutive_failures"] == 0
    assert data["stats"]["failures_evicted"] == 0
    assert data["stats"]["polling_events"] > 500
    assert data["stats"]["observer_failures"] == 0
    assert "PRIVATE" not in json.dumps(data)


@pytest.mark.asyncio
async def test_async_generator_does_not_leak_context_and_can_close_from_another_task():
    owner = SimpleNamespace(diagnostics=Diagnostics())

    @observe("tts", "fixture")
    async def source(self):
        for _ in range(100):
            yield {"type": "chunk", "audio": b"PRIVATE"}

    stream = source(owner)
    await anext(stream)
    assert owner.diagnostics.current() is None
    await asyncio.create_task(stream.aclose())
    assert owner.diagnostics.current() is None
    assert any(e["phase"] == "cancelled" for e in owner.diagnostics.snapshot()["recent"])
    assert "PRIVATE" not in json.dumps(owner.diagnostics.snapshot())


@pytest.mark.asyncio
async def test_stream_chunk_count_does_not_increase_event_volume_or_suppress_work():
    class BrokenLogger:
        def __getattr__(self, name):
            def fail(*args):
                raise RuntimeError("logger failed")
            return fail
    owner = SimpleNamespace(diagnostics=Diagnostics(logger=BrokenLogger()))

    @observe("stt", "fixture")
    async def source(self, count):
        for _ in range(count):
            yield {"audio": "PRIVATE"}

    assert len([v async for v in source(owner, 1000)]) == 1000
    events = owner.diagnostics.snapshot()["recent"]
    assert len(events) == 3  # start, first output, terminal — not one per chunk
    assert events[-1]["frames"] == 1000
    assert "PRIVATE" not in json.dumps(events)


def test_failure_history_survives_success_volume_and_native_logs_are_rate_bounded():
    class Logger:
        count = 0
        def warning(self, *args):
            self.count += 1
        def debug(self, *args):
            pass
    logger = Logger()
    owner = Diagnostics(logger=logger, limit=5, failure_limit=3)
    for _ in range(100):
        with pytest.raises(TimeoutError):
            with owner.start("http", "fixture"):
                raise TimeoutError("PRIVATE")
    assert len(owner.snapshot()["recent"]) == 5
    assert len(owner.snapshot()["failures"]) == 3
    assert logger.count == 9
    assert owner.current() is None
