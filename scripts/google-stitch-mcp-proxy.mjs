import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { StitchProxy } from "@google/stitch-sdk";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

function parseDotEnvLine(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) return null;

  const separatorIndex = trimmed.indexOf("=");
  if (separatorIndex <= 0) return null;

  const key = trimmed.slice(0, separatorIndex).trim();
  let value = trimmed.slice(separatorIndex + 1).trim();

  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    value = value.slice(1, -1);
  }

  // Preserve escaped newlines in quoted values.
  value = value.replace(/\\n/g, "\n");

  return { key, value };
}

function loadDotEnv(fileName) {
  const filePath = resolve(process.cwd(), fileName);
  if (!existsSync(filePath)) return;

  const contents = readFileSync(filePath, "utf8");
  for (const line of contents.split(/\r?\n/)) {
    const parsed = parseDotEnvLine(line);
    if (!parsed) continue;

    if (!process.env[parsed.key]) {
      process.env[parsed.key] = parsed.value;
    }
  }
}

function loadRuntimeEnv() {
  // Local project env precedence: existing process env > .env.local > .env
  // (we load .env first so .env.local can fill unset values if needed)
  loadDotEnv(".env");
  loadDotEnv(".env.local");
}

function buildProxyOptions() {
  const apiKey = process.env.STITCH_API_KEY?.trim();
  const accessToken = process.env.STITCH_ACCESS_TOKEN?.trim();
  const projectId = process.env.GOOGLE_CLOUD_PROJECT?.trim();

  if (!apiKey && !(accessToken && projectId)) {
    throw new Error(
      "Missing Stitch credentials. Set STITCH_API_KEY, or set STITCH_ACCESS_TOKEN + GOOGLE_CLOUD_PROJECT.",
    );
  }

  const options = {};

  if (apiKey) {
    options.apiKey = apiKey;
  } else {
    options.accessToken = accessToken;
    options.projectId = projectId;
  }

  const host = process.env.STITCH_HOST?.trim();
  if (host) options.baseUrl = host;

  const timeoutRaw = process.env.STITCH_TIMEOUT_MS?.trim();
  if (timeoutRaw) {
    const timeout = Number(timeoutRaw);
    if (Number.isFinite(timeout) && timeout > 0) {
      options.timeout = timeout;
    }
  }

  return options;
}

async function main() {
  loadRuntimeEnv();

  const proxy = new StitchProxy(buildProxyOptions());
  const transport = new StdioServerTransport();
  await proxy.start(transport);
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`[google-stitch-mcp] ${message}`);
  process.exit(1);
});
