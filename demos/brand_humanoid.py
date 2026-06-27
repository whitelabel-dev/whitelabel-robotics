"""
brand_humanoid.py — render the Unitree G1 humanoid with a CLIENT'S BRAND
colors painted on its body, doing a simple motion, with their brand name
overlaid. Outputs an MP4 video.

The white-label humanoid demo factory:
- Plug in any brand's color palette + name
- Get a 10-second branded robot video back
- Drop into a sales deck, a reseller pitch, a marketing landing page

Run:
    ./.venv/bin/mjpython demos/brand_humanoid.py --brand dreamcase
    ./.venv/bin/mjpython demos/brand_humanoid.py --brand agencycrm
    ./.venv/bin/mjpython demos/brand_humanoid.py --brand officeskylines
    ./.venv/bin/mjpython demos/brand_humanoid.py --brand custom \\
        --primary "#FF6B35" --secondary "#1A1A2E" --name "Acme Robotics"
"""

import argparse
import os

import mujoco
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont


# Brand palette library — hardcoded for v0.1; eventually pull from each
# brand's identity.yaml in whitelabel-brand-<slug> repos.
BRANDS = {
    "dreamcase": {
        "name": "DreamCase",
        "primary": "#6B2FBA",      # deep premium purple
        "secondary": "#F0E6FF",    # soft lavender
        "accent": "#FFB800",       # gold
        "tagline": "Premium Phone Cases",
    },
    "agencycrm": {
        "name": "AgencyCRM",
        "primary": "#0F2B5C",      # deep navy
        "secondary": "#3B82F6",    # electric blue
        "accent": "#FFFFFF",       # white
        "tagline": "Run Your Agency",
    },
    "officeskylines": {
        "name": "Office Skylines",
        "primary": "#3D5A3C",      # sage green
        "secondary": "#E8DDC7",    # warm cream
        "accent": "#A47551",       # earth tan
        "tagline": "Modular Workspaces",
    },
    "shinermarketing": {
        "name": "Shiner Marketing",
        "primary": "#D4AF37",      # rich gold
        "secondary": "#0A0A0A",    # near black
        "accent": "#FFFFFF",       # white
        "tagline": "Marketing That Works",
    },
    "whitelabel": {
        "name": "Whitelabel.dev",
        "primary": "#1D3026",      # deep forest green (from Father's Day menu palette)
        "secondary": "#F5EAD4",    # warm parchment
        "accent": "#B48B3D",       # brass
        "tagline": "Own Your Stack",
    },
}


def hex_to_rgba(hex_color, alpha=1.0):
    """#RRGGBB -> (r, g, b, a) floats in [0,1]."""
    h = hex_color.lstrip("#")
    return (
        int(h[0:2], 16) / 255.0,
        int(h[2:4], 16) / 255.0,
        int(h[4:6], 16) / 255.0,
        alpha,
    )


