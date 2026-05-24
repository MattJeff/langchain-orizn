# langchain-orizn

LangChain tools for the [Orizn Visa API](https://visa.orizn.app) — check visa requirements for 39,585 passport-destination pairs in 15 languages.

## Install

```bash
pip install langchain-orizn
```

## Quick start

```python
from langchain_orizn import OriznQuickVisaCheckTool, OriznVisaCheckTool

# No API key needed for quick checks
quick = OriznQuickVisaCheckTool()
print(quick.invoke({"passport": "FRA", "destination": "JPN"}))

# Full details (needs API key)
import os
os.environ["ORIZN_API_KEY"] = "your-key"
full = OriznVisaCheckTool()
print(full.invoke({"passport": "FRA", "destination": "JPN", "lang": "fr"}))
```

## Use with a LangChain agent

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

tools = [OriznQuickVisaCheckTool(), OriznVisaCheckTool(api_key="your-key")]
agent = create_react_agent(ChatOpenAI(model="gpt-4o"), tools)

result = agent.invoke({"messages": [("user", "Do I need a visa to go from Brazil to Japan?")]})
```

## Available tools

| Tool | Description | API Key |
|------|-------------|---------|
| `OriznVisaCheckTool` | Full visa details with documents, process & tips | Required |
| `OriznQuickVisaCheckTool` | Quick yes/no visa check | Not needed |

## Supported languages

en, fr, es, pt, de, ja, ko, zh, ru, it, ar, hi, th, vi, tl

## Links

- [API](https://visa.orizn.app)
- [Docs](https://visa.orizn.app/visa-api/dashboard/docs)
- [MCP Server](https://github.com/MattJeff/orizn-mcp-server)
- [GitHub](https://github.com/MattJeff/langchain-orizn)

## Feedback

Building a travel agent or visa tool? We'd love to hear what you're building.

→ **api@orizn.app** — Feature requests, partnerships, and questions welcome.

## License

MIT
