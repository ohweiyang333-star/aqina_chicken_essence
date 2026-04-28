import { spawn, spawnSync } from "node:child_process";
import { platform } from "node:process";

const quietTimeoutMs = secondsFromEnv("NEXT_BUILD_QUIET_TIMEOUT_SECONDS", 180);
const totalTimeoutMs = secondsFromEnv("NEXT_BUILD_TOTAL_TIMEOUT_SECONDS", 600);
const nextArgs = ["build", ...process.argv.slice(2)];
const isWindows = platform === "win32";

let timedOut = false;
let lastOutputAt = Date.now();
const startedAt = Date.now();

const child = spawn("./node_modules/.bin/next", nextArgs, {
  cwd: process.cwd(),
  detached: !isWindows,
  env: {
    ...process.env,
    NEXT_TELEMETRY_DISABLED: process.env.NEXT_TELEMETRY_DISABLED ?? "1",
  },
  stdio: ["ignore", "pipe", "pipe"],
});

child.stdout.on("data", (chunk) => {
  lastOutputAt = Date.now();
  process.stdout.write(chunk);
});

child.stderr.on("data", (chunk) => {
  lastOutputAt = Date.now();
  process.stderr.write(chunk);
});

child.on("error", (error) => {
  console.error(`[build-wrapper] Failed to start next build: ${error.message}`);
  process.exit(1);
});

const quietTimer = setInterval(() => {
  const quietForMs = Date.now() - lastOutputAt;
  if (quietForMs >= quietTimeoutMs) {
    failBuild(`no output for ${formatSeconds(quietForMs)}`);
  }
}, 1000);

const totalTimer = setTimeout(() => {
  failBuild(`total runtime exceeded ${formatSeconds(totalTimeoutMs)}`);
}, totalTimeoutMs);

child.on("exit", (code, signal) => {
  clearInterval(quietTimer);
  clearTimeout(totalTimer);

  if (timedOut) {
    process.exit(124);
  }

  if (signal) {
    console.error(`[build-wrapper] next build exited with signal ${signal}.`);
    process.exit(1);
  }

  process.exit(code ?? 1);
});

function failBuild(reason) {
  if (timedOut) {
    return;
  }

  timedOut = true;
  const elapsedMs = Date.now() - startedAt;
  const quietForMs = Date.now() - lastOutputAt;

  console.error("");
  console.error("[build-wrapper] Next/PostCSS build timeout.");
  console.error(`[build-wrapper] Reason: ${reason}.`);
  console.error(`[build-wrapper] Elapsed: ${formatSeconds(elapsedMs)}.`);
  console.error(`[build-wrapper] Quiet: ${formatSeconds(quietForMs)}.`);
  console.error("[build-wrapper] Last visible Next.js phase is usually the failing boundary. If it stops at 'Creating an optimized production build ...', inspect PostCSS/Tailwind and stale build artifacts.");

  printProcessSnapshot();
  stopChild();
}

function stopChild() {
  if (child.exitCode !== null || child.signalCode !== null) {
    return;
  }

  const targetPid = isWindows ? child.pid : -child.pid;
  try {
    process.kill(targetPid, "SIGTERM");
  } catch {
    return;
  }

  setTimeout(() => {
    if (child.exitCode !== null || child.signalCode !== null) {
      return;
    }

    try {
      process.kill(targetPid, "SIGKILL");
    } catch {
      // Process already exited.
    }
  }, 5000).unref();
}

function printProcessSnapshot() {
  if (isWindows) {
    return;
  }

  const ps = spawnSync("ps", ["-axo", "pid,ppid,stat,pcpu,pmem,etime,command"], {
    encoding: "utf8",
  });

  const interestingLines = (ps.stdout ?? "")
    .split("\n")
    .filter((line) => /next build|postcss\.js|tailwind|node_modules\/next/.test(line));

  if (interestingLines.length > 0) {
    console.error("[build-wrapper] Related process snapshot:");
    for (const line of interestingLines) {
      console.error(line);
    }
  }
}

function secondsFromEnv(name, fallbackSeconds) {
  const raw = process.env[name];
  if (!raw) {
    return fallbackSeconds * 1000;
  }

  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    console.warn(`[build-wrapper] Ignoring invalid ${name}=${raw}; using ${fallbackSeconds}s.`);
    return fallbackSeconds * 1000;
  }

  return parsed * 1000;
}

function formatSeconds(milliseconds) {
  return `${Math.round(milliseconds / 1000)}s`;
}
