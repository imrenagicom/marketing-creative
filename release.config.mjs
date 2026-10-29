import { join } from "node:path";
import { tmpdir } from "node:os";

export const archiveDir = process.env.RUNNER_TEMP || tmpdir();

export const imagesArchivePath = join(archiveDir, "marketing-images-plugin.zip");

export const performanceArchivePath = join(archiveDir, "marketing-performance-plugin.zip");

export const videoStudioArchivePath = join(archiveDir, "video-studio-plugin.zip");

export default {
  branches: ["main"],
  repositoryUrl: "https://github.com/imrenagicom/marketing-creative.git",
  tagFormat: "v${version}",
  plugins: [
    ["@semantic-release/commit-analyzer", {
      preset: "conventionalcommits",
      releaseRules: [
        { breaking: true, release: "major" },
        { type: "feat", release: "minor" },
        { release: "patch" },
      ],
    }],
    ["@semantic-release/release-notes-generator", {
      preset: "conventionalcommits",
      presetConfig: {
        types: [
          { type: "feat", section: "Features" },
          { type: "fix", section: "Fixes" },
          { type: "perf", section: "Performance" },
          { type: "docs", section: "Skills and documentation" },
          { type: "refactor", section: "Refactoring" },
          { type: "test", section: "Tests" },
          { type: "build", section: "Build" },
          { type: "ci", section: "Automation" },
          { type: "chore", section: "Maintenance" },
          { type: "style", section: "Formatting" },
          { type: "revert", section: "Reverts" },
        ],
      },
    }],
    "@semantic-release/changelog",
    "./scripts/release-plugin.mjs",
    ["@semantic-release/git", {
      assets: [
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
      ],
      message: "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}",
    }],
    ["@semantic-release/github", {
      assets: [
        { path: imagesArchivePath, label: "Marketing Images complete skill plugin" },
        { path: performanceArchivePath, label: "Marketing Performance complete skill plugin" },
        { path: videoStudioArchivePath, label: "Video Studio complete skill plugin" },
      ],
      successComment: false,
      failComment: false,
      failTitle: false,
      releasedLabels: false,
    }],
  ],
};
