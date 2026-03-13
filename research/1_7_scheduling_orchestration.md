# Research 1.7 — Scheduling/Orchestration Tools

> **Task:** Evaluate scheduling/orchestration tools for periodic signal checks (`APScheduler`, `Celery`, cron-based).

---

## Summary & Recommendation

### Primary: **APScheduler 3.x** (`BackgroundScheduler`)

For a single-process signal scanning app, APScheduler is the clear winner:

| Criteria | APScheduler | Celery | Cron |
|----------|-------------|--------|------|
| **Complexity** | Low | High | Minimal |
| **Broker required** | No | Yes (Redis/RabbitMQ) | No |
| **In-process** | Yes | No (separate workers) | No (separate process) |
| **Dynamic scheduling** | Yes (add/remove at runtime) | Yes (django-celery-beat) | No (edit crontab) |
| **Cross-platform** | Yes | Linux preferred | Unix/Linux only |
| **Async support** | Yes (`AsyncIOScheduler`) | Yes | No |
| **Persistence** | Optional (SQLite, Redis, MongoDB) | Broker-backed | OS-level |
| **Dependencies** | Minimal | Redis/RabbitMQ + Celery | None |
| **Streamlit integration** | BackgroundScheduler in bg thread | Overkill | External process |

**Why APScheduler:**
1. **No external services** — no Redis, no RabbitMQ, no message broker. Just Python
2. **In-process** — runs inside our app, shares memory with signal engine (no serialization overhead)
3. **Dynamic** — users can add/remove asset pairs and timeframes at runtime via UI, scheduler updates instantly
4. **Flexible triggers** — interval (every 5 min), cron (at market open), date (one-shot)
5. **Lightweight** — single pip install, minimal dependencies
6. **Good enough** — we're scanning signals, not processing millions of tasks. APScheduler handles this effortlessly

**Why NOT Celery:**
- Requires Redis or RabbitMQ — unnecessary infrastructure for a personal/small-team signal scanner
- Designed for distributed task queues across multiple workers/machines — we run on one machine
- Setup complexity is disproportionate to our needs
- Would be the right choice if we scaled to hundreds of users with separate worker nodes

**Why NOT bare cron:**
- External to the application — can't dynamically adjust schedules from the UI
- Unix-only — no Windows support
- No error handling, retry logic, or job state management
- No integration with Python application state

---

## APScheduler Architecture for Our Project

### Scheduler Types

| Scheduler | Use Case | Our Usage |
|-----------|----------|-----------|
| `BackgroundScheduler` | Non-blocking, runs in a background thread | **Primary** — for Streamlit/CLI apps |
| `AsyncIOScheduler` | Async apps using asyncio event loop | Alternative if we go fully async |
| `BlockingScheduler` | Blocks the main thread until shutdown | Not suitable (blocks UI) |

### Trigger Types

| Trigger | Syntax | Use Case |
|---------|--------|----------|
| `interval` | `minutes=5` | Periodic signal scans (every N minutes) |
| `cron` | `hour=8, minute=0` | Daily summary at fixed time |
| `date` | `run_date='2026-03-14 09:00'` | One-shot scheduled scan |

### Example: Signal Scanner Scheduler

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

# Scan BTC/ETH SMT divergence every 5 minutes
scheduler.add_job(
    func=scan_smt_divergence,
    trigger=IntervalTrigger(minutes=5),
    kwargs={"pair": ("BTC/USDT", "ETH/USDT"), "timeframe": "4H"},
    id="smt_btc_eth_4h",
    name="SMT Divergence: BTC/ETH 4H",
    replace_existing=True,
    max_instances=1,          # Prevent overlap if scan takes long
    misfire_grace_time=60,    # Allow 60s late execution
)

# Scan RSI divergence every 15 minutes
scheduler.add_job(
    func=scan_rsi_divergence,
    trigger=IntervalTrigger(minutes=15),
    kwargs={"pair": "BTC/USDT", "timeframe": "1H"},
    id="rsi_btc_1h",
    name="RSI Divergence: BTC 1H",
    replace_existing=True,
    max_instances=1,
)

# Daily summary at 08:00 UTC
scheduler.add_job(
    func=send_daily_summary,
    trigger=CronTrigger(hour=8, minute=0, timezone="UTC"),
    id="daily_summary",
    name="Daily Signal Summary",
)

