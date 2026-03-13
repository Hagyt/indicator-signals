# Research 1.6 — Signal Delivery Channels

> **Task:** Evaluate signal delivery channels: Telegram bot, Discord webhook, email. Select libraries.

---

## Summary & Recommendation

### Primary: **Apprise** (unified notification library)

**Apprise** (`pip install apprise`) is a Python library that supports **90+ notification services** through a single, unified API — including Telegram, Discord, Slack, email (SMTP), Pushover, ntfy, Gotify, Microsoft Teams, and many more.

**Why Apprise over individual libraries:**
- One dependency instead of three (no separate Telegram + Discord + email libs)
- Adding a new channel = adding a URL string to config, zero code changes
- Built-in async delivery for all services
- Supports attachments and images where the service allows
- Configuration via YAML or simple text file — perfect for our YAML/TOML config design (task 2.6)
- 14,600+ GitHub stars, actively maintained (Copyright © 2025)
- Also available as a Docker container with REST API for microservice architectures

**Example usage:**
```python
import apprise

apobj = apprise.Apprise()

# Add notification targets — each is just a URL string
apobj.add("tgram://bot_token/chat_id")           # Telegram
apobj.add("discord://webhook_id/webhook_token")   # Discord
apobj.add("mailto://user:pass@gmail.com")         # Email (Gmail)
apobj.add("slack://token_a/token_b/token_c/#channel")  # Slack (bonus)

# Send to ALL configured channels at once
apobj.notify(
    body="🔻 Bearish SMT Divergence detected: BTC/ETH on 4H",
    title="Signal Alert",
    notify_type=apprise.NotifyType.WARNING,
)
```

**Configuration file approach (YAML):**
```yaml
# notifications.yml
urls:
  - tgram://bot_token/chat_id:
      tag: telegram
  - discord://webhook_id/webhook_token:
      tag: discord
  - mailto://user:pass@smtp.gmail.com:
      tag: email
```

```python
config = apprise.AppriseConfig()
config.add("/path/to/notifications.yml")

apobj = apprise.Apprise()
apobj.add(config)

# Send to specific channels by tag
apobj.notify(body="Signal!", tag="telegram")

# Or send to all
apobj.notify(body="Signal!")
```

### Fallback: Individual libraries (if Apprise doesn't meet a specific need)

| Channel | Library | Use Case |
|---------|---------|----------|
| Telegram | `python-telegram-bot` | If we need interactive bot features (inline keyboards, conversations) |
| Discord | `discord-webhook` | If we need advanced embed formatting beyond Apprise |
| Email | `aiosmtplib` | If we need fine-grained async SMTP control |

---

## Channel-by-Channel Evaluation

### 1. Telegram Bot

**Why Telegram is the top choice for trading signals:**
- Most crypto traders already use Telegram
- Instant push notifications on mobile
- Supports rich formatting (Markdown, HTML), images, and inline keyboards
- Free, no rate limits for reasonable usage (~30 msgs/sec to different chats)
- Group/channel support for broadcasting to multiple users

**Library options:**

| Library | Async | Protocol | Best For | Stars |
|---------|-------|----------|----------|-------|
| `python-telegram-bot` | Sync (primarily) | HTTP Bot API | Simple bots, beginners | 26k+ |
| `aiogram` | Fully async | HTTP Bot API | High-performance async bots | 5k+ |
| `Telethon` | Fully async | MTProto | Advanced/user-bot features | 10k+ |
| **Apprise** | Async | HTTP Bot API | Notification-only (our use case) | 14k+ |

**For our use case (one-way signal notifications):**
- Apprise is sufficient — we only need to *send* messages, not handle commands or conversations
- If we later want interactive features (e.g., `/status`, `/subscribe`, inline buttons), upgrade to `python-telegram-bot` or `aiogram`

**Setup:**
1. Create bot via @BotFather → get `BOT_TOKEN`
2. Get `CHAT_ID` (personal, group, or channel)
3. Apprise URL: `tgram://BOT_TOKEN/CHAT_ID`

**Message formatting for signals:**
```
🔻 BEARISH SMT DIVERGENCE
━━━━━━━━━━━━━━━━━━━━━━
Pair: BTC/USDT vs ETH/USDT
Timeframe: 4H
BTC: Higher High at $105,200
ETH: Lower High at $3,820
Detected: 2026-03-13 14:00 UTC
Invalidation: $105,500
━━━━━━━━━━━━━━━━━━━━━━
Confluence: Near 4H Order Block
```

---

### 2. Discord Webhook

**Why Discord:**
- Popular among crypto/trading communities
- Webhook = no bot hosting needed, just a URL
- Rich embeds with colors, fields, thumbnails
- Free, reliable delivery

**Library options:**

| Library | Async | Best For | Maintained |
|---------|-------|----------|------------|
| Raw `requests` | No | Quick one-liners | N/A |
| `discord-webhook` | Both | Dedicated webhook lib with embeds, rate limiting | Yes |
| `discord.py` | Yes | Full bot framework (overkill for webhooks) | Yes |
| **Apprise** | Yes | Unified notification (our use case) | Yes |

**For our use case:** Apprise covers Discord webhooks. If we need advanced embeds (colored sidebar, thumbnail charts, multiple fields), `discord-webhook` is the upgrade path.

**Setup:**
1. Server Settings → Integrations → Webhooks → New Webhook → Copy URL
2. Apprise URL: `discord://webhook_id/webhook_token`

