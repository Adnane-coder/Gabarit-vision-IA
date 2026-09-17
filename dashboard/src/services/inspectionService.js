// ---------------------------------------------------------------------------
// Service layer talking to the real FastAPI backend (api/). Falls back to
// mocked data only when VITE_API_BASE_URL is unset, so the UI can still be
// developed/demoed without the backend running.
// ---------------------------------------------------------------------------
import { getMockCameraStatus, getMockAiStatus, getMockInspectionResult, getMockHistory, getMockStats, KNOWN_TRACEES } from "./mockData";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function request(path, options) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.error?.message || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const TRACEES = KNOWN_TRACEES;

export async function fetchCameraStatus() {
  if (USE_MOCK) {
    await delay(150);
    return getMockCameraStatus();
  }
  return request("/camera/status");
}

export async function fetchAiStatus() {
  if (USE_MOCK) {
    await delay(150);
    return getMockAiStatus();
  }
  return request("/ai/status");
}

export async function runInspection(tracee) {
  if (USE_MOCK) {
    await delay(900);
    return getMockInspectionResult(tracee);
  }
  return request("/inspection/run", {
    method: "POST",
    body: JSON.stringify(tracee ? { tracee } : {}),
  });
}

export async function fetchHistory() {
  if (USE_MOCK) {
    await delay(150);
    return getMockHistory();
  }
  return request("/inspection/history");
}

export async function fetchStats() {
  if (USE_MOCK) {
    await delay(150);
    return getMockStats();
  }
  return request("/inspection/stats");
}