scheduler.start()
```

### Dynamic Job Management (Runtime)

```python
# Add a new scan from the UI
scheduler.add_job(
    func=scan_smt_divergence,
    trigger=IntervalTrigger(minutes=10),
    kwargs={"pair": ("SOL/USDT", "ETH/USDT"), "timeframe": "1H"},
    id="smt_sol_eth_1h",
)

# Pause a scan
scheduler.pause_job("smt_btc_eth_4h")

# Resume a scan
scheduler.resume_job("smt_btc_eth_4h")

# Remove a scan
scheduler.remove_job("smt_sol_eth_1h")

# Modify interval
scheduler.reschedule_job("smt_btc_eth_4h", trigger=IntervalTrigger(minutes=10))

# List all active jobs
for job in scheduler.get_jobs():
    print(f"{job.id}: {job.name} — next run: {job.next_run_time}")
```

### Job Persistence (Optional)

By default APScheduler stores jobs in memory (lost on restart). For persistence:

```python
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = BackgroundScheduler(
    jobstores={
        "default": SQLAlchemyJobStore(url="sqlite:///jobs.db")
    }
)
```

Persistence options:
- **SQLite** — simplest, no extra service needed (recommended for us)
- **Redis** — if we already use Redis for caching
- **MongoDB** — if we use MongoDB for market data storage

### Streamlit Integration Pattern

```python
import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize scheduler ONCE (survives Streamlit reruns)
if "scheduler" not in st.session_state:
    scheduler = BackgroundScheduler()
    scheduler.add_job(scan_all_signals, "interval", minutes=5, id="main_scan")
    scheduler.start()
    st.session_state.scheduler = scheduler

# Display job status in the UI
for job in st.session_state.scheduler.get_jobs():
    st.write(f"{job.name}: next run at {job.next_run_time}")
```

### Error Handling & Listeners

```python
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

def job_listener(event):
    if event.exception:
        # Log error + send notification via Apprise
        notify_error(f"Job {event.job_id} failed: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} executed successfully")

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
```

---

## Scheduling Strategy for Signal Scanning

### Recommended Scan Intervals

| Signal Type | Timeframe | Scan Interval | Rationale |
|-------------|-----------|---------------|-----------|
| SMT Divergence | 4H | Every 5 min | Detect new 4H candle close, early detection |
| SMT Divergence | 1H | Every 2 min | Higher frequency for shorter timeframe |
| RSI Divergence | 4H | Every 5 min | Same as SMT |
| RSI Divergence | 1H | Every 2 min | Same as SMT |
| Daily Summary | 1D | Once at 00:05 UTC | After daily candle close |
| Correlation Check | N/A | Every 30 min | Monitor BTC-ETH correlation stability |

### Misfire Handling

When a job can't run at its scheduled time (e.g., app was paused):

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `coalesce=True` | Run once, skip missed runs | **Default for us** — no point running stale scans |
| `max_instances=1` | Prevent parallel runs of same job | **Always** — avoid duplicate scans |
| `misfire_grace_time=60` | Allow job to run if ≤60s late | **Set this** — short grace period |

```python
scheduler.add_job(
    func=scan_signals,
    trigger=IntervalTrigger(minutes=5),
    coalesce=True,
    max_instances=1,
    misfire_grace_time=60,
)
```

---

## APScheduler 4.0 Status (Future Consideration)

APScheduler 4.0 is a **ground-up redesign** currently in alpha (`4.0.0a1`). Key changes:

| Feature | 3.x | 4.0 (alpha) |
|---------|-----|-------------|
| Async | `AsyncIOScheduler` (separate class) | Async-first via AnyIO (asyncio + Trio) |
| Architecture | Monolithic scheduler | Scheduler + Worker + Event Broker (separated) |
| Scalability | Single process | Multi-node via shared data store + event brokers |
| Triggers | Stateless | Stateful (better combined triggers) |
| Timezone | pytz | `zoneinfo` (stdlib) |
| Config | `configure()` method | Constructor kwargs |

**Our stance:** Use **3.x stable** (`3.11.2`) now. APScheduler 4.0 is explicitly marked as not production-ready and may change in backwards-incompatible ways. When 4.0 stabilizes, migration should be straightforward — our usage is simple interval/cron triggers.

---

## Alternative Lightweight Schedulers (Considered but Not Selected)

| Library | Pros | Cons | Verdict |
|---------|------|------|---------|
| **`schedule`** | Dead simple API (`schedule.every(5).minutes.do(job)`) | No persistence, no async, single-threaded | Too basic for our needs |
| **Huey** | Lightweight task queue with Redis | Requires Redis (external dependency) | Unnecessary complexity |
| **Dramatiq** | Clean API, async, good error handling | Requires RabbitMQ or Redis | Same as Huey — overkill |
| **RQ (Redis Queue)** | Simple Redis-based task queue | Requires Redis | Same concern |
| **`asyncio` native** | `asyncio.create_task` + `asyncio.sleep` loops | No persistence, no management, DIY everything | Not a scheduler |

None of these offer a better tradeoff than APScheduler for our single-process, no-broker-required use case.

---

## Integration with Project Architecture

```
┌─────────────────────────────────────────────┐
│              Configuration (YAML)           │
│  - scan intervals per signal type           │
│  - asset pairs and timeframes               │
│  - notification channels                    │
└──────────────┬──────────────────────────────┘
               │ loaded at startup
               ▼
