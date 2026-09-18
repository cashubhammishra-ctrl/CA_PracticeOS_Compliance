# Tally Connector Setup

`TallyConnector` connects via the **ICAI Tally Prime MCP Server**
(https://ai.icai.org/usecases_details.php?id=200), the exact module this
capstone's L2 syllabus points at. Zoho Books and SAP are **not built** in this
timeline — `BaseConnector` (`connectors/base_connector.py`) exists so they can
be added later without touching the rest of the backend.

## What the Tally MCP Server actually is

- A local **Node.js** process, distributed by ICAI as a zip
  (`tally_mcp_server_v6.zip`), extracted to a folder on the same machine as
  Tally Prime.
- It talks to Tally Prime over Tally's own XML/ODBC gateway on **port 9000**,
  which you enable in Tally Prime via **F1 → Settings → Connectivity →
  Client/Server configuration**, setting "TallyPrime acts as: Server".
- It is launched by the **MCP client itself** (e.g. Claude Desktop) as a local
  subprocess over stdio — there is no standing server you connect to over the
  network by default.

## The architecture constraint (read this before assuming Tally "isn't working")

Because the MCP server is a local subprocess and Tally Prime is a local
Windows desktop application, **a backend deployed to Render/Railway cannot
reach a user's local Tally Prime instance over the public internet** without
a network tunnel exposing port 9000 — that's a real infrastructure constraint,
not a bug in `TallyConnector`. Per CLAUDE.md Section 6 ("if the Tally sandbox
isn't reachable, don't burn a session debugging network/auth issues — build
against a cached sample JSON response instead and flag it honestly"),
`TallyConnector` is built to be honest about this:

- If `TALLY_MCP_COMMAND` is set in `.env` **and** the backend process is
  running on the same machine as Tally Prime and the extracted MCP server
  (e.g. during a local live demo), every `fetch_*` method makes a real MCP
  stdio call and tags each result `"source": "live"`.
- Otherwise (including the deployed Render/Railway backend), every `fetch_*`
  method falls back to `examples/outputs/sample_tally_pull.json` — a real
  data pull captured from a live Tally MCP connection during development —
  and tags each result `"source": "cached_fallback"`. Nothing is silently
  faked as live.

## Configuring the live path (for a local demo)

1. Download and extract the Tally MCP Server zip from the ICAI link above.
2. Enable Tally Prime's XML server (F1 → Settings → Connectivity → port 9000)
   and open the company you want to demo against.
3. In `.env`, set:
   ```
   TALLY_MCP_COMMAND=node
   TALLY_MCP_ARGS=D:\path\to\extracted\tally-mcp-server\index.js
   ```
   (the exact entry-point filename depends on the extracted zip's contents —
   check its `package.json` "main" field or README if `index.js` isn't right).
4. Run the backend on that same machine. `TallyConnector` will now use the
   live path automatically — no code changes needed.

## Tool mapping

| BaseConnector method | Tally MCP tool(s) used |
|---|---|
| `fetch_clients()` | `list-master` (collection=`company`) |
| `fetch_ledgers(client_id)` | `set-company` then `list-master` (collection=`ledger`) |
| `fetch_vouchers(client_id, date_range)` | `ledger-account` (voucher-level GL statement) |
| `fetch_invoices(client_id)` | `bills-outstanding` (nature=`receivable`) |

These tool names were confirmed by calling them directly against a live Tally
MCP connection during development (2026-09-16 and 2026-09-20) — they are not
guessed.

---

## A second, simpler connector: the L1 app's in-browser Tally Connector

`CA_PracticeOS_Compliance.html` (the L1 app) also has its own **"📊 Tally
Connector"** section, built independently of the Python/MCP connector above.
It talks directly to Tally Prime's built-in XML/HTTP gateway (the same port
9000 interface) using plain browser `fetch()` — no Node.js, no Python, no MCP
needed for this path.

### Why it needs a relay

A browser cannot POST XML straight to Tally's gateway: Tally doesn't answer
the CORS preflight check browsers send before a cross-origin POST, so the
request gets blocked before it ever reaches Tally. This was confirmed live
(not guessed) — testing directly against a running Tally Prime instance
during development returned `Failed to fetch` from the app, while a plain
GET (typing the URL into the address bar) worked fine, which is the
signature of a CORS block, not a real connectivity problem.

The fix: `connectors/tally_browser_relay.py`, a small dependency-free Python
script that sits between the browser and Tally. It answers the CORS
preflight correctly, then forwards the request to Tally over a plain
server-to-server connection (not subject to browser CORS at all).

```bash
python connectors/tally_browser_relay.py
```

Then in the app's Tally Connector section, set **Tally Server URL** to
`http://localhost:9001` (the relay's port) instead of Tally's own 9000 —
Tally itself needs no reconfiguration.

### A real Tally XML quirk this connector works around

Tested live against a running Tally Prime (Educational edition) instance on
2026-09-18: Tally's ledger export embeds illegal XML 1.0 control characters
as hierarchy-depth markers inside group names — e.g. a `PARENT` value
literally contains `&#4; Primary`. Character code 4 is syntactically valid
as an escaped numeric reference but is one of the code points XML 1.0
forbids outright, so a strict browser `DOMParser` rejects the *entire*
document over one embedded marker. `sanitizeTallyXml()` strips these before
parsing. This was a genuine bug caught by testing against real Tally data,
not a hypothetical.

### Verified live (2026-09-18)

Against a real running Tally Prime instance ("Techno Traders Ltd"):
Test Connection, Fetch Companies (1 company), and Fetch Ledgers (48 ledgers
with real opening/closing balances) all confirmed working end to end through
the relay. Two bugs were caught and fixed during this testing: a stray
`<CMPINFO>` count element (unrelated metadata that happens to share the tag
name `COMPANY`/`LEDGER`) was polluting both result lists with a bogus empty
row — fixed by requiring a `NAME` attribute on matched elements.
