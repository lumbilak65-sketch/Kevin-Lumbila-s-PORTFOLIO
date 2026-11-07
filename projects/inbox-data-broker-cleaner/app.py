"""Local-only mailbox header scanner for the Inbox & Data Broker Cleaner demo."""
from contextlib import contextmanager
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from email.message import EmailMessage
from email.header import decode_header, make_header
import base64
from urllib.parse import parse_qs, unquote, urlparse
from html import unescape as html_unescape
import imaplib
import os
from pathlib import Path
import secrets
import sqlite3
import smtplib
import ssl
import re

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["DATABASE"] = os.environ.get("INBOX_CLEANER_DATABASE", str(ROOT / "instance" / "inbox_cleaner.sqlite3"))
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.metadata", "https://www.googleapis.com/auth/gmail.send"]
GMAIL_CREDENTIALS = None  # OAuth credentials live in memory only; restart to clear them.
UNSUBSCRIBE_ACTIONS = {}  # Only in memory; header URLs and addresses are never written to SQLite.
EMAIL_INSIGHTS = {}  # Short local summaries only; message previews are never persisted.


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
        columns = {row[1] for row in connection.execute("PRAGMA table_info(senders)")}
        if "unsubscribe_sent_at" not in columns:
            connection.execute("ALTER TABLE senders ADD COLUMN unsubscribe_sent_at TEXT")


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
    """Keep sender summaries and only cache unsubscribe actions in process memory."""
    senders = {}
    for key in [key for key in UNSUBSCRIBE_ACTIONS if key[0] == provider and key[1] == mailbox]:
        UNSUBSCRIBE_ACTIONS.pop(key, None)
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
        raw_action = str(header.get("List-Unsubscribe", ""))
        if raw_action:
            row["has_unsubscribe"] = True
            action = parse_unsubscribe_action(raw_action)
            if action:
                UNSUBSCRIBE_ACTIONS[(provider, mailbox, address)] = action
    return list(senders.values())


def parse_unsubscribe_action(value):
    """Extract safe HTTPS and mailto choices from a List-Unsubscribe header."""
    action = {}
    for candidate in re.findall(r"<([^<>]+)>", value):
        parsed = urlparse(candidate.strip())
        if parsed.scheme == "https" and parsed.hostname:
            action.setdefault("url", candidate.strip())
        elif parsed.scheme == "mailto" and parsed.path:
            recipient = unquote(parsed.path).strip()
            if re.fullmatch(r"[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+", recipient):
                params = parse_qs(parsed.query)
                subject = str(make_header(decode_header(params.get("subject", [""])[0]))).replace("\r", " ").replace("\n", " ")[:180]
                action["mailto"] = recipient
                action["subject"] = subject or "Unsubscribe request"
    return action or None


def save_scan(provider, mailbox, senders):
    with database() as connection:
        connection.executemany("""INSERT INTO senders
            (provider, mailbox, sender_name, sender_email, domain, message_count, has_unsubscribe, last_seen)
            VALUES (:provider, :mailbox, :sender_name, :sender_email, :domain, :message_count, :has_unsubscribe, :last_seen)
            ON CONFLICT(provider, mailbox, sender_email) DO UPDATE SET
            sender_name=excluded.sender_name, domain=excluded.domain, message_count=excluded.message_count,
            has_unsubscribe=excluded.has_unsubscribe, last_seen=excluded.last_seen""", senders)
        present = {row["sender_email"] for row in senders}
        if present:
            marks = ",".join("?" for _ in present)
            connection.execute(f"DELETE FROM senders WHERE provider=? AND mailbox=? AND sender_email NOT IN ({marks})", (provider, mailbox, *present))
        else:
            connection.execute("DELETE FROM senders WHERE provider=? AND mailbox=?", (provider, mailbox))


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
            metadataHeaders=["From", "Subject", "Date", "List-Unsubscribe"],
        ).execute()
        values = {h["name"].lower(): h["value"] for h in result.get("payload", {}).get("headers", [])}
        headers.append({"From": values.get("from", ""), "Subject": values.get("subject", ""),
                        "Date": values.get("date", ""), "Snippet": result.get("snippet", ""),
                        "List-Unsubscribe": values.get("list-unsubscribe", "")})
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
        recent_ids = data[0].split()[-limit:]
        for index, message_id in enumerate(recent_ids):
            status, parts = connection.fetch(message_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE LIST-UNSUBSCRIBE)])")
            if status != "OK":
                continue
            for part in parts:
                if isinstance(part, tuple):
                    parsed = BytesParser(policy=policy.default).parsebytes(part[1])
                    row = {"From": str(parsed.get("From", "")), "Subject": str(parsed.get("Subject", "")),
                           "Date": str(parsed.get("Date", "")), "Snippet": "",
                           "List-Unsubscribe": str(parsed.get("List-Unsubscribe", ""))}
                    if index >= max(0, len(recent_ids) - 30):
                        body_status, body_parts = connection.fetch(message_id, "(BODY.PEEK[TEXT]<0.4096>)")
                        if body_status == "OK":
                            row["Snippet"] = next((part[1].decode("utf-8", "replace") for part in body_parts if isinstance(part, tuple)), "")
                    headers.append(row)
    finally:
        try:
            connection.logout()
        except Exception:
            pass
    return headers


