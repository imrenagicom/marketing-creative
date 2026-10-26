#!/usr/bin/env python3
"""Check this repository's multi-client packaging invariants (stdlib only)."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "marketing-creative"
MANIFESTS = (".codex-plugin/plugin.json", ".claude-plugin/plugin.json", "plugin.json")
ANTIGRAVITY_FIELDS = {
    "$schema", "name", "displayName", "version",
    "description", "logo", "suggestedPrompts", "disabled",
}
PLUGINS_CONFIG = ".agents/plugins.json"
PLUGINS = {
    "marketing-creative": {"marketing-video", "creative-ideation", "ad-video-director",
        "motion-video-producer", "motion-art-director", "motion-storyboard",
        "motion-voice", "motion-composer", "motion-video-qa",
        "marketing-image-board", "marketing-image-producer", "marketing-veo-video",
        "marketing-omni-video"},
    "marketing-performance": {"marketing-brief", "campaign-manager",
        "marketing-copywriter", "google-analytics-analyst"},
    "video-studio": {"studio-producer", "director", "scriptwriter", "voice-director", "shot-designer"},
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def package_files(plugin=None):
    """An explicit surface allowlist; never archive the repository root."""
    plugin = PLUGIN if plugin is None else plugin
    files = [plugin / path for path in MANIFESTS]
    require(not plugin.is_symlink() and not (plugin / "skills").is_symlink(),
            "Plugin and skill roots must not be symlinks")
    for kind in (".codex-plugin", ".claude-plugin"):
        require(not (plugin / kind).is_symlink(), f"Symlinked package ancestor: {plugin / kind}")
    for path in sorted((plugin / "skills").rglob("*")):
        require(not path.is_symlink(), f"Symlink is not a distributable asset: {path}")
        if "__pycache__" in path.parts:
            continue
        if path.is_file():
            relative = path.relative_to(plugin / "skills")
            allowed = (len(relative.parts) == 2 and relative.name == "SKILL.md") or (
                len(relative.parts) >= 3 and relative.parts[1] in {
                    "agents", "references", "scripts", "assets"
                } and path.suffix in {
                    "agents": {".yaml"}, "references": {".md"},
                    "scripts": {".py", ".mjs"}, "assets": {".json", ".svg", ".html"}
                }[relative.parts[1]])
            allowed = allowed or (relative.parts[1:] == ("scripts", "requirements.txt")
                                  and relative.parts[0] == "marketing-image-producer")
            require(allowed, f"Unexpected skill asset: {path}")
            files.append(path)
    notices = plugin / "third-party"
    require(not notices.is_symlink(), "Third-party root must not be a symlink")
    expected_notices = ({"bang-motion.LICENSE", "hyperframe-pro.LICENSE"}
                        if plugin.name == "marketing-creative" else set())
    require(({p.name for p in notices.iterdir()} if notices.exists() else set()) == expected_notices,
            "Unexpected or missing third-party notices")
    files.extend(notices / name for name in sorted(expected_notices))
    for path in files:
        require(path.is_file() and not path.is_symlink(), f"Missing/unsafe package file: {path}")
        require(path.resolve().is_relative_to(plugin.resolve()), f"Package file escapes plugin: {path}")
        require(not any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(plugin)),
                f"Symlinked package ancestor: {path}")
    return files


def validate_plugin(plugin):
    codex, claude, antigravity = [read_json(plugin / path) for path in MANIFESTS]
    for key in ("name", "version", "description"):
        require(codex.get(key) == claude.get(key) == antigravity.get(key) and bool(codex.get(key)),
                f"Client manifests disagree or omit {key}")
    for key in ("author", "homepage", "repository"):
        require(codex.get(key) == claude.get(key) and bool(codex.get(key)),
                f"Codex and Claude manifests disagree or omit {key}")
    require(codex["name"] == plugin.name, "Unexpected plugin identity")
    require(re.fullmatch(r"\d+\.\d+\.\d+", codex["version"]), "Invalid release version")
    require(antigravity.get("$schema") == "https://antigravity.google/schemas/v1/plugin.json",
            "Antigravity manifest must declare the v1 plugin schema")
    require(set(antigravity).issubset(ANTIGRAVITY_FIELDS),
            "Unsupported top-level fields in Antigravity manifest")
    require(codex.get("skills") == "./skills/", "Codex skill path changed")
    interface = codex.get("interface", {})
    require(interface.get("displayName"), "Missing Codex display name")
    require(interface.get("shortDescription"), "Missing Codex description")
    require(interface.get("longDescription"), "Missing Codex longDescription")
    require(interface.get("developerName"), "Missing Codex developerName")
    require(interface.get("category"), "Missing Codex category")
    require(interface.get("capabilities"), "Missing Codex capabilities")
    require(antigravity.get("displayName") == interface.get("displayName"),
            "Antigravity displayName must match Codex")
    prompts = antigravity.get("suggestedPrompts")
    require(isinstance(prompts, list) and 1 <= len(prompts) <= 3
            and all(isinstance(p, str) and p.strip() for p in prompts),
            "Antigravity suggestedPrompts must contain 1 to 3 non-empty strings")
    require(prompts == interface.get("defaultPrompt"),
            "Antigravity suggestedPrompts must match Codex defaultPrompt")
    require(codex["author"].get("name"), "Missing publisher")

    plugins_config = read_json(ROOT / PLUGINS_CONFIG)
    require(plugins_config == {"entries": [{"path": "plugins"}]},
            "Workspace plugins.json must point to ./plugins")
    require(not (ROOT / ".agents/skills.json").exists(),
            "Do not combine .agents/skills.json with .agents/plugins.json; it duplicates plugin skills")

    marketplaces = [read_json(ROOT / p) for p in
                    (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json")]
    for market in marketplaces:
        require(market["name"] == "marketing-creative", "Unexpected marketplace identity")
        require({e["name"] for e in market["plugins"]} == set(PLUGINS)
                and len(market["plugins"]) == len(PLUGINS), "Marketplace plugin inventory mismatch")
        entry = next(e for e in market["plugins"] if e["name"] == plugin.name)
        require(entry["name"] == codex["name"], "Marketplace/plugin identity mismatch")
        source = entry["source"]
        if isinstance(source, dict):
            require(source.get("source") == "local", "Expected local Codex source")
            source = source["path"]
        require(source == f"./plugins/{plugin.name}", "Unexpected plugin source path")
        require((ROOT / source).resolve() == plugin, "Source must resolve from repository root")

    skills = sorted((plugin / "skills").glob("*/SKILL.md"))
    expected_skills = PLUGINS[plugin.name]
    require({s.parent.name for s in skills} == expected_skills, "Missing/unexpected suite skills")
    for skill in skills:
        text = skill.read_text(encoding="utf-8")
        require(text.startswith("---\n"), f"Missing frontmatter: {skill}")
        frontmatter = text.split("---", 2)[1]
        name = re.search(r"^name: ([a-z0-9-]+)$", frontmatter, re.M)
        require(name and name[1] == skill.parent.name, f"Skill name/path mismatch: {skill}")
        require(re.search(r"^description: \S.+$", frontmatter, re.M), f"Missing description: {skill}")
        require(not re.search(r"\bTODO\b|\[TBD\]", text), f"Unfinished scaffold: {skill}")
        ui = (skill.parent / "agents/openai.yaml").read_text(encoding="utf-8")
        require(f"${name[1]}" in ui, f"UI prompt does not invoke skill: {skill}")
        if name[1] in {"marketing-veo-video","marketing-omni-video"}:
            require(re.search(r"^\s+allow_implicit_invocation: false$",ui,re.M),
                    f"Paid video generation must remain opt-in: {skill}")

    files = package_files(plugin)
    for path in files:
        relative = path.relative_to(plugin)
        require(not any(p in {"samples", "local-docs", "__pycache__"} for p in relative.parts),
                f"Private/generated material in package: {path}")
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            require("/Users/" not in text, f"Non-portable private path in package: {path}")
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                resolved = (path.parent / target.split("#", 1)[0]).resolve()
                require(resolved.is_relative_to(plugin) and resolved.exists(),
                        f"Broken or escaping resource link: {path}: {target}")
        if path.suffix == ".json":
            read_json(path)
    return files


def validate(plugin_name=None):
    """Validate every plugin, or select one archive's independently usable tree."""
    names = [plugin_name] if plugin_name else PLUGINS
    files = []
    for name in names:
        require(name in PLUGINS, f"Unknown plugin: {name}")
        files.extend(validate_plugin(ROOT / "plugins" / name))
    versions = {
        read_json(ROOT / "plugins" / name / manifest)["version"]
        for name in PLUGINS
        for manifest in MANIFESTS
    }
    if (ROOT / "package.json").is_file():
        versions.add(read_json(ROOT / "package.json")["version"])
    if (ROOT / "package-lock.json").is_file():
        lock = read_json(ROOT / "package-lock.json")
        versions.add(lock["version"])
        versions.add(lock.get("packages", {}).get("", {}).get("version"))
    require(len(versions) == 1, "Plugins and release metadata must share the repository release version")
    return files


if __name__ == "__main__":
    files = validate()
    print(f"Validated all plugins, resources and marketplaces: {len(files)} package files")
