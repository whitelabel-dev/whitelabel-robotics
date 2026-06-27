# whitelabel-robotics

> Humanoid robotics — MuJoCo simulation today, real hardware later. Foundation for the **assistive humanoid layer** in the disability-employment platform: voice command → simulated (eventually physical) humanoid does the workplace task.

## status

**v0.1 — simulation alive (2026-06-26).** Unitree G1 humanoid loads + steps in MuJoCo at 26× real-time on a base M4 Mac Air. No control policy yet — robot falls over on launch. That's the smoke test.

## quickstart

```sh
cd whitelabel-robotics
uv venv --python 3.12 .venv      # one-time
source .venv/bin/activate
uv pip install mujoco numpy

# headless smoke test (no GUI required)
python demos/smoke_test.py

# interactive 3D viewer (macOS needs mjpython, not python)
./.venv/bin/mjpython demos/view_g1.py
```

## what's in here today

```
whitelabel-robotics/
├── demos/
│   ├── smoke_test.py    ← headless: confirms physics works
│   └── view_g1.py       ← interactive 3D viewer
├── models/
│   ├── unitree_g1/      ← Unitree G1 humanoid (commercial $16K robot)
│   └── unitree_h1/      ← Unitree H1 (larger $90K humanoid)
└── README.md / AGENTS.md
```

## the strategic frame

This isn't "build a humanoid robot company." It's "build the assistive layer that lets a humanoid (or eventually any embodied robot) do workplace tasks under voice/agent direction, so people with motor-skill constraints can do real work."

The stack:

| Layer | What | Where |
|---|---|---|
| **Hardware** | Physical humanoid (eventually) | Unitree G1 ($16K) or K-Scale Stompy ($10K) once we're ready |
| **Simulation** | MuJoCo + Unitree models | this repo |
| **Policy / control** | Pre-trained walking + grasping policies | this repo (v0.2) |
| **Intent layer** | Natural-language → structured robot commands | Claude API + [whitelabel-flow](https://github.com/whitelabel-dev/whitelabel-flow) |
| **Surface** | What the worker actually uses | Voice via Flow + UI via [whitelabel-accessibility](https://github.com/whitelabel-dev/whitelabel-accessibility) |
| **Mission** | Why we're doing this | [whitelabel-principles/doctrines/disability-employment.md](https://github.com/whitelabel-dev/whitelabel-principles) |

## roadmap

| Version | Adds | Status |
|---|---|---|
| **v0.1 (here)** | MuJoCo + Unitree G1 + H1 models + smoke test + viewer | ✓ shipped 2026-06-26 |
| v0.2 | Voice → command parser → motion primitives (wave / step / pick up). Whitelabel Flow voice → Claude API parses → MuJoCo executes. | next |
| v0.3 | Pre-trained walking policy loaded from MuJoCo Playground / Isaac Lab checkpoints. Robot walks on command. | |
| v0.4 | Three.js browser viewer streaming the sim — `robotics.whitelabel.dev`. Anyone can voice-control the humanoid from the web. | |
| v0.5 | Workplace-task vignettes — robot in a sim warehouse / kitchen / office does specific tasks (fetch, sort, assist). Demo videos for SBIR Phase I narrative. | |
| v1.0 | Hardware integration — Unitree G1 or K-Scale Stompy. Voice → physical robot. | |

## why MuJoCo specifically

- **Apple Silicon native** — no x86 emulation, no CUDA dependency
- **Industry standard** for humanoid research (DeepMind, OpenAI, Tesla AI Day demos)
- **Free + open source** — Google released it MIT-licensed in 2021
- **500 Hz physics** at real-time on a base M4 Mac mini, 26× headroom for batched training
- **Unitree, Boston Dynamics, K-Scale, Figure** all publish MuJoCo models of their robots

## related repos

| Repo | Connection |
|---|---|
| [whitelabel-flow](https://github.com/whitelabel-dev/whitelabel-flow) | Voice input layer (already shipped) |
| [whitelabel-accessibility](https://github.com/whitelabel-dev/whitelabel-accessibility) | Mission home; assistive surface design |
| [whitelabel-deep-learning](https://github.com/whitelabel-dev/whitelabel-deep-learning) | CV + perception models the robot eventually uses |
| [whitelabel-internship](https://github.com/whitelabel-dev/whitelabel-internship) | The program that this enables |
| [whitelabel-principles](https://github.com/whitelabel-dev/whitelabel-principles) | Doctrine — disability-employment non-negotiables |
| [whitelabel-3d](https://github.com/whitelabel-dev/whitelabel-3d) | Three.js front-end (v0.4 browser viewer will live here) |

## attribution

The Unitree G1 and H1 MuJoCo models are from [Google DeepMind's mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie), Apache 2.0 licensed. MuJoCo is from Google DeepMind, Apache 2.0.
