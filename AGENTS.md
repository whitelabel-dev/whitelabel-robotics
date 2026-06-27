# AGENTS.md — entry point for AI agents

**You are an AI agent consulting this repo. Read this file first.**

## what this repo is

Humanoid robotics — MuJoCo simulation layer for the assistive humanoid platform. v0.1 ships a working Unitree G1 simulator running at 26× real-time on a base M4 Mac mini. The strategic role: foundation for the voice-to-embodiment layer of the disability-employment platform.

## quickstart for agents

```sh
cd whitelabel-robotics
source .venv/bin/activate            # if venv already exists
# OR: uv venv --python 3.12 .venv && source .venv/bin/activate && uv pip install mujoco numpy

python demos/smoke_test.py           # headless verification
./.venv/bin/mjpython demos/view_g1.py # interactive viewer (mjpython, NOT python, on macOS)
```

## macOS-specific footgun

Interactive MuJoCo viewer on macOS requires `mjpython`, not `python`. This is because Cocoa requires the main thread to own the window. If you launch `python demos/view_g1.py` you'll get:

```
RuntimeError: `launch_passive` requires that the Python script be run under `mjpython` on macOS
```

The `mjpython` binary ships with the `mujoco` pip package and lives at `.venv/bin/mjpython`. Use it.

## where the big picture lives

- **Mission**: [`whitelabel-principles/doctrines/disability-employment.md`](https://github.com/whitelabel-dev/whitelabel-principles)
- **Operational arm**: [`whitelabel-accessibility`](https://github.com/whitelabel-dev/whitelabel-accessibility)
- **Voice input layer**: [`whitelabel-flow`](https://github.com/whitelabel-dev/whitelabel-flow) (already shipped)
- **Strategic context**: [`whitelabel-strategy`](https://github.com/whitelabel-dev/whitelabel-strategy)

## non-negotiables when working in this repo

Inherits all 6 non-negotiables from the disability-employment doctrine. The two most relevant here:

1. **The assist is the worker's tool, not surveillance of them.** The humanoid is voice-driven by the worker; it doesn't observe + report on them.
2. **Open over proprietary** wherever possible. Unitree publishes free MuJoCo models; K-Scale publishes free hardware designs; MuJoCo is Apache-2.0. Avoid getting locked into a closed humanoid platform when the open alternatives are catching up fast.

## what doesn't exist yet

Most things. v0.1 is just "simulator alive + humanoid loaded + falls over." See the roadmap in README.md for the v0.2-v1.0 work.
