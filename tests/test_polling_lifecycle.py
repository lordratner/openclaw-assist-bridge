from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.openclaw_voice.client import VoiceClient, VoiceTransportError
from test_ha_setup import hass, configure, CAPS, PAIRED


@pytest.mark.asyncio
async def test_native_runtime_refresh_records_outage_count_and_recovery_without_poll_flood(hass):
    with patch.object(VoiceClient, "pair", AsyncMock(return_value=PAIRED)), \
            patch.object(VoiceClient, "capabilities", AsyncMock(return_value=dict(CAPS))):
        entry = await configure(hass)
        runtime = entry.runtime_data
        for _ in range(20):
            await runtime.refresh()
        unavailable = VoiceTransportError("backend_unavailable", diagnostic={"category": "transport", "system_code": "ENETUNREACH"})
        with patch.object(VoiceClient, "capabilities", AsyncMock(side_effect=unavailable)):
            for _ in range(3):
                with pytest.raises(UpdateFailed):
                    await runtime.refresh()
        await runtime.refresh()
        snapshot = runtime.diagnostics.snapshot()
        assert snapshot["availability"]["checks"] >= 24
        assert snapshot["availability"]["failures"] == 3
        assert snapshot["availability"]["available"] is True
        assert snapshot["availability"]["last_failure"]["system_code"] == "ENETUNREACH"
        failure_events = [e for e in snapshot["failures"] if e["operation"] == "availability"]
        assert len(failure_events) == 1
        restored = [e for e in snapshot["recent"] if e["operation"] == "availability" and e["phase"] == "restored"]
        assert restored[-1]["count"] == 3
        assert snapshot["stats"]["observer_failures"] == 0
