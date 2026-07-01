# Remove all subscriptions and alerts

A small script to bulk-remove every dashboard subscription and alert from a
Metabase instance.

## Warning: this is not reliably reversible

Running this with `--execute` archives every dashboard subscription and
alert on the instance. Archiving is Metabase's only "delete" for these
resources (there's no hard delete via the API), but there is no restore
button in this script, and the alert bulk-archive endpoint has no
corresponding bulk-unarchive action to reverse it with. Treat this as
permanent, and only run it against an instance where that's actually what
you want.

## Requirements

- Python 3
- `pip install requests`

## Setup

Open `clean_all_subs.py` and update these three values at the top for your
instance:

```python
BASE_URL = "https://your-metabase-instance.example.com"
USERNAME = "your-admin-email@example.com"
PASSWORD = "your-admin-password"
```

The account must be an admin, since removing alerts uses an admin-only API
endpoint.

If you'd rather use an API key than a username/password, remove the call to
`authenticate()` in `main()` and set it directly instead:

```python
SESSION.headers["X-API-Key"] = "<your-api-key>"
```

## Usage

Dry run (default) — shows what would be removed, without changing anything:

```
python clean_all_subs.py
```

Actually remove everything (asks for a `yes` confirmation first):

```
python clean_all_subs.py --execute
```

## What it does

- Lists all active dashboard subscriptions and alerts.
- Archives each dashboard subscription individually.
- Archives all alerts in a single bulk request.
- Re-checks afterward and confirms nothing active is left.

Removal here means archiving — Metabase doesn't support a hard delete for
either resource through its API.
