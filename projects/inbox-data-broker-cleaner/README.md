# Inbox & Data Broker Cleaner

A local Python app for reviewing repeat email senders and unsubscribe options for **Gmail** and **iCloud Mail**. It runs on your computer; it is not hosted on GitHub Pages.

## What it does

- Scans up to 200 recent Inbox messages for sender and unsubscribe headers.
- Creates on-device, rule-based summaries for recent messages from email subjects and short previews. It flags possible renewals, bills, security notices, and delivery updates.
- Shows an unsubscribe link from the header when one is available. The link opens in a new browser tab; the app does not visit it automatically.
- For a `mailto:` unsubscribe option, shows the recipient, subject, and exact message before sending. You must check a confirmation box and press **Send unsubscribe request** for each sender.
- Stores sender summaries and a sent timestamp locally. Header URLs and unsubscribe email addresses stay in memory and are not stored in the database.
- Includes general guidance for handling data broker removal requests manually.

Email summaries use simple local pattern analysis, not an online generative AI service. Gmail provides a short message snippet with its metadata; iCloud previews read at most 4 KB of text for each of the 30 most recent messages. The preview and summary stay in memory and disappear when the app stops. The app does not save or send message previews to an AI provider. These summaries are clues, may be wrong or incomplete, and should not replace checking the original message.

The unsubscribe message is a firm request to stop marketing emails. It says continued messages may be reported or discussed with a legal adviser; it does not threaten a guaranteed lawsuit. Unsubscribe systems differ, and a sender may provide a web link instead of an email address. In the United States, the FTC says covered commercial senders must honor opt-out requests within 10 business days; this app cannot guarantee a sender's response.

Gmail credentials are held in memory and cleared when the app stops. The iCloud app-specific password is requested again only when sending and is not saved. The local report contains sender and mailbox addresses, so keep this folder private.

## Run locally on Windows

1. Download the portfolio ZIP from GitHub using **Code → Download ZIP**, then choose **Extract All**.
2. Open `projects\inbox-data-broker-cleaner` in the extracted folder.
3. Click File Explorer's address bar, type `powershell`, and press **Enter**.
4. Run these commands one at a time:

   ```powershell
   py -3.14 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe app.py
   ```

5. Leave PowerShell open and visit **http://127.0.0.1:5050** in Chrome.
6. When finished, press **Ctrl+C** in PowerShell. Gmail authorization must be repeated the next time the app starts.

## Gmail setup

Gmail uses `gmail.metadata` for headers/snippets and `gmail.send` to send only the unsubscribe request you confirm. Both are requested through Google OAuth. Google classifies metadata as a restricted scope and send as sensitive. For personal testing, configure an OAuth consent screen and add your Gmail address as a test user.

1. In the [Google Cloud Console](https://console.cloud.google.com/), select your project and enable Gmail API.
2. Under **Google Auth Platform → Data Access**, add `https://www.googleapis.com/auth/gmail.metadata` and `https://www.googleapis.com/auth/gmail.send`.
3. Under **Audience**, keep the app in testing and add the Gmail account you will use as a test user.
4. Keep the existing Desktop OAuth client and `credentials.json` in this project folder. No new client file is required just for the added scope.
5. Restart the app, click **Continue with Google**, and approve the updated permissions. If Google does not show the new permission, remove the app's existing access from your Google Account security settings, then reconnect.

Keep `credentials.json` private. It is excluded by `.gitignore`; do not upload it or share its contents. Google may show a warning for your own unverified test app. The app's local OAuth authorization is held in memory and ends when you stop the app.

Official instructions: [Gmail API Python quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python), [Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes), and [Gmail send API](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send).

## iCloud Mail setup

1. Enable two-factor authentication for your Apple Account and create an app-specific password.
2. Enter your iCloud address and app-specific password to scan. Never enter your regular Apple Account password.
3. When sending an unsubscribe email, enter the app-specific password again on the review page. It is not saved.

The app scans over read-only IMAP, then sends only after your confirmation using Apple's SMTP server. Official instructions: [app-specific passwords](https://support.apple.com/en-us/102654) and [iCloud Mail server settings](https://support.apple.com/en-us/102525).

## Local data and privacy

The database is `instance/inbox_cleaner.sqlite3`. It stores mailbox, sender name/address/domain, message count, whether the scan saw an unsubscribe header, scan time, and the local time an unsubscribe request was sent. It does not store subjects, message bodies, unsubscribe addresses, or unsubscribe URLs. Those header actions are held in memory until the app is stopped; after restarting, rescan the mailbox to restore action buttons. Use **Clear saved results** in the app to remove the report.

The app binds only to `127.0.0.1`. Do not expose it to the internet or use it as a shared service.

## Data broker requests

This demo does not search broker sites or submit removal requests. Visit each broker's official privacy page and record confirmations privately. See [FTC online privacy guidance](https://consumer.ftc.gov/articles/how-protect-your-privacy-online).

## Local checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

