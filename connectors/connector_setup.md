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