def build_email_insights(headers, provider, limit=30):
    """Make transparent, local rule-based summaries from subjects and short previews."""
    insights = []
    for header in headers[-limit:]:
        sender_name, sender_email = parseaddr(str(header.get("From", "")))
        subject = re.sub(r"\s+", " ", str(header.get("Subject", ""))).strip() or "(No subject)"
        preview = html_unescape(re.sub(r"<[^>]*>", " ", str(header.get("Snippet", ""))))
        preview = re.sub(r"\s+", " ", preview).strip()
        preview = preview[:340]
        text = f"{subject} {preview}".lower()
        renewal_terms = r"\b(renew(?:al)?|auto[ -]?renew|subscription|membership|expir(?:e|es|ed|ation|ing))\b"
        if re.search(renewal_terms, text) and re.search(r"\b(due|soon|expires?|expired|expiring|action|required|renew|by \w+|payment method)\b", text):
            category = "Renewal may need attention"
            summary = "This message mentions a renewal or expiration and may need action. Check the date and terms in the original email."
        elif re.search(renewal_terms, text):
            category = "Subscription or renewal information"
            summary = "This message appears to discuss a subscription, membership, or renewal. Check the original email for dates or required steps."
        elif re.search(r"\b(invoice|payment|bill|balance due|receipt|charged|billing)\b", text):
            category = "Payment or bill"
            summary = "This message appears to relate to a bill, payment, or charge. Verify it directly with the company before paying."
        elif re.search(r"\b(security|sign[ -]?in|password|verification|verify your account|suspicious|login alert)\b", text):
            category = "Account or security notice"
            summary = "This message appears to be an account or security notice. Open the service directly rather than using unexpected email links."
        elif re.search(r"\b(order|shipping|shipment|delivery|delivered|tracking)\b", text):
            category = "Order or delivery update"
            summary = "This message appears to contain an order, shipping, or delivery update."
        else:
            category = "General message"
            summary = "The subject and short preview do not clearly show a renewal or payment request. Open the original email to review it."
        insights.append({"provider": provider, "sender": sender_name.strip() or sender_email,
                         "sender_email": sender_email, "subject": subject,
                         "date": str(header.get("Date", "")), "category": category,
                         "summary": summary, "preview": preview})
    return insights


@app.route("/")
def dashboard():
    with database() as connection:
        senders = connection.execute("SELECT * FROM senders ORDER BY message_count DESC, sender_name COLLATE NOCASE").fetchall()
    stats = {"senders": len(senders), "messages": sum(row["message_count"] for row in senders), "unsubscribe": sum(bool(row["has_unsubscribe"]) for row in senders)}
    insights = [item for group in EMAIL_INSIGHTS.values() for item in group]
    insights.sort(key=lambda item: item.get("date", ""), reverse=True)
    return render_template("dashboard.html", senders=senders, stats=stats, gmail_connected=GMAIL_CREDENTIALS is not None, unsubscribe_actions=UNSUBSCRIBE_ACTIONS, email_insights=insights[:60])


def send_gmail_unsubscribe(mailbox, recipient, subject, body):
    service = gmail_service()
    message = EmailMessage()
    message["To"] = recipient
    message["From"] = mailbox
    message["Subject"] = subject
    message.set_content(body)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_icloud_unsubscribe(mailbox, app_password, recipient, subject, body):
    message = EmailMessage()
    message["To"] = recipient
    message["From"] = mailbox
    message["Subject"] = subject
    message.set_content(body)
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.mail.me.com", 587, timeout=20) as server:
        server.starttls(context=context)
        server.login(mailbox, app_password)
        server.send_message(message)


