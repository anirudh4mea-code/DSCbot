# Prop Firm Giveaway Tracker

Checks your Discord trading servers' giveaway channels at **9:00 AM and 9:00 PM IST** and sends each **new** prop-firm giveaway to a private Discord channel. Nothing is sent twice: a giveaway is skipped if its message was already alerted, or if the same text was already seen from another server.

## How it works

```
Trading servers' #giveaways (Announcement channels)
        │  Discord "Follow" (built-in, copies each post)
        ▼
Your private hub server  ──►  bot reads it (GitHub Actions, 2×/day)
                                   │ keyword filter + dedupe
                                   ▼
                     #giveaway-alerts (webhook) → your phone
```

Reading servers through your own account token is against Discord's rules and can get your account banned. Following channels into a server you own avoids that.

## One-time setup (about 15 minutes)

1. **Hub server:** In Discord, create a private server (for example "Giveaway Hub").
   - Create a `#giveaway-alerts` channel. Open Edit Channel → Integrations → Webhooks → New Webhook, then **copy the URL**.
   - Optional: make a category such as `feeds` for the followed channels.
2. **Follow each giveaway channel:** In every trading server, open its giveaways or announcements channel and click **Follow** (at the top or bottom of the channel). Choose your hub server and a feed channel there.
   - No Follow button means the channel isn't an Announcement channel, so its posts can't be copied. You can ask that server's mods to make it one, or to add your bot.
3. **Bot:** Go to <https://discord.com/developers/applications>, create a New Application, then open **Bot**.
   - Click **Reset Token** and copy the token.
   - Turn on **Message Content Intent**.
   - Under OAuth2 → URL Generator, choose scope `bot` with permissions **View Channels** and **Read Message History**. Open the URL and add the bot to **your hub server only**.
4. **Hub server ID:** Turn on Discord Settings → Advanced → Developer Mode. Then right-click the hub server → **Copy Server ID**.
5. **GitHub secrets:** In the repo, go to Settings → Secrets and variables → Actions → New repository secret, and add:
   - `DISCORD_BOT_TOKEN`
   - `DISCORD_HUB_GUILD_ID`
   - `DISCORD_ALERT_WEBHOOK_URL`
6. **Go live:** Merge this into `main`, because GitHub only runs schedules from the default branch. Then open Actions → *Prop firm giveaway tracker* → **Run workflow** to test.

## Tuning (`config.json`)

| Key | What it does |
|---|---|
| `channels` | Hub channel IDs to read. Leave empty to read every text or announcement channel in the hub. Exclude `#giveaway-alerts` by listing feed channels explicitly if alerts get re-detected. |
| `include_all_channels` | Channel IDs where every post counts as a giveaway, with no keyword check. |
| `score_threshold` | Higher means stricter. Each keyword adds its weight, and a known prop firm name adds `prop_firm_weight`. |
| `giveaway_keywords`, `prop_firms` | Edit freely. |
| `send_empty_summary` | `true` sends "No new giveaways" when a run finds nothing. |
| `first_run_lookback_hours` | How far back the very first run looks. |

## Local test

```bash
pip install -r requirements.txt
python -m pytest tests
python tracker.py --dry-run --fixture tests/fixtures/messages.json
```

## Notes

- GitHub can start scheduled runs about 5–15 minutes late.
- `state/seen.json` is committed after each run. It is the "already sent" memory. Delete its contents to start over.
- X/Twitter isn't included yet, because the X API is paid. It can be added later as another source that feeds the same filter and dedupe.
