# Research 1.5 — UI/Interface Options (Zero Frontend/Styling Effort)

> **Task:** Evaluate UI/interface options that require zero frontend/styling effort. Compare Streamlit, Gradio, Textual (TUI), CLI with `rich`/`typer`.

---

## Summary & Recommendation

| | Streamlit | Gradio | Textual (TUI) | Rich + Typer (CLI) |
|---|---|---|---|---|
| **Best for** | Data dashboards, analytics | ML model demos | Interactive terminal apps | CLI tools, scripts |
| **Interface** | Web browser | Web browser | Terminal | Terminal |
| **Real-time data** | Moderate (rerun model) | Limited (submit-based) | Excellent (async, workers) | Poor (static output) |
| **Charting** | Excellent (Plotly, Altair) | Decent (Matplotlib) | Basic (sparklines, custom) | Tables only |
| **Zero-effort setup** | Very low | Very low | Low-medium | Very low |
| **No browser needed** | No | No | Yes | Yes |
| **Deployment** | Web server | Web server / HF Spaces | Runs anywhere (incl. SSH) | Just Python |
| **State management** | Session state (reruns) | Reactive (events) | Reactive attributes (async) | Stateless |
| **Concurrency** | Thread-per-session | Thread-per-session | Native asyncio | N/A |
| **Large datasets** | Good | Poor | Good | Good (streaming) |
| **Community/ecosystem** | Very large | Large (HF-backed) | Growing | Large |

**Recommendation for this project: Streamlit** — with the option to add a Textual TUI later for terminal-only environments.

**Rationale:**
1. Our primary need is a **signal dashboard** with charts, tables, and interactive filters — Streamlit's sweet spot
2. Streamlit has native Plotly/Altair integration for candlestick charts and signal visualizations
3. Zero frontend code required — pure Python
4. `st.dataframe`, `st.metric`, `st.plotly_chart` cover 90% of our UI needs out of the box
5. Auto-refresh via `streamlit-autorefresh` or `st.fragment` (Streamlit 1.33+) handles periodic signal updates
6. For truly real-time WebSocket data, Streamlit's session state + background threads work adequately for our polling intervals (minutes, not milliseconds)
7. Massive ecosystem of examples for crypto dashboards specifically

---

## Detailed Evaluation

### 1. Streamlit

**What it is:** Open-source Python framework that turns data scripts into shareable web apps. Write Python, get a web UI automatically.

**How it works:**
- Script runs top-to-bottom on every interaction (reactive rerun model)
- Widgets (sliders, dropdowns, buttons) automatically trigger reruns
- Session state persists data across reruns per user session
- Since v1.33: `st.fragment` allows partial reruns (only specific functions re-execute)

**Strengths for our project:**
- **Charting:** Native support for Plotly, Altair, Matplotlib, Vega-Lite. Plotly's `go.Candlestick` is perfect for OHLCV data
- **Data display:** `st.dataframe` for interactive tables, `st.metric` for KPI cards (signal counts, current price)
- **Layout:** `st.columns`, `st.tabs`, `st.sidebar` — no CSS needed
- **Interactivity:** Dropdowns for asset pair selection, timeframe selection, signal type filtering
- **Deployment:** Streamlit Community Cloud (free), or any server with `streamlit run`
- **Ecosystem:** `streamlit-autorefresh` for periodic polling, many crypto dashboard examples

**Limitations:**
- **Rerun model:** Entire script re-executes on every widget change (mitigated by `st.cache_data`, `st.fragment`)
- **No built-in auth:** Need external auth (Streamlit Community Cloud has basic auth)
- **Not truly real-time:** Polling-based, not push-based. Fine for our 1-minute+ signal refresh intervals
- **Scaling:** Single-threaded per session. Not an issue for personal/small-team use

**Real-time data pattern for our use case:**
```python
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 60 seconds
st_autorefresh(interval=60_000, key="signal_refresh")

# Or with st.fragment (Streamlit 1.33+):
@st.fragment(run_every="60s")
def live_signals():
    signals = fetch_latest_signals()
    st.dataframe(signals)
```

**Verdict:** Best fit for our signal dashboard. Handles our requirements with minimal code.

---

### 2. Gradio

**What it is:** Python library for building web UIs, primarily designed for ML model interaction. Acquired by Hugging Face in 2022.

**How it works:**
- Define input/output components → Gradio generates a web UI
- Submit-button-driven by default (`live=True` for auto-update)
- Event-driven architecture (callbacks on component changes)

**Strengths:**
- Extremely fast to prototype — even simpler than Streamlit for basic interfaces
- Built-in sharing via Hugging Face Spaces (one command)
- Good for demo/presentation purposes

