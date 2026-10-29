import { execFileSync } from "node:child_process";
import { archiveDir } from "../release.config.mjs";

export function prepare(_config, { cwd, nextRelease }) {
  execFileSync("python3", [
    "scripts/prepare_release.py", nextRelease.version, "--output-dir", archiveDir,
  ], { cwd, stdio: "inherit" });
}
