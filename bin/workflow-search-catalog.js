#!/usr/bin/env node

const { spawnSync } = require("node:child_process");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const script = path.join(root, "scripts", "query_workflow_catalog.py");
const args = process.argv.slice(2);

const candidates = process.env.PYTHON
  ? [[process.env.PYTHON, []]]
  : [
      ["python3", []],
      ["python", []],
      ["py", ["-3"]],
    ];

let lastError = null;

for (const [command, prefixArgs] of candidates) {
  const result = spawnSync(command, [...prefixArgs, script, ...args], {
    stdio: "inherit",
    cwd: root,
  });

  if (result.error && result.error.code === "ENOENT") {
    lastError = result.error;
    continue;
  }

  if (result.error) {
    console.error(`workflow-search-catalog: failed to run ${command}: ${result.error.message}`);
    process.exit(1);
  }

  process.exit(result.status ?? 0);
}

console.error("workflow-search-catalog: Python is required. Install python3 or set PYTHON=/path/to/python.");
if (lastError) {
  console.error(`Last error: ${lastError.message}`);
}
process.exit(1);
