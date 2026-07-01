# Remove all subscriptions and alerts

Stop every dashboard subscription and alert on a Metabase instance from sending anything out, by removing them for good.

If you're self-hosted, you could try unsetting `MB_EMAIL_SMTP_HOST` and `MB_SLACK_APP_TOKEN` on the Metabase server so it has nowhere to send email or Slack messages. That stops delivery, but the subscriptions and alerts still run on schedule; they just fail silently instead of reaching anyone. This script removes them entirely, so they stop firing at all.

## This isn't reliably reversible

Running the script with `--execute` archives every dashboard subscription and alert on the instance. Archiving is the only "delete" Metabase supports for these resources through its API, but this script has no restore command, and the alert bulk-archive endpoint has no bulk-unarchive counterpart to reverse it with. Treat this as permanent, and only run it against an instance where that's what you actually want.

## Requirements

- Python 3
- `pip install requests`

## Set up the script

Open `clean_all_subs.py` and update these three values at the top for your instance:

```python
BASE_URL = "https://your-metabase-instance.example.com"
USERNAME = "your-admin-email@example.com"
PASSWORD = "your-admin-password"
```

The account needs to be an admin, since removing alerts uses an admin-only API endpoint.

If you'd rather authenticate with an API key than a username and password, remove the call to `authenticate()` in `main()` and set the header directly instead:

```python
SESSION.headers["X-API-Key"] = "<your-api-key>"
```

If you're self-hosting, unset `MB_EMAIL_SMTP_HOST` and `MB_SLACK_APP_TOKEN` on the Metabase server before you create test subscriptions and alerts, and they'll fail silently instead of emailing or messaging anyone. This only affects delivery - listing, archiving, and re-checking through the API all work the same either way. Handy if you want to try the script out safely before running it for real.

## Run it

Dry run (the default) shows what would be removed, without changing anything:

```
python clean_all_subs.py
```

Actually remove everything (asks you to type `yes` to confirm first):

```
python clean_all_subs.py --execute
```

## What it does

- Lists every active dashboard subscription and alert.
- Archives each dashboard subscription one at a time.
- Archives all alerts in a single bulk request.
- Checks again afterward to confirm nothing active is left.
