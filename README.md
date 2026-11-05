# OpenClaw Assist Bridge

[![Validation](https://github.com/lordratner/openclaw-assist-bridge/actions/workflows/validate.yml/badge.svg)](https://github.com/lordratner/openclaw-assist-bridge/actions/workflows/validate.yml)
[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lordratner&repository=openclaw-assist-bridge&category=integration)

Connects Home Assistant Assist to an OpenClaw agent for text conversations,
native Assist tools, and optional speech recognition and synthesis.

This repository was renamed from `home-assistant-openclaw-voice` to
`openclaw-assist-bridge`. The integration domain `openclaw_voice`, action/entity
IDs, and existing settings are unchanged. The integration is still displayed as
**OpenClaw Home Assistant** in HA/HACS. Existing installations do not need to be
deleted or re-paired because of this repository rename.

## Install with HACS

Requires **Home Assistant 2026.10.4 or newer**, HACS, and a configured
[companion OpenClaw plugin](https://github.com/lordratner/homeassistant-assist).
This is an initial public release, not universal provider or hardware
certification. HACS installs the HA integration only, not the OpenClaw plugin
or optional OpenClaw core capabilities.

Use the **Open in HACS** button above, or add it manually:

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/lordratner/openclaw-assist-bridge` with type
   **Integration**.
3. Find **OpenClaw Home Assistant** in HACS and download it. Release **0.0.1** does not need
   **Show beta versions** (that toggle is only for older development releases).
4. Restart Home Assistant, then open **Settings → Devices & services → Add
   integration → OpenClaw Home Assistant** and pair with the OpenClaw plugin.

For an existing manual installation, back up first, let HACS manage the same
`custom_components/openclaw_voice` directory, and restart HA. Keep the existing
integration entry; do not delete/re-pair it or create a duplicate just to switch
installation methods. Installation does not change your Assist pipelines.

Custom-repository installation does not require default-catalog inclusion.
Inclusion in HACS's default catalog is subject to HACS review and is not claimed
here. See [installation, upgrades and rollback](docs/INSTALL.md) for details.

## Public release 0.0.1

Plugin **0.0.1** uses the dev.11 implementation; HA integration **0.0.1** uses
the dev.7 implementation, with additive protocol **1.2**. Install the versioned
[plugin archive](https://github.com/lordratner/homeassistant-assist/releases/tag/0.0.1)
and [HA integration](https://github.com/lordratner/openclaw-assist-bridge/releases/tag/0.0.1)
using the [installation guide](docs/INSTALL.md). No npm publication is required.
This initial public release does not certify every provider, satellite or runtime.
Start with [setup](docs/PRODUCT.md) and [compatibility](docs/COMPATIBILITY.md).
Older versioned sections below are historical engineering notes.

Use OpenClaw conversation with existing HA speech providers, all three OC
entities, or a mix. Missing OC speech dependencies do not disable text chat.
Streaming is preferred automatically and unsupported capabilities use native
batch/buffered paths; interrupted admitted work is never blindly repeated.


Native Home Assistant STT, streaming conversation and streaming-text TTS entities,
backed by the companion [OpenClaw plugin](https://github.com/lordratner/homeassistant-assist).
OC owns the selected agent, normal tools/memory/policy, actual persistent session,
model/thinking/fast and provider credentials. HA chooses mode and playback target.

**Integration 0.0.1**, based on dev.7. Config/options/reauth, all three entities
and both actions are exercised with real HA APIs in disposable runtimes.
Real-provider and physical listening behavior remain deployment-specific.
HACS custom-repository installation is supported; default-catalog inclusion is separate.

## Setup and use

After installing through HACS or manually, add **OpenClaw Home Assistant** in
Settings → Devices & services. Enter the Gateway base URL and a one-use pairing
code issued by its administrator. Choose persistent history or a fresh session
per conversation. Only the scoped voice token is stored in HA's config entry;
protect HA backups. Provider keys and Gateway owner credentials stay out of HA.

Select the three entities in an Assist pipeline yourself. Installation does not
change preferred/default pipelines. Existing conversations keep their selected
mode across options edits and integration reload; a fresh session retains normal
agent knowledge, memory, skills and tools.

### Ask and optionally speak

```yaml
action: openclaw_voice.query
data:
  config_entry_id: YOUR_ENTRY_ID
  prompt: "Give me a short update."
  session_mode: per_conversation
  speaker: media_player.YOUR_SPEAKER
response_variable: answer
```

Omit `speaker` for text only. `assist_satellite` targets are also supported.
The structured result contains conversation/mode/job/request IDs, response and
`speech_requested`. It is not an acknowledgment of audible playback. Pass the
returned `conversation_id` to continue that conversation without changing mode.
An overlapping query on the same HA conversation is rejected before another turn.

### Start an interactive satellite conversation

```yaml
action: openclaw_voice.start_conversation
data:
  config_entry_id: YOUR_ENTRY_ID
  satellite_id: assist_satellite.YOUR_SATELLITE
  start_message: "What would you like to do?"
  session_mode: per_conversation
response_variable: interaction
```

The satellite must support HA's native start-conversation service and already
select a pipeline using this connection's conversation entity. Otherwise the
action fails before starting playback/listening. Follow-ups keep the override;
no global settings or private satellite fields are changed.

## Documentation

- [Install/upgrade/rollback](docs/INSTALL.md)
- [Protocol, limits, retention and recovery](docs/PROTOCOL.md)
- [Evidence and remaining gates](docs/ACCEPTANCE.md)
- [Native streaming-transcription capability and fallback](docs/SDK-GAPS.md)
- [Detailed planning baseline](planning/00-README.md)
- [Current development checkpoint](implementation/STATUS.md)

TTS uses a single canonical WAV stream. HA device-specific format preferences
still apply and can add conversion latency. HA streams bounded PCM microphone
chunks to OC. The companion plugin can use provider-dependent realtime
STT when the host supplies the reviewed optional finite-transcription runtime
(including the separately prepared core backport); only a completed transcript
is returned for conversation processing. Older hosts or unsupported selections
retain native batch STT. A failed admitted stream is never automatically replayed
through batch or another provider. A bridge update alone does not install the
core capability, and not every provider/model supports it.

Existing HA integration dev.3 needs no code update or restart solely for this STT
capability or the bridge's clarification repair. Backend capabilities/profile
refresh every 30 seconds. Explicit per-turn continuation intent is forwarded to
HA's native conversation result; actual wake-word-free listening after playback
still needs a satellite observation. Unconsumed action playback expires after
60 seconds; normal HA cache/URL retention remains HA-owned.

Diagnostics are allowlisted and exclude connection/agent/client/session identities,
credentials, conversation text and audio. Reauthentication creates a new scoped
identity; old conversations must not silently adopt a new agent or profile.

Local diagnostics retain at most 20 conversation/TTS timing samples in memory,
including first text/audio received and completion/close/failure offsets. These
do not measure when the speaker becomes audible. Model/thinking/fast preferences
can be changed through the companion plugin's owner-only `inference.get` and
`inference.update` Gateway methods without reloading HA or losing its current
conversation. The HA client token does not receive model-administration rights.

## Development

Python >=3.14.2; the lock file pins the tested HA 2026.10.4 environment.

```sh
uv venv --python 3.14 .venv
uv pip sync --python .venv/bin/python requirements-test.lock
.venv/bin/python -m pytest -q
```

Run `npm run test:native-pair` in the sibling OC checkout for the full isolated
production-plugin/native-HA proof. Synthetic providers and satellite fixtures
are not real-provider latency or audible-playback evidence.

For a review archive, include only `custom_components/openclaw_voice/` source
and metadata, excluding `__pycache__`/`.pyc`. The repository also has HACS metadata;
public source availability does not imply a stable release, an official HACS listing,
or a change to satellite firmware.

Original source is MIT; see [LICENSE](LICENSE) and [provenance](THIRD_PARTY_NOTICES.md).

## Native HA Assist tools (candidate dev.3)

The [native Assist bridge](docs/NATIVE-ASSIST.md) forwards HA’s own prompt/tool API and executes callbacks through HA’s ChatLog. Enable Device control in HA options; allow the `home_assistant` tool in the selected agent’s policy. No MCP or SSH dependency. Existing entries keep control disabled until explicitly selected. Local-first pipeline choices remain untouched.

### Stale conversation recovery

Bridge dev.7 and HA dev.4 recover a retained native satellite chat ID after
voice-profile change or expiry, without replacing native session/history.
Recovery is bounded to one explicit pre-admission refresh/reopen; known or
uncertain admitted work never redispatches. See [protocol](docs/PROTOCOL.md).

### Structured diagnostics

The logging candidate adds consistent bounded lifecycle/error logs across both
products, persistent safe failure summaries, cross-layer request/job correlation,
and diagnostics readable during startup/storage failure. No transcript/audio/key
logging is enabled. Bounded speech retry is described below. See [logging contract](docs/LOGGING.md).

## Speech retry and health logging

Speech recovery has one owner and at most one additional bridge attempt per eligible streaming STT/TTS job. There is no whole-pipeline replay or retry after partial TTS output. Batch-only setups keep native OpenClaw retry policy without an added bridge retry. Successful health polling stays DEBUG; availability transitions and real voice work remain visible. See [speech reliability](docs/SPEECH-RELIABILITY.md) for eligibility, cancellation, native SDK limits and diagnostic metadata.
