/**
 * Vercel build: copy landing/ to dist/ so the site deploys when
 * the project root is the repo root (Root Directory not set to landing).
 */
import { cpSync, existsSync, mkdirSync, rmSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "landing");
const dest = join(root, "dist");

if (!existsSync(src)) {
  console.error("Missing landing/ directory");
  process.exit(1);
}

if (existsSync(dest)) {
  rmSync(dest, { recursive: true, force: true });
}

mkdirSync(dest, { recursive: true });
cpSync(src, dest, { recursive: true });

// Never deploy local overrides or env files (even if present on disk).
for (const rel of ["assets/config.local.js", ".env", ".env.local"]) {
  const p = join(dest, rel);
  if (existsSync(p)) {
    rmSync(p, { force: true });
    console.warn("Removed", rel, "from dist (must not be public)");
  }
}

console.log("Copied landing/ → dist/ for Vercel deploy");
