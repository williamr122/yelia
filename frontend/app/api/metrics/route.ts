import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";
import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const execFileAsync = promisify(execFile);

const projectRoot = path.resolve(process.cwd(), "..");

const pythonCandidates = [
  process.env.PYTHON,
  "C:\\Users\\HP\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
  "python",
  "py"
].filter(Boolean) as string[];

const pythonCode = `
import contextlib
import io
import os
import sys

with contextlib.redirect_stdout(sys.stderr):
    from app import create_app
    app = create_app()
    client = app.test_client()
    headers = {}
    token = os.environ.get("YELIA_METRICS_TOKEN", "").strip()
    if token:
        headers["X-Admin-Token"] = token
    response = client.get("/api/metrics", headers=headers)

sys.stdout.write(response.get_data(as_text=True))
`;

async function readMetrics(token: string) {
  let lastError: unknown = null;

  for (const python of pythonCandidates) {
    const args = python === "py" ? ["-3", "-c", pythonCode] : ["-c", pythonCode];
    try {
      const { stdout } = await execFileAsync(python, args, {
        cwd: projectRoot,
        timeout: 25000,
        maxBuffer: 12 * 1024 * 1024,
        env: {
          ...process.env,
          FLASK_ENV: "development",
          YELIA_METRICS_TOKEN: token
        }
      });
      return stdout;
    } catch (error) {
      lastError = error;
    }
  }

  const backendBase = (
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    process.env.BACKEND_URL ||
    "http://localhost:5000"
  ).replace(/\/+$/, "");
  const url = new URL(`${backendBase}/api/metrics`);
  if (token) url.searchParams.set("token", token);
  const response = await fetch(url, {
    method: "GET",
    cache: "no-store",
    headers: token ? { "X-Admin-Token": token } : undefined
  });
  if (!response.ok) {
    throw lastError || new Error(`Backend metrics HTTP ${response.status}`);
  }
  return response.text();
}

export async function GET(request: NextRequest) {
  try {
    const token = request.nextUrl.searchParams.get("token") || request.headers.get("x-admin-token") || "";
    const stdout = await readMetrics(token);
    const payload = JSON.parse(stdout);
    return NextResponse.json(payload, { status: payload?.ok === false ? 500 : 200 });
  } catch (error) {
    return NextResponse.json(
      {
        ok: false,
        error: {
          code: "METRICS_LOCAL_ERROR",
          message: error instanceof Error ? error.message : "No se pudieron cargar las metricas locales."
        }
      },
      { status: 500 }
    );
  }
}
