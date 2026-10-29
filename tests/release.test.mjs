import assert from "node:assert/strict";
import { test } from "node:test";
import { analyzeCommits } from "@semantic-release/commit-analyzer";
import { generateNotes } from "@semantic-release/release-notes-generator";
import config from "../release.config.mjs";

const options = config.plugins[0][1];
const logger = { log() {} };

for (const [message, expected] of [
  ["feat(skills): add a skill", "minor"],
  ["fix(images): preserve alpha", "patch"],
  ["docs(skills): clarify the handoff", "patch"],
  ["ci: update the runner", "patch"],
  ["Update a skill reference", "patch"],
  ["feat: change the contract\n\nBREAKING CHANGE: remove the old field", "major"],
  ["feat!: replace the project contract", "major"],
]) {
  test(`${message.split("\n")[0]} produces ${expected}`, async () => {
    assert.equal(await analyzeCommits(options, {
      cwd: process.cwd(), commits: [{ message }], logger,
    }), expected);
  });
}

test("a rerun with no new commits does not create a release", async () => {
  assert.equal(await analyzeCommits(options, {
    cwd: process.cwd(), commits: [], logger,
  }), null);
});

test("a mixed push uses the highest required bump", async () => {
  assert.equal(await analyzeCommits(options, {
    cwd: process.cwd(),
    commits: [
      { message: "docs: update skill guidance" },
      { message: "feat: add a skill" },
    ],
    logger,
  }), "minor");
});

test("release notes include skill documentation changes", async () => {
  const notes = await generateNotes(config.plugins[1][1], {
    cwd: process.cwd(),
    options: { repositoryUrl: config.repositoryUrl },
    commits: [{ message: "docs(skills): clarify asset handoff", hash: "a".repeat(40) }],
    lastRelease: { gitTag: "v0.1.0" },
    nextRelease: { version: "0.1.1", gitTag: "v0.1.1" },
    logger,
  });
  assert.match(notes, /Skills and documentation/);
  assert.match(notes, /clarify asset handoff/);
});

test("git release commit stages changelog, package metadata, and Claude/Codex/Antigravity manifests", () => {
  const gitPlugin = config.plugins.find(
    (entry) => Array.isArray(entry) && entry[0] === "@semantic-release/git",
  );
  assert.ok(gitPlugin, "Expected @semantic-release/git plugin");
  assert.deepEqual(gitPlugin[1].assets, [
    "CHANGELOG.md",
    "package.json",
    "package-lock.json",
    "plugins/marketing-images/.codex-plugin/plugin.json",
    "plugins/marketing-images/.claude-plugin/plugin.json",
    "plugins/marketing-images/plugin.json",
    "plugins/marketing-performance/.codex-plugin/plugin.json",
    "plugins/marketing-performance/.claude-plugin/plugin.json",
    "plugins/marketing-performance/plugin.json",
    "plugins/video-studio/.codex-plugin/plugin.json",
    "plugins/video-studio/.claude-plugin/plugin.json",
    "plugins/video-studio/plugin.json",
  ]);
});