**Limitations for our project:**
- **Not designed for dashboards:** Gradio excels at input→output interfaces (upload image → get classification). Our use case is a monitoring dashboard, not a model demo
- **Poor large dataset handling:** Not optimized for structured data tables or large DataFrames
- **Limited charting:** No native Plotly candlestick support; would need custom HTML components
- **Fixed UI design:** Less layout flexibility than Streamlit (no sidebar, limited column control)
- **Real-time:** Not built for continuous data streaming or auto-refresh dashboards
- **Share links expire:** Public share links expire after 72 hours

**Verdict:** Wrong tool for the job. Gradio is excellent for ML demos but not for data monitoring dashboards.

---

### 3. Textual (TUI)

**What it is:** Modern terminal UI framework by Textualize (same team behind Rich). Build interactive, async-powered terminal applications with CSS-like styling.

**How it works:**
- Widget-based architecture (buttons, tables, inputs, sparklines, trees)
- CSS-like stylesheets for layout and theming
- Fully async (built on asyncio) — ideal for real-time data
- Reactive attributes for automatic UI updates when data changes
- Can also run in a web browser via `textual-web`

**Strengths:**
- **No browser needed:** Runs in any terminal, including over SSH
- **True real-time:** Native asyncio means smooth, non-blocking updates. Worker threads for background data fetching
- **Performance:** 120 FPS renders, delta-updates only dirty regions
- **Built-in widgets:** DataTable, Sparkline, Header, Footer, TabbedContent, Input
- **Sparklines:** Perfect for mini price charts in a signal dashboard
- **Low resource:** No web server, no browser overhead
- **Deployment:** Just Python. Works on servers, Raspberry Pi, SSH sessions

**Limitations for our project:**
- **No candlestick charts:** Terminal-based, so no Plotly/Altair integration. Limited to sparklines, ASCII-style charts, or custom braille-dot plots
- **Higher learning curve:** Textual's widget/CSS system takes more time to learn than Streamlit's linear script model
- **Less visual polish:** Even the best TUI can't match a web-based chart dashboard for visual richness
- **Smaller ecosystem:** Fewer examples and community components than Streamlit

**When to use it:**
- Running on a headless server (no browser available)
- SSH-only environments
- Lightweight monitoring alongside other terminal tools
- Personal preference for terminal workflows

**Verdict:** Excellent secondary option. Could serve as a lightweight "terminal monitor" complement to a Streamlit dashboard. Not the primary UI due to charting limitations.

---

### 4. Rich + Typer (CLI)

**What it is:** Rich = beautiful terminal formatting library. Typer = CLI framework built on Click with type hints. Together they create polished CLI tools.

**How it works:**
- Typer handles command parsing, help text, argument validation
- Rich handles output formatting: tables, panels, progress bars, syntax highlighting, markdown
- Stateless: each command invocation runs, outputs, and exits

**Strengths:**
- **Absolute minimum effort:** A few lines of code for a beautiful CLI
- **Perfect for one-shot queries:** `python signals.py check --pair BTC/ETH --timeframe 4H`
- **Composable:** Output can be piped to other tools, logged, or used in cron jobs
- **No overhead:** No server, no browser, no persistent process
- **Tables:** `rich.table.Table` produces excellent formatted tables in the terminal

**Limitations for our project:**
- **No interactivity:** Each run is stateless — can't have a live-updating dashboard
- **No charts:** Tables and text only (no sparklines without Textual)
- **No filtering/drill-down:** Would need separate commands for different views
- **Not a dashboard:** It's a reporting tool, not a monitoring tool

**When to use it:**
- CLI interface for running signal scans: `python scan.py --pair BTC/ETH --tf 4H`
- Generating signal reports for logging or alerting
- Cron job output
- Quick spot-checks between dashboard sessions

**Verdict:** Essential complement, not a primary UI. Every project needs a good CLI. Rich + Typer is the right choice for our command-line interface layer, but the dashboard should be Streamlit.

---

## Architecture Recommendation

```
┌─────────────────────────────────────────────┐
│              Signal Engine (Core)            │
│  - Data fetching (OHLCV via CCXT)           │
│  - Indicator calculation                     │
│  - SMT divergence detection                  │
│  - Signal generation                         │
│                                              │
│         Pure Python, no UI dependency        │
└──────────┬──────────────┬───────────────────┘
           │              │
    ┌──────▼──────┐  ┌───▼────────────┐
    │  Streamlit  │  │  Rich + Typer  │
    │  Dashboard  │  │     CLI        │
    │  (Primary)  │  │  (Secondary)   │
    └─────────────┘  └────────────────┘
                          │
                     ┌────▼─────────┐
                     │  Textual TUI │  (Optional future)
                     │  (Terminal)  │
                     └──────────────┘
```