def hex_to_rgb255(hex_color):
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def build_logo_png(palette, size=320):
    """Generate a square brand logo (PNG, RGBA) we'll composite on the
    robot's chest each frame. v0.1: a rounded-corner brand-color tile
    with the brand initials in big bold. v0.2 will replace this with
    each brand's actual logo file from whitelabel-brand-<slug>."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    primary = hex_to_rgb255(palette["primary"])
    secondary = hex_to_rgb255(palette["secondary"])

    # Rounded-square background
    radius = size // 4
    draw.rounded_rectangle(
        [(8, 8), (size - 8, size - 8)],
        radius=radius,
        fill=primary + (240,),
        outline=secondary + (255,),
        width=6,
    )

    # Brand initials in the center
    initials = "".join(
        w[0].upper() for w in palette["name"].replace(".", " ").split()[:3]
    )[:3]
    try:
        font = ImageFont.truetype(
            "/System/Library/Fonts/Supplemental/Arial Black.ttf",
            int(size * 0.55),
        )
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((size - text_w) // 2 - bbox[0], (size - text_h) // 2 - bbox[1]),
        initials,
        font=font,
        fill=secondary + (255,),
    )
    return img


def world_to_screen(world_xyz, camera, model, width, height):
    """Approximate world → screen projection using MuJoCo's camera params.
    Returns (x, y) in pixel coords, or None if behind the camera."""
    # Get camera view matrix the same way MuJoCo's renderer does.
    # Use mjv_updateCamera + mjv_projection — simpler approximation here:
    # build the camera position from azimuth/elevation/distance/lookat,
    # then project world point into camera space.
    az = np.radians(camera.azimuth)
    el = np.radians(camera.elevation)
    d = camera.distance
    lookat = np.array(camera.lookat)

    # Camera position (matches mjv_updateCamera convention)
    cam_pos = lookat + d * np.array([
        np.cos(el) * np.cos(az),
        np.cos(el) * np.sin(az),
        np.sin(el),
    ])
    forward = lookat - cam_pos
    forward = forward / np.linalg.norm(forward)
    world_up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, world_up)
    right = right / np.linalg.norm(right)
    up = np.cross(right, forward)

    # World → camera-relative
    rel = np.array(world_xyz) - cam_pos
    x_cam = np.dot(rel, right)
    y_cam = np.dot(rel, up)
    z_cam = np.dot(rel, forward)

    if z_cam <= 0:
        return None

    # Perspective projection. MuJoCo's default fovy is 45deg (in scene.xml
    # we accept default). Approximate.
    fovy = np.radians(45.0)
    f = 1.0 / np.tan(fovy / 2.0)
    aspect = width / height
    x_ndc = (x_cam / z_cam) * f / aspect
    y_ndc = (y_cam / z_cam) * f
    # NDC [-1,1] → screen
    px = int((x_ndc + 1.0) * 0.5 * width)
    py = int((1.0 - (y_ndc + 1.0) * 0.5) * height)
    return (px, py, z_cam)


def apply_brand_colors(model, palette):
    """Paint the robot's geoms with the brand colors.

    Strategy: every visual-only geom (those used purely for rendering, not
    collision) gets recolored. Most of the G1's body parts are visual
    geoms; we tint them with the brand primary + secondary alternating by
    body-part index so the robot looks intentionally branded, not blobby.
    """
    primary = hex_to_rgba(palette["primary"])
    secondary = hex_to_rgba(palette["secondary"])
    accent = hex_to_rgba(palette["accent"])

    palette_cycle = [primary, secondary, accent]

    for i in range(model.ngeom):
        # group 1 = visual-only meshes in the G1 model
        if model.geom_group[i] != 1:
            continue
        # Cycle through palette so the robot has visual variety
        body_id = model.geom_bodyid[i]
        color = palette_cycle[body_id % len(palette_cycle)]
        model.geom_rgba[i] = color


def render_branded_video(palette, model_path, output_path, duration_s=8.0, fps=30):
    """Render the branded G1 doing a simple motion, save as MP4."""
    print(f"[brand] loading {model_path}")
    model = mujoco.MjModel.from_xml_path(model_path)
    data = mujoco.MjData(model)

    # === Keep the robot UPRIGHT for a clean brand demo ===
    # No balance controller is loaded yet, so we cheat: zero gravity
    # plus only animate arm joints. The robot stays planted and looks
    # like it's posing gracefully instead of flopping.
    model.opt.gravity[:] = 0.0

    apply_brand_colors(model, palette)

    # Identify arm/hand actuators by joint name — only these get animated.
    # Legs + waist stay still so the robot doesn't drift.
    arm_actuator_ids = []
    for a in range(model.nu):
        # Each actuator targets a joint; get the joint's name
        joint_id = model.actuator_trnid[a, 0]
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_id) or ""
        if any(tag in joint_name.lower() for tag in ("shoulder", "elbow", "wrist", "hand")):
            arm_actuator_ids.append(a)
    print(f"[brand] animating {len(arm_actuator_ids)}/{model.nu} actuators (arms + hands only)")

    # Tint the floor to a soft brand-tone background
    secondary = hex_to_rgba(palette["secondary"], alpha=1.0)
    for i in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i) or ""
        if "floor" in name.lower() or "ground" in name.lower():
            model.geom_rgba[i] = (
                secondary[0] * 0.7,
                secondary[1] * 0.7,
                secondary[2] * 0.7,
                1.0,
            )

    # Set background to brand primary, slightly desaturated
    primary = hex_to_rgba(palette["primary"])

    # MuJoCo's offscreen renderer — 1280x720 for shareable video.
    # The G1 model's default offscreen framebuffer is 640x480; bump it up
    # before creating the renderer.
    width, height = 1280, 720
    model.vis.global_.offwidth = width
    model.vis.global_.offheight = height
    renderer = mujoco.Renderer(model, height=height, width=width)

    # Camera: slow orbit around the robot at torso height
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat = np.array([0.0, 0.0, 0.7])
    camera.distance = 4.5
    camera.elevation = -10.0

    n_frames = int(duration_s * fps)
    sim_steps_per_frame = int(round(1.0 / fps / model.opt.timestep))
    print(f"[brand] rendering {n_frames} frames @ {fps}fps = {duration_s}s")
    print(f"[brand]   {sim_steps_per_frame} sim steps per frame")

    # Pre-render the brand logo PNG once; composite onto the chest each frame
    logo_img = build_logo_png(palette, size=400)

    # Find the chest/torso body so we can project its world position to
    # the screen each frame and stick the logo on it.
    chest_body_id = None
    for candidate in ("torso_link", "pelvis", "waist_yaw_link", "torso"):
        cid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, candidate)
        if cid != -1:
            chest_body_id = cid
            print(f"[brand] tracking body for logo: {candidate}")
            break
    if chest_body_id is None:
        # Fallback: just put the logo at fixed screen center-ish
        print(f"[brand] no chest body found; logo will be at fixed screen position")

    # Try to load a font for the brand overlay
    try:
        font_path = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
        font_name = ImageFont.truetype(font_path, 56)
        font_tag = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
    except OSError:
        font_name = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    frames = []
    for f in range(n_frames):
        # Orbit camera slowly: ~30 degrees per second of azimuth
        camera.azimuth = 135.0 + (f / fps) * 30.0

        # Only animate arm joints, with gentle amplitude so the robot
        # poses like it's "presenting itself" rather than flailing.
        t = f / fps
        for idx, a in enumerate(arm_actuator_ids):
            phase = (idx / max(1, len(arm_actuator_ids))) * 2 * np.pi
            data.ctrl[a] = 0.25 * np.sin(2 * np.pi * 0.3 * t + phase)

        # Step physics
        for _ in range(sim_steps_per_frame):
            mujoco.mj_step(model, data)

        # Render this frame
        renderer.update_scene(data, camera=camera)
        pixels = renderer.render()  # numpy (H, W, 3) uint8

        # Overlay brand name + tagline + logo-on-chest
        img = Image.fromarray(pixels).convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        # ── Logo on chest (follows the robot in world space) ──
        if chest_body_id is not None:
            chest_pos = data.xpos[chest_body_id].copy()
            # Nudge the projected logo slightly upward to land on the upper
            # torso instead of the belly
            chest_pos[2] += 0.1
            proj = world_to_screen(chest_pos, camera, model, width, height)
            if proj is not None:
                sx, sy, depth = proj
                # Logo size scales with distance — closer = bigger
                logo_pixel_size = int(max(60, min(180, 900 / max(depth, 0.5))))
                logo_resized = logo_img.resize(
                    (logo_pixel_size, logo_pixel_size), Image.LANCZOS
                )
                paste_xy = (sx - logo_pixel_size // 2, sy - logo_pixel_size // 2)
                img.paste(logo_resized, paste_xy, logo_resized)

        # Subtle dark gradient at bottom for text legibility
        for y in range(height - 160, height):
            alpha = int(180 * (y - (height - 160)) / 160)
            draw.rectangle([(0, y), (width, y + 1)], fill=(0, 0, 0, alpha))

        # Brand primary as a thin top accent stripe
        accent_rgba = tuple(int(c * 255) for c in primary[:3]) + (255,)
        draw.rectangle([(0, 0), (width, 6)], fill=accent_rgba)

        # Name + tagline
        draw.text((40, height - 130), palette["name"], font=font_name, fill="#FFFFFF")
        draw.text((40, height - 60), palette["tagline"], font=font_tag, fill="#DDDDDD")

        # Whitelabel.dev watermark, bottom-right
        draw.text(
            (width - 200, height - 40),
            "made by whitelabel.dev",
            font=font_tag,
            fill="#888888",
        )

        frames.append(np.array(img.convert("RGB")))

        if f % 30 == 0:
            print(f"[brand]   frame {f}/{n_frames}")

    print(f"[brand] writing {output_path}")
    imageio.mimsave(output_path, frames, fps=fps, codec="libx264", quality=8)
    print(f"[brand] ✓ done")
    return output_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--brand", default="whitelabel", help=f"one of: {','.join(BRANDS.keys())} or 'custom'")
    p.add_argument("--primary", help="custom primary color #RRGGBB (only if --brand custom)")
    p.add_argument("--secondary", help="custom secondary color")
    p.add_argument("--accent", help="custom accent color")
    p.add_argument("--name", help="custom brand name (only if --brand custom)")
    p.add_argument("--tagline", default="", help="custom tagline")
    p.add_argument("--model", default="models/unitree_g1/scene_with_hands.xml")
    p.add_argument("--output", help="output mp4 path (default: output/<brand>.mp4)")
    p.add_argument("--duration", type=float, default=8.0, help="seconds of footage")
    p.add_argument("--fps", type=int, default=30)
    args = p.parse_args()

    if args.brand == "custom":
        if not (args.primary and args.name):
            raise SystemExit("--brand custom requires --primary and --name")
        palette = {
            "name": args.name,
            "primary": args.primary,
            "secondary": args.secondary or "#FFFFFF",
            "accent": args.accent or "#000000",
            "tagline": args.tagline,
        }
    else:
        if args.brand not in BRANDS:
            raise SystemExit(f"unknown brand {args.brand}; known: {','.join(BRANDS)}")
        palette = BRANDS[args.brand]

    os.makedirs("output", exist_ok=True)
    output = args.output or f"output/{args.brand}.mp4"
    render_branded_video(palette, args.model, output, args.duration, args.fps)


if __name__ == "__main__":
    main()
