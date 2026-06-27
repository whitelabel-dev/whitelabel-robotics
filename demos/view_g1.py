"""
view_g1.py — open an interactive 3D viewer with the Unitree G1 humanoid.

Run:
    source .venv/bin/activate
    python demos/view_g1.py

What you'll see:
- A 3D window with the G1 humanoid standing on a floor
- Drag to orbit the camera; scroll to zoom; right-drag to pan
- The sim runs in real time; the robot will fall over because no
  control policy is loaded yet (that's v0.2)

Why this is the first demo:
This is the "is the simulator alive on this hardware?" check. Loading
a 28-DOF humanoid in real-time physics on a base M4 Mac mini is a
non-trivial smoke test of the whole stack — physics engine, model
parsing, MuJoCo viewer GUI, GPU/CPU pipeline. If this works, the rest
of the demo work (voice control, learned policies, browser streaming)
is layering, not foundation work.
"""

import argparse
import os
import time

import mujoco
import mujoco.viewer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="models/unitree_g1/scene_with_hands.xml",
        help="Path to the MJCF scene XML",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Auto-close after N seconds (0 = run until window closed)",
    )
    args = parser.parse_args()

    model_path = os.path.abspath(args.model)
    if not os.path.exists(model_path):
        raise SystemExit(f"model not found: {model_path}")

    print(f"[wl-robotics] loading {os.path.basename(model_path)}")
    model = mujoco.MjModel.from_xml_path(model_path)
    data = mujoco.MjData(model)

    print(f"[wl-robotics] dof:      {model.nq}")
    print(f"[wl-robotics] actuators: {model.nu}")
    print(f"[wl-robotics] bodies:   {model.nbody}")
    print(f"[wl-robotics] launching viewer — drag to orbit, scroll to zoom")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        start = time.time()
        while viewer.is_running():
            step_start = time.time()
            mujoco.mj_step(model, data)
            viewer.sync()
            # Sleep to keep real-time pace (default 500 Hz sim → 2 ms per step)
            time_until_next_step = model.opt.timestep - (time.time() - step_start)
            if time_until_next_step > 0:
                time.sleep(time_until_next_step)
            if args.duration > 0 and (time.time() - start) > args.duration:
                break

    print("[wl-robotics] viewer closed")


if __name__ == "__main__":
    main()