**Key principle:** The signal engine is a standalone Python module with no UI dependencies. Each UI layer (Streamlit, CLI, Textual) imports and calls the engine. This separation means:
- We can build the CLI first (fastest to implement)
- Add Streamlit dashboard when we want visual exploration
- Optionally add Textual TUI later if terminal monitoring is desired
- All UIs share the same signal logic — no duplication

---

## Streamlit Key Components We'll Use

| Component | Purpose |
|-----------|---------|
| `st.plotly_chart` | Candlestick charts with signal overlays |
| `st.dataframe` | Signal tables with sorting/filtering |
| `st.metric` | KPI cards (signal count, price, correlation) |
| `st.sidebar` | Asset pair, timeframe, signal type selectors |
| `st.tabs` | Separate views (Signals, Charts, SMT, Settings) |
| `st.columns` | Multi-column layouts |
| `st.cache_data` | Cache API responses (TTL-based) |
| `st.fragment` | Partial reruns for live signal updates |
| `streamlit-autorefresh` | Periodic auto-refresh (every N seconds) |

---

## Sources

- [Streamlit vs Gradio: The Ultimate Showdown — UI Bakery](https://uibakery.io/blog/streamlit-vs-gradio)
- [Streamlit vs Gradio in 2025 — Squadbase](https://www.squadbase.dev/en/blog/streamlit-vs-gradio-in-2025-a-framework-comparison-for-ai-apps)
- [Gradio vs Streamlit vs Dash vs Flask — Towards Data Science](https://towardsdatascience.com/gradio-vs-streamlit-vs-dash-vs-flask-d3defb1209a2/)
- [Gradio vs. Streamlit: Choosing a Tool — Evidence](https://evidence.dev/learn/gradio-vs-streamlit)
- [Streamlit vs Gradio — MyScale](https://www.myscale.com/blog/streamlit-vs-gradio-ultimate-showdown-python-dashboards/)
- [Streamlit vs Gradio — Analytics Vidhya](https://www.analyticsvidhya.com/blog/2023/02/streamlit-vs-gradio-a-guide-to-building-dashboards-in-python/)
- [Streamlit vs Gradio — UnfoldAI](https://unfoldai.com/streamlit-vs-gradio/)
- [4 Streamlit Alternatives — Anvil](https://anvil.works/articles/4-alternatives-streamlit)
- [Top 10 Streamlit Alternatives 2026 — ClickUp](https://clickup.com/blog/streamlit-alternatives/)
- [Streamlit, Gradio, NiceGUI, Mesop — Medium](https://medium.com/@manikolbe/streamlit-gradio-nicegui-and-mesop-building-data-apps-without-web-devs-4474106778f5)
- [A Survey of Python Frameworks — Ploomber](https://ploomber.io/blog/survey-python-frameworks/)
- [Python Textual: Build Beautiful UIs — Real Python](https://realpython.com/python-textual/)
- [Textual Official Site](https://textual.textualize.io/)
- [Textual Sparkline Widget](https://textual.textualize.io/widgets/sparkline/)
- [Textual GitHub Repo](https://github.com/Textualize/textual)
- [Custom Charts in Textual Widget — DEV Community](https://dev.to/jaimin_patel_18d43f77f1b5/integrating-a-custom-charting-library-into-a-textual-custom-widget-elevate-your-tui-charts-289l)
- [Textual TUI Widgets 2025 — johal.in](https://johal.in/textual-tui-widgets-python-rich-terminal-user-interfaces-apps-2025/)
- [10 Best Python TUI Libraries 2025 — Medium](https://medium.com/towards-data-engineering/10-best-python-text-user-interface-tui-libraries-for-2025-79f83b6ea16e)
- [Building Real-Time Forex Dashboard with Streamlit — Medium](https://medium.com/data-science-collective/building-a-real-time-forex-dashboard-with-streamlit-and-websocket-56a14a985f42)
- [Real-Time Crypto Dashboard Pipeline — Medium](https://medium.com/@mlvoss0202/real-time-crypto-dashboard-feature-engineering-pipeline-using-python-uv-ruff-streamlit-201b19c1351a)
- [Financial Data Streaming with Alpaca and Streamlit](https://alpaca.markets/learn/financial-data-streaming-alpaca-streamlit)
- [streamlit-autorefresh — GitHub](https://github.com/kmcgrady/streamlit-autorefresh)
- [Streamlit Continuously Updating Dashboard — Forum](https://discuss.streamlit.io/t/continuously-updating-dashboard/532)
