# cbs-bot

Discord bot that reads [CluesBySam](https://cluesbysam.com/) score shares (messages containing `#CluesBySam`), parses date, difficulty, time, and the emoji grid, then appends a row to your **existing** Google Sheet (**columns A–F**: Day, Name, Difficulty, Time, Perfect?, Hints?).

## Behavior

- Messages **without** `#CluesBySam` are ignored.
- On **success** (parsed and appended): reacts with a checkmark on the message.
- On **parse or Sheets failure**: posts a short error in a **thread** on that message (or replies if a thread cannot be created).

## Setup

### 1. Python and dependencies

Use [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

### 2. Discord application

1. Create an application and bot at the [Discord Developer Portal](https://discord.com/developers/applications).
2. Under **Bot**, enable **Message Content Intent** (required to read message text in servers).
3. Invite the bot with permissions: **Read Messages/View Channels**, **Send Messages**, **Add Reactions**, **Create Public Threads**, **Send Messages in Threads** (adjust to your server’s needs).
4. Copy the bot token into `.env` as `DISCORD_TOKEN`.

### 3. Google Cloud / Sheets

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project (or pick one).
2. Enable **Google Sheets API** (and **Google Drive API** if gspread requests it for opening the file).
3. Create a **service account**, then create and download a **JSON key**.
4. Set `GOOGLE_APPLICATION_CREDENTIALS` in `.env` to the **absolute path** of that JSON file.
5. Open your spreadsheet → **Share** → add the service account’s **client email** (from the JSON, `client_email`) with **Editor** access.
6. Set `SPREADSHEET_ID` to the ID in the sheet URL (`/d/<id>/edit`).

### 4. Environment

```bash
cp .env.example .env
# Edit .env with real values
```

Optional: `ALLOWED_CHANNEL_IDS` — comma-separated channel IDs; if set, the bot only processes messages in those channels.

**Discord-only test (no Google Sheets):** set `CBSC_SHEETS_DRY_RUN=1` (or `SHEETS_DRY_RUN=1`). The bot still parses messages and reacts with a checkmark on success, but prints the **raw message** and **parsed row** to the terminal instead of calling Sheets.

### 5. Run

```bash
uv run python main.py
```

## Sheet format

- The bot appends **six** values only: **A–F**. Column **G** and anything to the right are left untouched on that row.
- **Difficulty** is written as `Easy`, `Medium`, `Hard`, `Tricky`, or `Evil`.
- **Perfect?** and **Hints?** are exactly `Yes` or `No` (to match typical dropdown validation).
- **Perfect** means every grid cell is a green square (🟩). **Hints** means any **circle** clue tile in the grid (e.g. 🟠, 🟡), not yellow/green **squares**.

Extend your Sheet **data validation** ranges down the column if you append rows below pre-formatted cells.

## Project layout

| File | Role |
|------|------|
| `main.py` | Loads `.env`, logging, starts the bot |
| `bot.py` | Discord `on_message`, reactions, thread errors |
| `cbs_parser.py` | Parse share text → row fields (no Discord) |
| `sheets_client.py` | gspread append to sheet |

## Tests

```bash
uv run pytest
```
