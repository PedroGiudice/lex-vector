import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const serverPath = join(__dirname, "server.py");

const child = spawn("python3", ["-u", serverPath], {
  stdio: ["pipe", "pipe", "inherit"],
  env: { ...process.env, PYTHONUNBUFFERED: "1" },
});

process.stdin.pipe(child.stdin);
child.stdout.pipe(process.stdout);

process.on("SIGTERM", () => child.kill("SIGTERM"));
process.on("SIGINT", () => child.kill("SIGINT"));
child.on("exit", (code) => process.exit(code ?? 0));
