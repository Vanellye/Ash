import { createServer } from "node:http";
import { DatabaseSync } from "node:sqlite";
import { readFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import worker from "./src/index.js";

const port = Number(process.env.PORT || 8080);
const dbPath = process.env.DATABASE_PATH || "/data/eria.sqlite";
mkdirSync(dirname(dbPath), { recursive: true });
const db = new DatabaseSync(dbPath);
db.exec(readFileSync(new URL("./migrations/0001_initial.sql", import.meta.url), "utf8"));
db.exec("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;");

const d1 = {
  prepare(sql) {
    let values = [];
    const statement = db.prepare(sql);
    const api = {
      bind(...args) { values = args; return api; },
      async first() { return statement.get(...values) ?? null; },
      async all() { return { results: statement.all(...values) }; },
      async run() { return statement.run(...values); }
    };
    return api;
  },
  async batch(items) {
    db.exec("BEGIN IMMEDIATE");
    try {
      const results = [];
      for (const item of items) {
        const sql = item && item.__sql;
        if (sql) results.push(db.prepare(sql).run(...(item.__values || [])));
        else throw new Error("Unsupported batch statement");
      }
      db.exec("COMMIT");
      return results;
    } catch (error) { db.exec("ROLLBACK"); throw error; }
  }
};

// Batch support for the worker's two-statement mutation transaction.
const originalPrepare = d1.prepare;
d1.prepare = (sql) => {
  let values = [];
  const statement = db.prepare(sql);
  const api = {
    __sql: sql,
    __values: values,
    bind(...args) { values = args; api.__values = args; return api; },
    async first() { return statement.get(...values) ?? null; },
    async all() { return { results: statement.all(...values) }; },
    async run() { return statement.run(...values); }
  };
  return api;
};

const server = createServer(async (req, res) => {
  try {
    const chunks = [];
    let size = 0;
    for await (const chunk of req) {
      size += chunk.length;
      if (size > 64 * 1024) { res.writeHead(413).end(); return; }
      chunks.push(chunk);
    }
    const request = new Request(`http://127.0.0.1:${port}${req.url}`, {
      method: req.method,
      headers: req.headers,
      body: ["GET", "HEAD"].includes(req.method) ? undefined : Buffer.concat(chunks)
    });
    const response = await worker.fetch(request, {
      DB: d1,
      MUTATION_TOKEN: process.env.MUTATION_TOKEN || ""
    });
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
  } catch (error) {
    console.error("request_failed", error);
    if (!res.headersSent) res.writeHead(500, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "internal_server_error" }));
  }
});

server.listen(port, "0.0.0.0", () => console.log(`ERIA API listening on :${port}`));
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => {
  server.close(() => { db.close(); process.exit(0); });
});
