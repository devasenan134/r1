# R1 — architecture & design decisions

**R1 is a desk pet with a dumb body and a private brain. The phone is just an eye and a face; all the perception and all the thinking run on my own laptop over the LAN; nothing touches the cloud.** This doc is the *why* behind that — the decisions I've actually committed to, and the ones I killed on purpose.

## The shape

Three parts, one rule: the body never thinks.

```
app/        the phone — a dumb eye + face (Capacitor Android)
server/     the orchestrator — senses + brain call (Python)
firmware/   the ESP32 body — motors, later (PlatformIO)
```

- The **brain** is my own Qwen, reached through an Ollama-style `/api/generate`. It stays private, it stays free, and it's one config line to swap.
- The **orchestrator** is pure Python and config-driven, so it runs wherever I want it to. Location is config, not code.
- The **phone** captures and plays — audio, a camera frame, a face. It never reasons about anything.

That split is the whole point. Each layer is the only thing that knows its own backend, so replacing one touches nothing else.

## Keeping the logic out of the frontend

I don't want to write HTML, JS or Kotlin — *"i wanted to program these logic by myself, but i dont want to do html, js or kotlin."* So the phone frontend stays deliberately thin and generic: the face, the mic/camera plumbing, the WebSocket client, and nothing more. Every decision that actually matters — the perception, the senses, the brain call — lives in the Python orchestrator, my strongest language. The ESP32 firmware is the same story: a dumb body driven from the orchestrator.

## The big decision: the phone does not stream its camera to the AI

I started with the obvious idea — point the phone's camera at the room, stream the live feed to the model, let the pet "watch" and react. I talked myself out of it: *"i thought accessing phone's camera and streaming live feed to AI will enable the pet to continously look around and react to its surroundings but i dont think that would be efficient and practical."*

That instinct was right. Feeding every frame to the VLM is expensive, laggy, and hot — it burns battery and says nothing new most of the time. Nothing alive reasons about every frame. So I killed that idea and settled on a **tiered nervous system**:

- **cheap, always-on senses decide *when* the pet thinks** — motion, sound level, movement;
- **the camera snapshot is only *what* it thinks about**, in that one moment;
- **the expensive brain (Qwen) stays episodic** — it wakes up when something is actually worth a thought, not on a timer.

## How perception runs

Perception does **not** live in `index.html`. It lives in the Python orchestrator — which is exactly what the project already preaches ("the device never thinks… everything else lives in the orchestrator"). The phone stays a thin eye + face and streams cheap cues to the laptop; I write the CV and the logic in Python.

The transport is a **continuous low-res stream** — video frames + mic level + accelerometer — from phone to laptop over WiFi. LAN latency is a non-issue (~2–30 ms round-trip, under 2 Mbit/s for low-res frames). The real cost is inference and a frame queue backing up, so the rule is simple: **always process the latest frame, drop the backlog.** One frame in flight at a time.

The pipeline I'm building toward:

```
phone (dumb) --WiFi stream--> orchestrator:
    frames + mic + accel  ->  saliency map (motion + sound + face)
                          ->  + habituation (decay) + novelty (preempt)
                          ->  arousal threshold crossed?
                               -> look / react   (cheap, local)
                               -> escalate to Qwen  (rare, "thinking")
    -> commands back to phone (face) + ESP32 (body)
```

## Why this, grounded in what the pros do

I checked this against real robots before committing:

- **Cozmo** streamed 15fps to the phone and let the phone do all the vision — body dumb, brains elsewhere. Same split I'm using.
- **Vector / Aibo** run perception locally and reserve the big brain for language and personality. Episodic thinking, not constant.
- **EMO / Lovot** lean on cheap non-camera senses — touch, mic-array sound direction, thermal. The pros use the camera *least*.
- **Kismet** (MIT, Breazeal/Scassellati) is the academic answer to "how do you process the senses": fuse cues (motion + sound + face) into one **saliency / arousal map**, add **habituation** (get bored of constant stimuli) and **novelty** (a strong or new stimulus preempts), threshold it, and only then escalate. Sony's emotion patent uses the same arousal-axis + behavior state-machine bones.
- The cautionary tale is **Anki**: Cozmo and Vector bricked when the company folded because they leaned on the cloud. That's exactly what my self-hosted Qwen orchestrator is built to never do.

## The brain contract

The orchestrator talks to the brain over HTTP and keeps it dumb-simple. Replies are capped short on purpose (`num_predict`) — an uncapped Qwen answer runs ~25s; capped, it lands well under a second. Short *is* the personality: R1 answers in one or two spoken sentences, no lists, no markdown, no emoji.

## Senses transport — the step-1 contract

Before stacking any CV on top, I'm proving the pipe and clocking real latency on my own network. The seam the phone and orchestrator both build to:

- **`/senses`** — a WebSocket on the orchestrator.
- Phone → server (JSON text): `{"t": <client ms>, "seq": <n>, "frame": "<payload>"}`.
- Server → phone: **echo it straight back, verbatim.** No processing — a pure echo is enough to measure the round trip.
- Phone computes `RTT = now − t`, with one frame in flight at a time.

One deliberate simplification for step 1: the phone sends a **synthetic payload the size of a real low-res frame (~18 KB)**, not a camera image. That lets me measure latency from a plain browser tab, with no camera permission and no APK rebuild. Real frames go in once the number looks good.

See [progress.md](progress.md) for where each piece stands and what's next.
