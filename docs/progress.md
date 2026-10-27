# R1 — progress

Where each part stands, newest first. For the *why* behind any of this, see [architecture.md](architecture.md).

## Status at a glance

| Part | What | State |
|------|------|-------|
| **app** (phone) | face, on-device STT/TTS, camera, hands-free loop, settings | ✅ works, builds to APK |
| **server** (orchestrator) | `/chat` brain proxy, `/health`, serves the app + APK | ✅ chat works |
| **senses transport** | `/senses` WebSocket + latency clock | 🚧 doing — step 1 |
| **saliency map** | motion → sound → face, with habituation + novelty | 🔜 next |
| **firmware** (ESP32) | body / motors | 🪨 still a blank stub |

---

## 2026-10-27 — step 1: prove the senses transport, clock the latency

The first real move toward the tiered senses design: get frames flowing phone → orchestrator over a WebSocket and measure the actual round-trip on my LAN, *before* I write a single line of CV. Prove the pipe, then stack perception on it.

**My side (orchestrator) — in progress:** a `/senses` WebSocket route in `server/main.py` that accepts the connection and echoes every message straight back. Zero processing — it just proves the pipe and lets the phone time the round trip. Run with `--host 0.0.0.0` so the phone on the LAN can reach it.

**Phone side — done:** a 📡 probe button and an RTT HUD (last / avg / p95). It streams frame-sized payloads at 5 fps with strict backpressure — one frame in flight, always the latest, never a backlog. For step 1 it sends a synthetic ~18 KB payload so I can measure latency from a browser tab without a camera permission or an APK rebuild.

**The contract both sides build to:**
```
/senses  (WebSocket)
  phone → server :  {"t": <client ms>, "seq": <n>, "frame": "<payload>"}
  server → phone :  the same message, echoed verbatim
  phone          :  RTT = now − t   (one frame in flight at a time)
```

**Next, once the number looks good:** swap the synthetic payload for real camera frames, then start the saliency map — motion first. why: prove the transport + measure latency before stacking CV on top.

---

## Before that — what was already standing

- **The orchestrator talks to the brain.** `server/main.py` proxies `/chat` to my own Qwen over an Ollama-style `/api/generate`, with replies capped short on purpose. `/health` for a liveness check; `/` serves the app and `/r1.apk` serves the installable so the phone can grab it straight off the LAN.
- **The phone has a face.** `server/static/index.html`: animated eyes that blink, think, talk and listen; on-device speech-to-text and text-to-speech; the front camera; a hands-free conversation loop that stays quiet while R1 thinks so it never hears itself; and a settings panel to point the app at whatever orchestrator URL I'm running. It builds to an APK via Capacitor.
- **The ESP32 firmware is initialized but empty** — a PlatformIO project with the default Arduino stub. The body comes after the senses.
- **`.reference/`** is the earlier CLI-shaped design (host-side STT/TTS/skills/awareness/scheduler) from before the pivot to "the phone *is* the body." Kept as reference, not the live path.
