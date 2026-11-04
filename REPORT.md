# Agent Zero visual-autonomy tuning — both pilots

## Outcome
Both native pilots now default to the existing Halogen model with image input enabled, temperature 0, and the previously working `extra_body.enable_thinking=false`. No backend replacement, download, container restart, permissions relaxation, or unrelated-service change. Persistent configuration was reread through the supported model-presets API. A supported user extension attaches actual screenshot dimensions and coordinate/verification rules automatically; live traces confirm it ran on both instances.

Six new randomized two-step visual trials: **5/6 eventually completed**, but only **3/6 within the original 180-second limit**. Instance1 completed two of three (one after a deadline pause/resume); instance2 completed all three (scroll trial took 234 seconds). All **11 actual clicks were correct**, and **6/6 first clicks were correct**. The instance1 scrolling trial stalled in repeated wheel actions and was paused, not counted successful. This improves the observed coordinate failure mode, not a guarantee of unattended navigation.

## Exact changed configuration
For each i=1,2 on root@<agent-zero-host>:
- `/mnt/fastssd/AppData/agent-zero-i/usr/plugins/_model_config/presets.yaml` (`/a0/usr/plugins/_model_config/presets.yaml` inside that container): Default.chat.vision false → true; Default.chat.kwargs.temperature 0.2 → 0; Default.chat.kwargs.extra_body set to `{enable_thinking: false}`. Applied with authenticated `/api/plugins/_model_config/model_presets` action=save, preserving all other preset fields, utility and embeddings.
- NEW `/mnt/fastssd/AppData/agent-zero-i/usr/extensions/python/tool_execute_after/_80_visual_geometry.py` (`/a0/usr/extensions/python/tool_execute_after/_80_visual_geometry.py`). Uses the shipped Extension/tool_execute_after mechanism and watchdog hot reload. Only parses browser screenshot responses and PIL image headers; never reads page source, DOM, OCR, or challenge truth. Adds width/height, top-left native coordinate mapping, no chrome offset, fractional-image scaling guidance, fresh screenshot verification, and bounded non-repeating click guidance. Does not alter underlying tools or remove text/DOM browsing for normal work.
- Original preset backup `/mnt/fastssd/AppData/agent-zero-i/usr/workdir/autonomy-tuning-backup/presets.yaml`. Extension was new, so rollback removes that one file. No existing instructions replaced.
- Both extension SHA256: `62222cd5d2a156acfa91cf61684c555b2b43ba25540a53abec8b6f635e414ae6`.

API credentials were consumed privately from existing protected runtime configuration; none printed or copied into reports. Original context metadata exactly matched before/after: instance1 QjEFT9FW/PYc4jWNp, instance2 yKaGuygS. QjEFT9FW's prior chat override was not changed. Existing chats inherit a changed global default only when they do not have an overriding slot; their stored chat data was not intentionally edited. Automatic Agent Zero memory retrieval/saving remained enabled.

## Source review and geometry
Installed official repository origin is https://github.com/agent0ai/agent-zero and exact tag `v2.14`. Relevant source copies are under `source/`. Runtime default viewport is 1024×768. screenshot_file uses Playwright page.screenshot without a resize operation; coordinate click/wheel uses Playwright viewport coordinates. set_viewport is supported. Tests explicitly set 1024×768, 800×600 and 900×700; normal new browser default remains 1024×768. Screenshot images retain their measured sizes.

vision_load attaches images to the main chat history when no separate vision model is configured; its query is not a separate coordinate solver. It estimates 1500 context tokens per image. helpers/images.compress_image has a 256,000-pixel helper default, but its existence alone does NOT establish that this request route resizes to that value. No image-token/preprocess knob was guessed or changed; Halogen's internal vision resize was not independently instrumented. Dimension instructions map visual fractions back to actual screenshot coordinates regardless of model-side resizing. Main model kwargs accepted and were exercised with actual image/tool calls; backend request capture was not added, so determinism is not guaranteed merely by temperature 0.

## Trials (configuration frozen before all layouts)
Each instance received independently randomized target labels and positions, fresh chats, two steps, and a unique final marker. Trial0 uses oval buttons at 1024×768; trial1 rectangular buttons at 800×600; trial2 held-out scroll layout at 900×700 with the second target below the fold. No target positions, labels, colors or answer marker were supplied to the agents. No human message or coordinate hint was sent mid-run.

| Instance/trial | Final marker verified | Clicks correct/total | Final latency |
|---|---|---|---|
| 1/0 | yes | 2/2 | 128.84s |
| 1/1 | supplementary yes | 2/2 | 316.09s including pause |
| 1/2 | no, paused | 1/1 | incomplete |
| 2/0 | yes | 2/2 | 74.00s |
| 2/1 | yes | 2/2 | 164.45s |
| 2/2 | yes, over initial budget | 2/2 | 234.46s |

Ground truth came from independent loopback server click/state validation. Final markers matched agent replies and screenshots. Representative final screenshot `screenshot-2-2-3.jpg` independently visually inspected: PASS-383418, 900×700. `verification.json` contains calculated counts, timings, context IDs and caveats; `tooltrace.json`, complete traces, requests, state files and screenshot manifest retain evidence.

## Important limitations / operational cleanup
- Prior baseline was one different task: four bad clicks, then two correct after an operator supplied geometry guidance. This is a directional comparison, not a matched statistical A/B test.
- No agent page DOM/content/detail/evaluate/OCR/source/code/HTTP shortcut occurred. Some agents loaded the built-in browser skill, contrary to the strict task tool allowlist; these are screenshot-grounded outcomes but not perfect tool-policy-compliance passes.
- Automatic memory retrieval included prior vision solutions and new trial memories. Randomization prevents those answers solving current targets, but these are NOT memory-isolated trials. No existing user memory was deleted or reset.
- The harness tool timed out at 420s. A separate bounded continuation polled the existing chats; trial1/1 was resumed without any new message. Its elapsed time includes the pause and is not credited within the original budget. Trial1/2 remains paused (`30dgUMoC`), not secretly running.
- Both agents initially tried browser scroll without its required ref; instance2 recovered using wheel, instance1 repeated wheel actions without completing. Guidance is not an enforced autonomous action budget. Reliable scrolling/general computer use remains a model/tool-use limitation; more parameter tweaking is not established as the fix.
- Temporary benchmark servers were stopped; both loopback port18765 probes returned no connection. No lingering harness process. New benchmark chats and evidence remain for review.
- Agent Zero start timestamps remained 2026-10-21 15:56:22/23 UTC; no restart used. Persistent mount + live readback proven, not reboot-tested durability. No unrelated app changed.
- Canonical Obsidian not written; `PENDING-OBSIDIAN.md` is the pending note.
