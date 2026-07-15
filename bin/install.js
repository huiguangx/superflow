#!/usr/bin/env node

const fs = require("fs");
const os = require("os");
const path = require("path");

const root = path.resolve(__dirname, "..");
const source = path.join(root, "skills");
const target = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(os.homedir(), ".agents", "skills");

if (!fs.existsSync(source)) {
  console.error(`Superflow skills folder not found: ${source}`);
  process.exit(1);
}

fs.mkdirSync(target, { recursive: true });

for (const name of fs.readdirSync(source)) {
  const from = path.join(source, name);
  const to = path.join(target, name);
  if (!fs.statSync(from).isDirectory()) continue;
  if (fs.existsSync(to)) {
    console.log(`skip ${name}: already exists at ${to}`);
    continue;
  }
  fs.cpSync(from, to, { recursive: true });
  console.log(`installed ${name} -> ${to}`);
}

console.log(`\nDone. Start a new Codex session to load Superflow from ${target}`);
