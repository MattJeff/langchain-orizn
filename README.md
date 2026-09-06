# langchain-orizn

LangChain tools for the [Orizn Visa API](https://visa.orizn.app) — visa requirements for
199 passports x 202 destinations, in 15 languages, from official government sources.

## Run it in under 5 minutes

**1. Get a free API key** (10 seconds, no credit card):
→ **https://visa.orizn.app/visa-api**

Free tier: **100 requests/month**, all 15 languages included.
(5 requests until you confirm your email — click the link in the confirmation mail.)

**2. Install**

```bash
pip install langchain-orizn
export ORIZN_API_KEY=orizn_visa_...
```

**3. Run**

```python
# quickstart.py
from langchain_orizn import OriznQuickVisaCheckTool, OriznVisaCheckTool

quick = OriznQuickVisaCheckTool()  # reads ORIZN_API_KEY
print(quick.invoke({"passport": "FRA", "destination": "JPN"}))

full = OriznVisaCheckTool()
print(full.invoke({"passport": "FRA", "destination": "JPN", "lang": "fr"}))
```

**Expected output** — the first call prints a compact JSON object:

```json
{"passport": "FRA", "destination": "JPN", "requirement": "visa_free",
 "visa_free_days": 90, "visa_required": false, "last_verified": "2026-05-10", "...": "..."}
```

and the second prints the full record (`data.description`, `data.documents_required`,
`data.process`, `data.cost`, `data.processing_time`, …) in French.

Both tools require the API key. Without it they raise an error naming
`https://visa.orizn.app/visa-api`, so an agent can report what is missing.

## Use with a LangChain agent

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_orizn import OriznQuickVisaCheckTool, OriznVisaCheckTool

tools = [OriznQuickVisaCheckTool(), OriznVisaCheckTool()]
agent = create_react_agent(ChatOpenAI(model="gpt-4o-mini"), tools)

result = agent.invoke(
    {"messages": [("user", "Do I need a visa to go from Brazil to Japan?")]}
)
print(result["messages"][-1].content)
```

## Available tools

| Tool | Use it when | Endpoint |
|------|-------------|----------|
| `OriznQuickVisaCheckTool` | "Do I need a visa, and for how long?" | `/api/v1/visa/check` |
| `OriznVisaCheckTool` | documents, fees, processing time, process steps, tips | `/api/v1/visa` |

Both read `ORIZN_API_KEY`, or take the key explicitly:
`OriznVisaCheckTool(api_key="orizn_visa_...")`.

## Languages

`en, fr, es, pt, de, it, ja, ko, zh, ru, ar, hi, th, vi, tl` — available on **every plan,
including free**, via the `lang` argument of `OriznVisaCheckTool`.

## Plans

| Plan | Price | Requests/month |
|------|-------|----------------|
| Free | 0 | 100 |
| Starter | $49 | 30,000 |
| Pro | $199 | 250,000 |
| Business | $699 | 1,000,000 |

[Upgrade](https://visa.orizn.app/visa-api/login?next=%2Fvisa-api%2Fdashboard%2Fbilling%3Fplan%3Dstarter%26source%3Dlangchain_py)

## Changelog

**0.2.0 — breaking.** `OriznQuickVisaCheckTool` now requires an API key. The `/api/v1/visa/check`
endpoint stopped serving keyless requests, so the old "no API key needed" path returned 401 on
every call. Pass `api_key=` or set `ORIZN_API_KEY`. Errors now carry the URL where a key is
obtained, and `_run` returns real JSON instead of a Python `repr`.

**0.1.1** — initial release.

## Links

- [Get an API key](https://visa.orizn.app/visa-api)
- [API docs](https://visa.orizn.app/visa-api/dashboard/docs)
- [MCP server](https://github.com/MattJeff/orizn-mcp-server)
- [JS package](https://www.npmjs.com/package/@orizn/langchain)

## Feedback

Building a travel agent or visa tool? → **api@orizn.app**

## License

MIT