@app.route("/unsubscribe/<int:sender_id>", methods=["GET", "POST"])
def unsubscribe(sender_id):
    with database() as connection:
        sender = connection.execute("SELECT * FROM senders WHERE id=?", (sender_id,)).fetchone()
    if sender is None:
        abort(404)
    key = (sender["provider"], sender["mailbox"], sender["sender_email"])
    action = UNSUBSCRIBE_ACTIONS.get(key)
    if not action or not action.get("mailto"):
        flash("No email unsubscribe address is available. Rescan this mailbox, or use the listed unsubscribe page.", "error")
        return redirect(url_for("dashboard"))
    sent = bool(sender["unsubscribe_sent_at"])
    body = (f"Please unsubscribe {sender['mailbox']} from this mailing list. I am cancelling this subscription and request that no further marketing emails be sent to this address.\n\n"
            "If marketing emails continue after this request, I will keep a record and may report the issue to the appropriate consumer protection authority or seek legal advice.")
    if request.method == "POST":
        if sent:
            flash("An unsubscribe request was already sent for this sender.", "error")
            return redirect(url_for("dashboard"))
        if request.form.get("confirm_send") != "yes":
            flash("Check the confirmation box before sending.", "error")
            return redirect(url_for("unsubscribe", sender_id=sender_id))
        app_password = request.form.get("app_password", "").strip()
        try:
            if sender["provider"] == "Gmail":
                send_gmail_unsubscribe(sender["mailbox"], action["mailto"], action["subject"], body)
            elif sender["provider"] == "iCloud":
                if not app_password:
                    raise ValueError("Enter your Apple app-specific password to send.")
                send_icloud_unsubscribe(sender["mailbox"], app_password, action["mailto"], action["subject"], body)
            else:
                abort(400)
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            with database() as connection:
                connection.execute("UPDATE senders SET unsubscribe_sent_at=? WHERE id=?", (stamp, sender_id))
            flash("Your unsubscribe request was sent. Save this confirmation for your records.", "success")
        except Exception:
            flash("The request was not sent. Check your mailbox connection and credentials, then try again.", "error")
        finally:
            app_password = ""
        return redirect(url_for("dashboard"))
    return render_template("unsubscribe_review.html", sender=sender, action=action, body=body, sent=sent)


@app.route("/connect/gmail", methods=["POST"])
def connect_gmail():
    global GMAIL_CREDENTIALS
    credentials_file = ROOT / "credentials.json"
    if not credentials_file.is_file():
        flash("Gmail setup is unfinished. Add your Google OAuth Desktop credentials.json file to this folder; see the README.", "error")
        return redirect(url_for("dashboard"))
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes=GMAIL_SCOPES)
        GMAIL_CREDENTIALS = flow.run_local_server(port=0, open_browser=True, access_type="offline")
        service = gmail_service()
        mailbox = service.users().getProfile(userId="me").execute()["emailAddress"]
        headers = scan_gmail_headers(service)
        save_scan("Gmail", mailbox, normalize_sender_rows(headers, "Gmail", mailbox))
        EMAIL_INSIGHTS[("Gmail", mailbox)] = build_email_insights(headers, "Gmail")
        flash(f"Header scan finished for {mailbox}. No message bodies were read. Unsubscribe emails require your review and confirmation.", "success")
    except Exception:
        GMAIL_CREDENTIALS = None
        flash("Gmail connection did not finish. Check the OAuth setup and try again.", "error")
    return redirect(url_for("dashboard"))


@app.route("/scan/gmail", methods=["POST"])
def rescan_gmail():
    try:
        service = gmail_service()
        mailbox = service.users().getProfile(userId="me").execute()["emailAddress"]
        headers = scan_gmail_headers(service)
        save_scan("Gmail", mailbox, normalize_sender_rows(headers, "Gmail", mailbox))
        EMAIL_INSIGHTS[("Gmail", mailbox)] = build_email_insights(headers, "Gmail")
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
        EMAIL_INSIGHTS[("iCloud", mailbox)] = build_email_insights(headers, "iCloud")
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
    EMAIL_INSIGHTS.pop((provider, mailbox), None)
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
    EMAIL_INSIGHTS.clear()
    UNSUBSCRIBE_ACTIONS.clear()
    flash("All saved sender summaries were removed from this computer.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5050, debug=False)