**Advanced embeds (if needed later, via `discord-webhook`):**
```python
from discord_webhook import DiscordWebhook, DiscordEmbed

webhook = DiscordWebhook(url="https://discord.com/api/webhooks/...")
embed = DiscordEmbed(
    title="Bearish SMT Divergence",
    description="BTC/USDT vs ETH/USDT on 4H",
    color="FF0000",
)
embed.add_embed_field(name="BTC", value="Higher High: $105,200")
embed.add_embed_field(name="ETH", value="Lower High: $3,820")
embed.set_footer(text="Invalidation: $105,500")
webhook.add_embed(embed)
webhook.execute()
```

---

### 3. Email (SMTP)

**Why email:**
- Universal — everyone has email
- Good for daily/weekly signal summaries (not real-time alerts)
- HTML formatting for rich signal reports
- Archive/searchability

**Library options:**

| Library | Async | Best For |
|---------|-------|----------|
| `smtplib` (built-in) | No | Simple scripts, zero dependencies |
| `aiosmtplib` | Yes | Non-blocking async apps |
| `yagmail` | No | Quick Gmail integration |
| `Red Mail` | Yes | High-volume async sending |
| **Apprise** | Yes | Unified notification (our use case) |

**For our use case:** Apprise handles email via `mailto://` URLs. Supports Gmail, Outlook, Yahoo, and custom SMTP out of the box.

**Setup:**
- Apprise URL: `mailto://user:app_password@gmail.com`
- For custom SMTP: `mailtos://user:pass@smtp.example.com:587`

**Consideration:** Email is best as a **secondary** channel for summaries, not real-time alerts (delivery can be delayed, spam filters, etc.)

---

## Architecture Integration

```
┌──────────────────────────────────────┐
│          Signal Engine               │
│  Emits: DivergenceDetected event     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│      Notification Service            │
│                                      │
│  - Receives domain events            │
│  - Formats message per channel       │
│  - Delegates to Apprise              │
│                                      │
│  apprise.notify(                     │
│      body=format_signal(event),      │
│      title="Signal Alert",           │
│      tag=["telegram", "discord"]     │
│  )                                   │
└──────────────────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
 Telegram   Discord    Email
```

**Key design decisions:**
1. **Apprise as the notification adapter** — hides all channel-specific logic behind URL config
2. **Tag-based routing** — different signal types can go to different channels (e.g., critical signals → Telegram + Discord, daily summaries → email only)
3. **Message formatting layer** — a `SignalFormatter` that converts domain events into human-readable messages. Separate from delivery
4. **Configuration-driven** — adding/removing channels = editing a YAML file, no code changes

---

## Dependency Summary

| Package | Purpose | Install |
|---------|---------|---------|
| **`apprise`** | Unified notifications (Telegram, Discord, Email, 90+ services) | `pip install apprise` |
| `discord-webhook` | *Optional:* Advanced Discord embeds if needed | `pip install discord-webhook` |
| `python-telegram-bot` | *Optional:* Interactive Telegram bot features if needed | `pip install python-telegram-bot` |

**Minimum viable: just `apprise`.** Everything else is optional and only needed if we outgrow Apprise's built-in formatters.

---

## Sources

- [Apprise — GitHub](https://github.com/caronc/apprise)
- [Apprise — PyPI](https://pypi.org/project/apprise/)
- [How to Run Apprise in Docker — OneUptime](https://oneuptime.com/blog/post/2026-02-08-how-to-run-apprise-in-docker-for-multi-platform-notifications/view)
- [Send Notifications to 100+ Services — BrightCoding](https://www.blog.brightcoding.dev/2025/08/21/send-notifications-to-100+-services-with-a-simple-rest-api)
- [Apprise Notifications — Dagster Docs](https://docs.dagster.io/integrations/libraries/apprise)
- [python-telegram-bot vs aiogram vs Telethon — PipTrends](https://piptrends.com/compare/telethon-vs-python-telegram-bot-vs-aiogram)
- [python-telegram-bot vs aiogram — Restack](https://www.restack.io/p/best-telegram-bot-frameworks-ai-answer-python-telegram-bot-vs-aiogram-cat-ai)
- [Top 5 Python Telegram Bot Libraries 2025 — Valebyte](https://valebyte.com/blog/en/top-5-python-libraries-for-building-telegram-bots-on-your-vpsvds-in-2025/)
- [aiogram Official Site](https://aiogram.dev/)
- [python-discord-webhook — PyPI](https://pypi.org/project/discord-webhook/)
- [python-discord-webhook — GitHub](https://github.com/lovvskillz/python-discord-webhook)
- [Discord.py Webhook Guide — GitHub Gist](https://gist.github.com/izxxr/086a16bfd52b32b34a587b356bc32584)
- [Webhooking into Discord with Python — Medium](https://medium.com/pragmatic-programmers/webhooking-into-discord-with-python-8e9eb41a446c)
- [How to Use Discord Webhook with Python — PythonCentral](https://www.pythoncentral.io/how-to-use-discord-webhook-with-python-an-easy-to-use-guide/)
- [Email Notification Alerts with Python — Medium](https://medium.com/@wl8380/email-notification-alerts-with-python-automate-your-buy-sell-signals-5a6627f89a56)
- [Building a Real-Time Equity Price Alert System — Medium](https://medium.com/@wutainfofu/building-a-real-time-equity-price-alert-system-with-python-a-practical-guide-for-quantitative-c464515b0a7e)
- [Python Send Email Tutorial 2026 — Mailtrap](https://mailtrap.io/blog/python-send-email/)
- [Top 10 Python Libraries for Sending Email — AOTsend](https://www.aotsend.com/blog/p7558.html)
