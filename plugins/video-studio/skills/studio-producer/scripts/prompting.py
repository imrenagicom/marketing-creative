"""Shared prompt pieces for image and video requests built from the continuity bible (stdlib only).

Element support was read from the Higgsfield MCP `manage_reference_elements`
tool description on 2026-10-27; re-check it (and `models_explore`) when models
change. Models outside this list get reference images as media instead.
"""

ELEMENT_MODELS = {
    "nano_banana_pro", "nano_banana_2", "gpt_image_2", "seedream_v4_5", "seedream_v5_lite", "cinematic_studio_2_5",
    "cinematic_studio_video_v2", "cinematic_studio_3_0", "seedance_2_0", "kling3_0",
}
ASPECT = {"16x9": "16:9", "9x16": "9:16", "4x5": "4:5", "1x1": "1:1"}


def refs_for(shot, bible):
    by_id = {ref["id"]: ref for ref in bible["references"]}
    return [by_id[ref] for ref in shot.get("refs", []) if ref in by_id]


def subject(ref, model):
    """How a reference is named in a prompt: an element placeholder when the model supports it."""
    if ref.get("higgsfield_element_id") and model in ELEMENT_MODELS:
        return f"<<<{ref['higgsfield_element_id']}>>> ({ref['name']})"
    return f"{ref['name']} ({'; '.join(ref['preserve'])})"


def media_refs(refs, model):
    """Reference images to attach when the model cannot use element placeholders.

    Roles are model-specific; `image` is a placeholder the agent must map to the
    selected model's declared media roles before submission.
    """
    if model in ELEMENT_MODELS:
        return []
    return [{"role": "image", "ref": ref["id"], "asset": ref["images"][0]} for ref in refs if ref.get("images")]


def environment(refs):
    env = next((ref for ref in refs if ref["role"] == "environment"), None)
    if not env:
        return None, []
    return env, env.get("light_sources", [])
