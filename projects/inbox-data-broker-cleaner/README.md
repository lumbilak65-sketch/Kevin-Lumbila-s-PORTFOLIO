# Inbox & Data Broker Cleaner

A local Python app for reviewing repeat email senders and unsubscribe availability. It can connect to **Gmail** and **iCloud Mail**. It runs on your computer; it is not hosted on GitHub Pages.

## What it does

- Connects to Gmail with Google's authorization window, or to iCloud Mail with an Apple app-specific password.
- Checks up to 200 recent Inbox messages for the `From` and `List-Unsubscribe` headers.
- Shows repeat senders and a link back to the provider's inbox so you can review and unsubscribe yourself.
- Stores a small sender summary in a local SQLite file.
- Includes general guidance for handling data broker removal requests manually.

It does **not** read message bodies or subjects, save the unsubscribe link/token, send unsubscribe messages, contact data brokers, or upload your mailbox data. Gmail OAuth credentials are held in memory only and are cleared when the app stops. The iCloud app-specific password is not written to the database or a file. The report contains personal sender and mailbox addresses, so keep the project folder private.

## Run locally on Windows

1. Download the portfolio repository ZIP from GitHub using **Code → Download ZIP**, then use **Extract All**.
2. Open the extracted folder, then open `projects\inbox-data-broker-cleaner`.
3. Click File Explorer's address bar, type `powershell`, and press **Enter**.
4. Run these commands one at a time:

   ```powershell
   py -3.14 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe app.py
   ```

5. Leave PowerShell open and visit **http://127.0.0.1:5050** in Chrome.
6. When finished, press **Ctrl+C** in PowerShell. Gmail authorization must be repeated the next time the app starts.

## Set up Gmail

This app uses Google's OAuth flow and requests only the Gmail `gmail.metadata` scope. This scope can access message metadata and headers, not message bodies. Google classifies it as a restricted scope; for personal testing, configure an OAuth consent screen and add your own Google account as a test user.

1. In the [Google Cloud Console](https://console.cloud.google.com/), create or select a project and enable the Gmail API.
2. Configure the OAuth consent screen. If prompted for an audience, select **External** and add your Gmail address as a test user.
3. Create an OAuth client ID with application type **Desktop app**.
4. Download its JSON file. Put it in this project folder and rename it to `credentials.json`.
5. Start the app, click **Continue with Google**, and approve the requested metadata-only access.

Keep `credentials.json` private. It is excluded by this folder's `.gitignore`; never upload it or paste its contents into chat. Google may show a warning for your own unverified test app.

Official Google instructions: [Gmail API Python quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python) and [Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes).

## Set up iCloud Mail

1. Make sure two-factor authentication is enabled for your Apple Account.
2. Create an **app-specific password** in your Apple Account settings.
3. In the local app, enter your full iCloud email and that app-specific password, then select **Scan iCloud inbox**.
4. Do not enter your normal Apple Account password.

The app uses Apple's iCloud IMAP server over SSL and selects the Inbox in read-only mode. The app-specific password is used for the scan and is not saved. Apple instructions: [app-specific passwords](https://support.apple.com/en-us/102654) and [iCloud Mail server settings](https://support.apple.com/en-us/102525).

## Local data and privacy

The report database is `instance/inbox_cleaner.sqlite3` inside this folder. It stores mailbox address, sender name/address/domain, message count, whether an unsubscribe header was present, and scan time. It does not store subjects, message bodies, or unsubscribe URLs. Use **Clear saved results** in the app to remove the report, or stop the app and delete that database file.

The app binds only to `127.0.0.1` and is intended for your computer. Do not expose it to the internet or use it as a shared service. Unsubscribe and data removal actions stay under your control.

## Data broker requests

This demo does not search data broker sites or submit requests. Visit each broker's official privacy page, follow its current removal steps, and record confirmations privately. The app links to [FTC online privacy guidance](https://consumer.ftc.gov/articles/how-protect-your-privacy-online).

## Run the local checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Four local checks cover the dashboard, header-only sender summaries, not saving the iCloud password, and rejecting form submissions without a valid CSRF token. The checks use sample data; they do not sign in to a real mailbox.