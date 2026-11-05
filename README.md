# OpenClaw Assist Bridge

[![Validation](https://github.com/lordratner/openclaw-assist-bridge/actions/workflows/validate.yml/badge.svg)](https://github.com/lordratner/openclaw-assist-bridge/actions/workflows/validate.yml)
[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lordratner&repository=openclaw-assist-bridge&category=integration)

Use an existing **OpenClaw agent as your Home Assistant assistant**, including
its normal knowledge, memory, skills, tools and history—not a second, unrelated
chatbot. This is the **Home Assistant-side custom integration**, displayed as
**OpenClaw Home Assistant** in HA/HACS. It requires the companion
[Home Assistant Assist plugin](https://github.com/lordratner/homeassistant-assist)
on your OpenClaw Gateway.

## Who it is for, and why use it?

For people who already run HA and OpenClaw and want the same agent in Assist
chat, voice satellites and automations. Use it for conversations, optional native
HA device control, text/spoken automation queries and interactive satellite
conversations. It is not a standalone assistant, an OpenClaw installer or
replacement satellite firmware.

You do **not** have to move speech providers to OpenClaw:

- **Conversation only:** HA STT → OpenClaw conversation → HA TTS. Keep your
  existing local engines; no OC speech provider or FFmpeg is needed.
- **All OpenClaw:** OC-backed STT → OpenClaw conversation → OC-backed TTS.
- **Mixed, or text only:** select STT and TTS independently, or omit the speaker
  from the query action.

## What runs where?

| Location | Install / responsibility |
| --- | --- |
| Home Assistant host | **This integration**, under `custom_components/openclaw_voice/`; registers native conversation/STT/TTS entities plus `query` and `start_conversation` actions |
| OpenClaw Gateway host | The [companion plugin](https://github.com/lordratner/homeassistant-assist) selects one existing agent and uses OC's normal history, model, tools, policy and optional speech providers |
| Satellite or speaker | Your existing HA device and selected Assist pipeline; a media player can play speech but is not an interactive microphone |

HA owns pipeline selection, exposed entities, device formats and playback. OC
owns the agent and its other tool permissions. HA's exposed-entity policy governs
native Assist calls, not unrelated tools already granted to that agent. Hosts
can be separate machines: HA must reach the existing OC Gateway URL; no extra
plugin listener/port is needed. Provider credentials stay with their owning
platform. HA stores only a scoped pairing token, not provider keys or an OC
admin token. Pairing does not identify the human speaker.

## Minimum versions and stock compatibility

**Yes: both components work with unmodified, stock Home Assistant and OpenClaw
cores.** Install this project's HA custom integration and OpenClaw plugin through
their normal extension mechanisms; no core fork, patch, custom Assist pipeline
engine, MCP server or SSH bridge is required.

| Component | Minimum supported version / requirement |
| --- | --- |
| Home Assistant Core | **2026.10.4**; older HA releases are not supported |
| OpenClaw | **2026.10.3**; older OC releases are not supported |
| This project's pair | OpenClaw plugin **0.0.1** + HA integration **0.0.1**, protocol **1.2** |
| Node.js on the OC host | For the tested Node 24 line, **24.16.0 or newer within 24.x**; follow OC's own engine requirements, not just the plugin's looser metadata |
| Python on the HA host | **3.14.2+**, normally managed by HA OS/Container; not a separate install step on those systems |
| FFmpeg on the OC host | Required **only for OC-backed TTS**; not needed for conversation, OC STT or HA-native TTS. Version 7.1.5 was exercised; no older FFmpeg minimum has been established |
| HACS | Optional installation convenience for the HA component; manual installation is also supported |

These are the **supported version floors**, not a claim that every later release
has been tested. Plugin CI passes against stock OC **2026.10.3 and 2026.10.10**.
The complete archive-loaded native-pair proof passes on stock **OC 2026.10.10 +
HA 2026.10.4**; use that combination to match the end-to-end evidence. Other
versions above the floors still need compatibility checks. The plugin's current
peer-dependency declaration deliberately lists the two tested OC versions.

The proof uses synthetic providers and devices with real host APIs. It verifies
pairing, conversation/tools, batch STT, TTS and follow-up decisions—not every
provider account, physical speaker or satellite. See [compatibility](docs/COMPATIBILITY.md)
and [acceptance evidence](docs/ACCEPTANCE.md).

## Install and pair

Current public release: **0.0.1** (HA dev.7 implementation; companion plugin
dev.11 implementation). Both releases are non-prereleases:

- [HA integration release and manual archive](https://github.com/lordratner/openclaw-assist-bridge/releases/tag/0.0.1)
- [Required OC plugin archive and checksums](https://github.com/lordratner/homeassistant-assist/releases/tag/0.0.1)

### 1. Prepare the OpenClaw side

Install the companion plugin **on the OC host** using its
[README](https://github.com/lordratner/homeassistant-assist#install-and-connect)
and [installation guide](docs/INSTALL.md). Select an existing `agentId`, grant
`hooks.allowConversationAccess` for conversation, and activate through OC's normal
plugin lifecycle. The plugin is a GitHub release archive, not an npm publication.
HA installation alone does not install/configure OC or its providers.

### 2. Install this integration in HA

With HACS already installed, use the **Open in HACS** button above, or:

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/lordratner/openclaw-assist-bridge` as **Integration**.
3. Download **OpenClaw Home Assistant**. Release **0.0.1** needs no **Show beta
   versions** toggle; that toggle is for historical development releases.
4. Restart Home Assistant to load the Python code.

HACS installs **only the HA integration**, not the OC plugin. Custom-repository
installation does not require HACS default-catalog inclusion, and catalog approval
is not claimed here. Without HACS, verify the release checksum and extract the
manual archive's `custom_components/openclaw_voice/` into HA's configuration
directory, then restart HA. See [install, upgrade and rollback](docs/INSTALL.md).

Existing manual installation: back up first, let HACS manage the same component
directory, and restart HA. **Keep the existing config entry, entities and pairing**;
do not delete/re-pair or create a duplicate simply to change install methods.

### 3. Pair and choose your pipeline

On the OC host, issue a private one-use code:

```sh
openclaw gateway call openclaw_home_assistant.pairing.issue --params '{"label":"Home Assistant"}' --json
```

In HA, open **Settings → Devices & services → Add integration → OpenClaw Home
Assistant**. Enter the Gateway base URL and code (expires in five minutes), not
the owner token. Use HTTPS across untrusted networks and protect HA backups,
which contain the scoped token.

Choose persistent history or a fresh session per conversation; fresh history
still uses the agent's normal knowledge, memory, skills and tools. In
**Settings → Voice assistants**, choose the OpenClaw conversation entity and the
STT/TTS engines you want, then assign that assistant to your device. You need not
select all three OC entities. Installation does not change default/preferred
pipelines or other rooms.

For native HA control, enable **Device control** in integration Options and allow
`home_assistant` under the OC agent's normal tool policy. Explicit follow-up intent
uses `voice_conversation`; it also needs a suitable model and satellite. Keep
control disabled if you only want conversation. See [setup](docs/PRODUCT.md) and
[native Assist authorization](docs/NATIVE-ASSIST.md).

## Speech-to-text and the upstream PRs

**You do not need any unmerged PR to use this pair.** On the tested stock OC
versions, OC-backed STT transcribes the completed utterance through OC's native
**batch** API. Alternatively, keep HA's existing STT engine. Conversation and
TTS are independent of the optional realtime-STT work.

Upstream status checked **2026-11-04**:

| OpenClaw PR | Purpose | Required to use the pair? |
| --- | --- | --- |
| [#187371](https://github.com/openclaw/openclaw/pull/187371) — **open** | Adds an optional finite-input streaming-transcription runtime so a plugin can send audio during capture and await a finalized transcript | **No.** Needed only for this plugin's optional realtime STT path, with a supporting provider/model |
| [#187369](https://github.com/openclaw/openclaw/pull/187369) — **merged Nov. 2** | Makes realtime transcription honor configured environment proxies | **No.** Relevant to that realtime transport when using such proxies; a merge alone does not prove inclusion in your installed OC release |
| [#189044](https://github.com/openclaw/openclaw/pull/189044) — **open** | Preserves realtime STT provider/connection failure codes for better diagnostics and retry decisions | **No.** Unknown/flattened failures stay conservative rather than being blindly retried |
| [#189043](https://github.com/openclaw/openclaw/pull/189043) — **open** | Related TTS failure-metadata improvement | **No.** Improves diagnosis/retry classification, not basic conversation or speech availability |

Installing our plugin does **not** install these core changes. Use ordinary stock
batch STT or HA-native STT unless your host supplies the optional runtime; do not
patch core merely to get started. A realtime-only OC model needs an explicit
batch-capable alternative (`stt.batch`), or choose HA STT. The plugin does not
invent provider/model aliases. Unsupported streaming can fall back before audio
is consumed; admitted failures never silently switch to batch or another provider.
No partial transcript is dispatched to the conversation agent. See
[SDK notes](docs/SDK-GAPS.md) and [speech recovery](docs/SPEECH-RELIABILITY.md).

## Use it from automations

### Ask, with optional speech

```yaml
action: openclaw_voice.query
data:
  config_entry_id: YOUR_ENTRY_ID
  prompt: "Give me a short update."
  session_mode: per_conversation
  speaker: media_player.YOUR_SPEAKER
response_variable: answer
```

Omit `speaker` for text only. With a speaker, speech defaults to OC TTS; add
`tts_entity: tts.YOUR_EXISTING_ENGINE` to use an HA engine instead.
`assist_satellite` targets are also supported. Pass the returned `conversation_id`
to continue the same conversation. Results contain response/job/request IDs and
`speech_requested`; that is **not** confirmation that a speaker was audible.
Overlapping queries on the same HA conversation are rejected before another turn.

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
use a pipeline with this connection's conversation entity. Otherwise it fails
before playback/listening. Follow-ups preserve the chosen session mode; no global
settings or private satellite fields are changed. Physical wake-word-free
listening still depends on the device and must be observed on your hardware.

## Troubleshooting and documentation

Availability is per stage: missing OC TTS does not break a conversation-only
pipeline. Capabilities refresh every 30 seconds. Diagnostics exclude conversation
text, audio, credentials and connection/session identities; local bounded timing
samples measure receipt, not when a speaker becomes audible. Model/thinking/fast
preferences can change through OC's owner-only inference API without reloading
HA; the paired token cannot administer them.

Speech recovery is bounded. It never replays a conversation/device action or
retries TTS after partial output. HA retrieves the same admitted job instead of
starting it again. [Protocol](docs/PROTOCOL.md) covers limits and recovery.

- [Product setup, mixed pipelines and configuration lifecycle](docs/PRODUCT.md)
- [Install/upgrade/rollback](docs/INSTALL.md)
- [Logging](docs/LOGGING.md), [timing](docs/TIMING.md) and [speech reliability](docs/SPEECH-RELIABILITY.md)
- [Compatibility](docs/COMPATIBILITY.md), [acceptance](docs/ACCEPTANCE.md) and [quality checklist](docs/QUALITY.md)

## Development

Python **3.14.2+**; the test lock pins stock HA **2026.10.4**.

```sh
uv venv --python 3.14 .venv
uv pip sync --python .venv/bin/python requirements-test.lock
.venv/bin/python scripts/validate_package.py
.venv/bin/python -m pytest -q
```

Run `npm run test:native-pair` in the sibling OC plugin checkout for the isolated
production-plugin/native-HA proof. Synthetic providers/devices are not real-account,
physical playback or acoustic-latency evidence. Review archives contain only
`custom_components/openclaw_voice/` source/metadata, excluding caches and `.pyc`.
See [engineering history](implementation/STATUS.md) for earlier candidate evidence.

### Repository rename and license

Renamed from `home-assistant-openclaw-voice` to `openclaw-assist-bridge`. The
`openclaw_voice` domain, action/entity IDs and existing settings are unchanged.
HA/HACS still displays **OpenClaw Home Assistant**; the rename alone needs no
reinstall or re-pairing.

Original source is MIT: [LICENSE](LICENSE), [provenance](THIRD_PARTY_NOTICES.md).
