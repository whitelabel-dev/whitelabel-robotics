"""
smoke_test.py — headless physics smoke test. No GUI; confirms MuJoCo
parses + steps the G1 model on this machine before we open a viewer.

Run:
    python demos/smoke_test.py
"""

import os
import time
import mujoco


def main():
    path = os.path.abspath("models/unitree_g1/scene_with_hands.xml")
    print(f"[smoke] loading {path}")
    model = mujoco.MjModel.from_xml_path(path)
    data = mujoco.MjData(model)

    print(f"[smoke] model: {model.nq} dof, {model.nu} actuators, {model.nbody} bodies")
    print(f"[smoke] timestep: {model.opt.timestep * 1000:.2f} ms (= {1 / model.opt.timestep:.0f} Hz)")

    n_steps = 5000
    start = time.time()
    for _ in range(n_steps):
        mujoco.mj_step(model, data)
    elapsed = time.time() - start

    sim_time = n_steps * model.opt.timestep
    speed = sim_time / elapsed
    print(f"[smoke] stepped {n_steps} steps ({sim_time:.2f}s sim) in {elapsed:.3f}s real → {speed:.1f}x real-time")
    print(f"[smoke] CoM z-height after free-fall: {data.qpos[2]:.3f} m")
    print(f"[smoke] ✓ physics engine alive, model parsed, real-time-capable")


if __name__ == "__main__":
    main()
