"""Local-only mailbox header scanner for the Inbox & Data Broker Cleaner demo."""
from contextlib import contextmanager
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
import imaplib
import os
from pathlib import Path
import secrets
import sqlite3

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["DATABASE"] = os.environ.get("INBOX_CLEANER_DATABASE", str(ROOT / "instance" / "inbox_cleaner.sqlite3"))
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.metadata"
GMAIL_CREDENTIALS = None  # OAuth credentials live in memory only; restart to clear them.


@contextmanager
def database():
    path = Path(app.config["DATABASE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db():
    with database() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS senders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, provider TEXT NOT NULL, mailbox TEXT NOT NULL,
            sender_name TEXT NOT NULL, sender_email TEXT NOT NULL, domain TEXT NOT NULL,
            message_count INTEGER NOT NULL, has_unsubscribe INTEGER NOT NULL, last_seen TEXT NOT NULL,
            UNIQUE(provider, mailbox, sender_email))""")


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(24)
    return session["csrf_token"]


@app.before_request
def protect_post_forms():
    if request.method == "POST":
        expected = session.get("csrf_token")
        submitted = request.form.get("csrf_token", "")
        if not expected or not submitted or not secrets.compare_digest(submitted, expected):
            abort(400)


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": csrf_token}


def normalize_sender_rows(headers, provider, mailbox):
    """Keep sender metadata only; discard message bodies, subjects, and unsubscribe URLs."""
    senders = {}
    scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    for header in headers:
        name, address = parseaddr(str(header.get("From", "")))
        address = address.strip().lower()
        if "@" not in address:
            continue
        domain = address.rsplit("@", 1)[1]
        row = senders.setdefault(address, {
            "provider": provider, "mailbox": mailbox,
            "sender_name": name.strip() or domain, "sender_email": address,
            "domain": domain, "message_count": 0, "has_unsubscribe": False,
            "last_seen": scanned_at,
        })
        row["message_count"] += 1
        row["has_unsubscribe"] = row["has_unsubscribe"] or bool(header.get("List-Unsubscribe"))
    return list(senders.values())


def save_scan(provider, mailbox, senders):
    with database() as connection:
        connection.execute("DELETE FROM senders WHERE provider=? AND mailbox=?", (provider, mailbox))
        connection.executemany("""INSERT INTO senders
            (provider, mailbox, sender_name, sender_email, domain, message_count, has_unsubscribe, last_seen)
            VALUES (:provider, :mailbox, :sender_name, :sender_email, :domain, :message_count, :has_unsubscribe, :last_seen)""", senders)


def gmail_service():
    global GMAIL_CREDENTIALS
    if GMAIL_CREDENTIALS is None:
        raise RuntimeError("Connect Gmail first.")
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    if GMAIL_CREDENTIALS.expired and GMAIL_CREDENTIALS.refresh_token:
        GMAIL_CREDENTIALS.refresh(Request())
    return build("gmail", "v1", credentials=GMAIL_CREDENTIALS, cache_discovery=False)


def scan_gmail_headers(service, limit=200):
    messages = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=limit).execute().get("messages", [])
    headers = []
    for message in messages[:limit]:
        result = service.users().messages().get(
            userId="me", id=message["id"], format="metadata",
            metadataHeaders=["From", "List-Unsubscribe"],
        ).execute()
        values = {h["name"].lower(): h["value"] for h in result.get("payload", {}).get("headers", [])}
        headers.append({"From": values.get("from", ""), "List-Unsubscribe": values.get("list-unsubscribe", "")})
    return headers


def scan_icloud_headers(mailbox, app_password, limit=200):
    headers = []
    connection = imaplib.IMAP4_SSL("imap.mail.me.com", 993, timeout=20)
    try:
        connection.login(mailbox, app_password)
        status, _ = connection.select("INBOX", readonly=True)
        if status != "OK":
            raise RuntimeError("Could not open iCloud Inbox.")
        status, data = connection.search(None, "ALL")
        if status != "OK":
            raise RuntimeError("Could not list iCloud Inbox.")
        for message_id in data[0].split()[-limit:]:
            status, parts = connection.fetch(message_id, "(BODY.PEEK[HEADER.FIELDS (FROM LIST-UNSUBSCRIBE)])")
            if status != "OK":
                continue
            for part in parts:
                if isinstance(part, tuple):
                    parsed = BytesParser(policy=policy.default).parsebytes(part[1])
                    headers.append({"From": str(parsed.get("From", "")), "List-Unsubscribe": str(parsed.get("List-Unsubscribe", ""))})
    finally:
        try:
            connection.logout()
        except Exception:
            pass
    return headers


@app.route("/")
def dashboard():
    with database() as connection:
        senders = connection.execute("SELECT * FROM senders ORDER BY message_count DESC, sender_name COLLATE NOCASE").fetchall()
    stats = {"senders": len(senders), "messages": sum(row["message_count"] for row in senders), "unsubscribe": sum(bool(row["has_unsubscribe"]) for row in senders)}
    return render_template("dashboard.html", senders=senders, stats=stats, gmail_connected=GMAIL_CREDENTIALS is not None)


@app.route("/connect/gmail", methods=["POST"])
def connect_gmail():
    global GMAIL_CREDENTIALS
    credentials_file = ROOT / "credentials.json"
    if not credentials_file.is_file():
        flash("Gmail setup is unfinished. Add your Google OAuth Desktop credentials.json file to this folder; see the README.", "error")
        return redirect(url_for("dashboard"))
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes=[GMAIL_SCOPE])
        GMAIL_CREDENTIALS = flow.run_local_server(port=0, open_browser=True, access_type="offline")
        service = gmail_service()
        mailbox = service.users().getProfile(userId="me").execute()["emailAddress"]
        save_scan("Gmail", mailbox, normalize_sender_rows(scan_gmail_headers(service), "Gmail", mailbox))
        flash(f"Read-only header scan finished for {mailbox}. No message bodies were read.", "success")
    except Exception:
        GMAIL_CREDENTIALS = None
        flash("Gmail connection did not finish. Check the OAuth setup and try again.", "error")
    return redirect(url_for("dashboard"))


@app.route("/scan/gmail", methods=["POST"])
def rescan_gmail():
    try:
        service = gmail_service()
        mailbox = service.users().getProfile(userId="me").execute()["emailAddress"]
        save_scan("Gmail", mailbox, normalize_sender_rows(scan_gmail_headers(service), "Gmail", mailbox))
        flash(f"Gmail scan refreshed for {mailbox}.", "success")
    except Exception:
        flash("Could not refresh Gmail. Reconnect and try again.", "error")
    return redirect(url_for("dashboard"))


@app.route("/connect/icloud", methods=["POST"])
def connect_icloud():
    mailbox = request.form.get("mailbox", "").strip()
    app_password = request.form.get("app_password", "").strip()
    if not mailbox or not app_password or "@" not in mailbox:
        flash("Enter your iCloud email and Apple app-specific password.", "error")
        return redirect(url_for("dashboard"))
    try:
        headers = scan_icloud_headers(mailbox, app_password)
        save_scan("iCloud", mailbox, normalize_sender_rows(headers, "iCloud", mailbox))
        flash(f"Read-only header scan finished for {mailbox}. Your app-specific password was not saved.", "success")
    except Exception:
        flash("iCloud could not connect. Check the address, app-specific password, and two-factor authentication.", "error")
    finally:
        app_password = ""
    return redirect(url_for("dashboard"))


@app.route("/disconnect", methods=["POST"])
def disconnect():
    global GMAIL_CREDENTIALS
    provider, mailbox = request.form.get("provider", ""), request.form.get("mailbox", "")
    if provider not in {"Gmail", "iCloud"}:
        abort(400)
    with database() as connection:
        connection.execute("DELETE FROM senders WHERE provider=? AND mailbox=?", (provider, mailbox))
    if provider == "Gmail":
        GMAIL_CREDENTIALS = None
    flash(f"Removed saved {provider} scan results for {mailbox} from this computer.", "success")
    return redirect(url_for("dashboard"))


@app.route("/clear", methods=["POST"])
def clear_data():
    global GMAIL_CREDENTIALS
    with database() as connection:
        connection.execute("DELETE FROM senders")
    GMAIL_CREDENTIALS = None
    flash("All saved sender summaries were removed from this computer.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5050, debug=False)

