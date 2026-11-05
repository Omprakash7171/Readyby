/**
 * Start the whole local app with one command.
 *
 * Before this existed, `npm run dev` started only Next.js. The landing page
 * rendered fine (it is static), so a fresh checkout looked healthy while every
 * API call - sign up, sign in, load the cafe list - failed, because the Django
 * API was never running. This script starts both and labels their output.
 *
 * No dependencies: uses only Node's standard library.
 */

import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const backendDir = path.join(root, "backend");

const API_PORT = Number(process.env.PORT ?? 8000);
const WEB_PORT = Number(process.env.WEB_PORT ?? 3000);

const API_BASE = `http://127.0.0.1:${API_PORT}`;
const COLORS = { api: "[36m", web: "[35m", dim: "[90m", red: "[31m", reset: "[0m" };

function prefixStream(stream, label, color) {
  let buffer = "";
  stream.setEncoding("utf8");
  stream.on("data", (chunk) => {
    buffer += chunk;
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      process.stdout.write(`${color}[${label}]${COLORS.reset} ${line}\n`);
    }
  });
}

function portInUse(port) {
  return new Promise((resolve) => {
    const socket = net.connect({ port, host: "127.0.0.1" });
    const done = (inUse) => {
      socket.destroy();
      resolve(inUse);
    };
    socket.setTimeout(1000);
    socket.once("connect", () => done(true));
    socket.once("timeout", () => done(false));
    socket.once("error", () => done(false));
  });
}

/** Wait until the API answers, so we can tell the user when sign-in will work. */
async function apiResponds(timeoutMs = 2500) {
  try {
    const response = await fetch(`${API_BASE}/api/cafes/`, {
      signal: AbortSignal.timeout(timeoutMs),
    });
    return response.ok;
  } catch {
    return false;
  }
}

async function waitForApi(timeoutMs = 60000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await apiResponds()) return true;
    await new Promise((r) => setTimeout(r, 700));
  }
  return false;
}

function run(label, color, command, args, cwd) {
  let child;
  try {
    child = spawn(command, args, {
      cwd,
      shell: false,
      windowsHide: true,
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    });
  } catch (error) {
    // spawn can fail synchronously (bad path, .cmd without a shell). Report it
    // for this service only - a dead API must not take the frontend down too.
    process.stdout.write(
      `${COLORS.red}[${label}] failed to start: ${error.message}${COLORS.reset}\n`,
    );
    return null;
  }
  prefixStream(child.stdout, label, color);
  prefixStream(child.stderr, label, color);
  child.on("error", (error) => {
    process.stdout.write(
      `${COLORS.red}[${label}] failed to start: ${error.message}${COLORS.reset}\n`,
    );
  });
  return child;
}

function pythonExecutable() {
  return process.platform === "win32"
    ? path.join(backendDir, ".venv", "Scripts", "python.exe")
    : path.join(backendDir, ".venv", "bin", "python");
}

const children = [];
let shuttingDown = false;

function shutdown(code) {
  if (shuttingDown) return;
  shuttingDown = true;
  for (const child of children) {
    if (child && child.exitCode === null && !child.killed) child.kill();
  }
  process.exit(code);
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

async function main() {
  const out = (line) => process.stdout.write(`${line}\n`);

  // Refuse up front with a clear instruction. Letting "next dev" discover this
  // itself produces an EADDRINUSE stack trace with no hint that another dev
  // server (very often one you started minutes ago) already owns the port.
  if (await portInUse(WEB_PORT)) {
    out(
      `${COLORS.red}Port ${WEB_PORT} is already in use, so the frontend can't start.${COLORS.reset}\n` +
        `${COLORS.dim}Something else is serving there - most likely a previous "npm run dev" you forgot about.\n` +
        `Close it (or run: npx kill-port ${WEB_PORT}), then try again.${COLORS.reset}`,
    );
    shutdown(1);
    return;
  }

  const python = pythonExecutable();
  if (!(await import("node:fs")).existsSync(python)) {
    out(
      `${COLORS.red}No virtualenv found at ${python}${COLORS.reset}\n` +
        `Create it first:  cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt`,
    );
    shutdown(1);
    return;
  }

  // Decide using the API's own health, not just whether the port is bound.
  // Checking the port alone is a trap: a server that is still shutting down
  // holds the port for a moment, so we would decide "the API is already
  // running", skip starting it, and then that process would exit and leave
  // nothing listening. The frontend would come up perfectly and every API
  // call would fail with no process to blame.
  if (await apiResponds()) {
    out(`${COLORS.dim}The API is already answering on ${API_BASE}.${COLORS.reset}`);
  } else {
    if (await portInUse(API_PORT)) {
      out(
        `${COLORS.red}Port ${API_PORT} is held by a process that isn't answering.${COLORS.reset}\n` +
          `${COLORS.dim}Starting the API anyway; if it can't bind, close the other process with:\n` +
          `  npx kill-port ${API_PORT}${COLORS.reset}`,
      );
    }
    out(`${COLORS.dim}Starting Django API on ${API_BASE} ...${COLORS.reset}`);
    children.push(
      run("api", COLORS.api, python, ["manage.py", "runserver", `127.0.0.1:${API_PORT}`], backendDir),
    );
  }

  out(`${COLORS.dim}Starting Next.js on http://localhost:${WEB_PORT} ...${COLORS.reset}`);
  // Spawn node against Next's own entry point rather than "npx next dev".
  // On Windows the "next" launcher is a .cmd, and Node refuses to spawn a .cmd
  // without a shell (spawn EINVAL), which a shell would only paper over with
  // fragile quoting rules.
  children.push(
    run(
      "web",
      COLORS.web,
      process.execPath,
      [path.join(root, "node_modules", "next", "dist", "bin", "next"), "dev", "--port", String(WEB_PORT)],
      root,
    ),
  );

  const ready = await waitForApi();
  out("");
  if (ready) {
    out(`${COLORS.api}API is answering.${COLORS.reset} Sign up and sign in will work.`);
    out(`  app   http://localhost:${WEB_PORT}`);
    out(`  api   ${API_BASE}/api/`);
    out(`  admin ${API_BASE}/admin/`);
    out("");
    out(`${COLORS.dim}Demo logins: customer@readyby.demo / merchant@readyby.demo (readyby-demo-2026)${COLORS.reset}`);
  } else {
    out(
      `${COLORS.red}The API did not start within 60s. Sign up and sign in will fail.${COLORS.reset}\n` +
        `${COLORS.dim}Check the [api] lines above, then try: cd backend && .venv/Scripts/python manage.py migrate${COLORS.reset}`,
    );
  }
  out("");
}

main();
