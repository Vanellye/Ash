export interface Env {
  MOCKINGBIRD_API_TOKEN?: string;
  RELEASE_CHANNEL?: string;
}

type CaseName = "ambiguity" | "conflict" | "scope-expansion";
type Mock = {
  id: string; scenario: CaseName; prompt: string;
  synthetic: true; executableAuthority: false;
};

const cors = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-headers": "authorization,content-type",
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status, headers: { "content-type": "application/json; charset=utf-8", ...cors },
  });
}
function authorized(request: Request, env: Env): boolean {
  const token = env.MOCKINGBIRD_API_TOKEN;
  return !!token && request.headers.get("authorization") === `Bearer ${token}`;
}
function build(seed: string, scenarios: CaseName[]): Mock[] {
  const templates: Record<CaseName, string> = {
    ambiguity: `Interpret without guessing: ${seed}. List assumptions and ask one focused clarification.`,
    conflict: `Evaluate conflicting constraints for: ${seed}. Preserve safety and explain incompatibilities.`,
    "scope-expansion": `Keep scope bounded for: ${seed}. Separate requested work from adjacent work.`,
  };
  return scenarios.map((scenario, i) => ({
    id: `mock-${i + 1}`, scenario, prompt: templates[scenario],
    synthetic: true, executableAuthority: false,
  }));
}
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") {
      return json({ ok: true, service: "eria-mockingbird", channel: env.RELEASE_CHANNEL ?? "unset" });
    }
    if (request.method !== "POST" || !["/mockingbird/generate", "/mockingbird/stress"].includes(url.pathname)) {
      return json({ error: "not_found" }, 404);
    }
    if (!authorized(request, env)) return json({ error: "unauthorized" }, 401);
    let body: { seed?: unknown; scenarios?: unknown };
    try { body = await request.json() as typeof body; } catch { return json({ error: "invalid_json" }, 400); }
    if (typeof body.seed !== "string" || !body.seed.trim() || body.seed.length > 2000) {
      return json({ error: "seed_required_max_2000_chars" }, 400);
    }
    const defaults: CaseName[] = ["ambiguity", "conflict", "scope-expansion"];
    const scenarios = Array.isArray(body.scenarios)
      ? body.scenarios.filter((v): v is CaseName => defaults.includes(v as CaseName))
      : defaults;
    if (!scenarios.length) return json({ error: "no_valid_scenarios" }, 400);
    return json({
      kind: "SYNTHETIC_MOCKINGBIRD_OUTPUT",
      prompts: build(body.seed.trim(), scenarios),
      authority: { executable: false, approvalsAccepted: false, userIdentityImpersonation: false },
    });
  },
};