┌─────────────────────────────────────────────┐
│        APScheduler (BackgroundScheduler)    │
│                                              │
│  Job: scan_smt("BTC/ETH", "4H")  every 5m  │
│  Job: scan_rsi("BTC", "1H")      every 2m  │
│  Job: daily_summary()          cron 00:05   │
│  Job: check_correlation()      every 30m    │
│                                              │
│  Listeners: on_error → notify via Apprise   │
│  JobStore: SQLite (optional persistence)    │
└──────────────┬──────────────────────────────┘
               │ calls
               ▼
┌─────────────────────────────────────────────┐
│           Signal Engine (Core)              │
│  - fetch OHLCV (ccxt)                       │
│  - compute indicators (pandas-ta)           │
│  - detect divergences                       │
│  - emit signals → Notification Service      │
└─────────────────────────────────────────────┘
```

---

## Dependency

| Package | Version | Install |
|---------|---------|---------|
| **`APScheduler`** | `3.11.x` (stable) | `pip install apscheduler` |

Optional for persistence:
- `SQLAlchemy` — for SQLite job store (likely already a dependency)

---

## Sources

- [APScheduler — GitHub](https://github.com/agronholm/apscheduler)
- [APScheduler — PyPI](https://pypi.org/project/APScheduler/)
- [APScheduler User Guide — ReadTheDocs](https://apscheduler.readthedocs.io/en/3.x/userguide.html)
- [APScheduler 4.0 Migration Guide](https://apscheduler.readthedocs.io/en/master/migration.html)
- [APScheduler 4.0 Progress Tracking — GitHub Issue #465](https://github.com/agronholm/apscheduler/issues/465)
- [Job Scheduling in Python with APScheduler — Better Stack](https://betterstack.com/community/guides/scaling-python/apscheduler-scheduled-tasks/)
- [Scheduling Tasks: APScheduler vs Celery Beat — Leapcell](https://leapcell.io/blog/scheduling-tasks-in-python-apscheduler-vs-celery-beat)
- [Chapter 9: Task Scheduling — Celery and APScheduler](https://aligheshlaghi97.github.io/asynchronous-python/chapter9/)
- [Celery vs APScheduler — StackShare](https://stackshare.io/stackups/apscheduler-vs-celery)
- [Task Scheduling and Background Jobs in Python — Naveen PN](https://blog.naveenpn.com/task-scheduling-and-background-jobs-in-python-the-ultimate-guide)
- [If Celery Bores You — Alternatives — Substack](https://smshahinulislam.substack.com/p/if-celery-bores-you-here-are-some)
- [Scheduling Regular Events: Cron, Celery, and Alternatives — CopyProgramming](https://copyprogramming.com/howto/scheduling-a-regular-event-cron-cron-alternatives-including-celery)
- [Python Job Scheduling: Methods and Overview — AIMultiple](https://aimultiple.com/python-job-scheduling)
- [Streamlit + Scheduler Discussion — Streamlit Forum](https://discuss.streamlit.io/t/is-it-possible-to-include-a-kind-of-scheduler-within-streamlit/31279)
- [Tasklit: Task Scheduling on Streamlit — GitHub](https://github.com/straussmaximilian/tasklit)
- [APScheduler Guide — Comprehensive — Oreate AI](https://www.oreateai.com/blog/a-comprehensive-guide-to-the-python-task-scheduling-framework-apscheduler/0d1447747384720491913235dfed188d)
- [APScheduler Introduction — jdhao](https://jdhao.github.io/2021/10/20/python_apsscheduler_intro/)
- [Using Python APScheduler — PolarSparc](https://polarsparc.github.io/Python/APScheduler.html)
