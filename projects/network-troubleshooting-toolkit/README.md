# Network Troubleshooting Toolkit

A small, beginner-friendly command-line tool for checking basic network connectivity on Windows, macOS, and Linux. It uses only Python's built-in modules, so there is nothing extra to install.

## What it can do

- Run a quick check for DNS, ping, and an HTTPS connection.
- Look up a hostname to see the IP addresses it resolves to.
- Ping a hostname or IP address.
- Test whether a hostname or IP accepts a TCP connection on a port, such as `443` for HTTPS.
- Display the computer name and its local IPv4 address.

The tool does not scan your network or change your settings. It contacts only the hostname/IP and port you enter, plus `example.com` and `1.1.1.1` when you choose Quick connection check. Use it on your own computer and networks you are allowed to troubleshoot. Some networks block ping, so a failed ping by itself does not mean the internet is unavailable.

## Run it on Windows

1. Download the portfolio ZIP from GitHub using **Code → Download ZIP**, then click **Extract All**.
2. Open the extracted folder, then open `projects\network-troubleshooting-toolkit`.
3. Click the File Explorer address bar, type `powershell`, and press **Enter**.
4. Type this command and press **Enter**:

   ```powershell
   py -3.14 .\network_toolkit.py
   ```

5. A menu appears. Type `1` for a quick check, or choose `2`, `3`, or `4` to test something specific.
6. When finished, type `5` and press **Enter**.

If PowerShell says `py` is not recognized, try:

```powershell
python .\network_toolkit.py
```

## Example: test a website connection

1. Start the tool and choose `4` (Test a TCP port).
2. For the hostname, enter `example.com`.
3. For the port, enter `443`.
4. A successful result means your computer could open a TCP connection to that site's HTTPS port. It does not test the whole website or your login.

## Results in simple words

- **DNS works:** your computer found an IP address for the hostname.
- **Ping replies:** a device replied to a basic network check. Some devices block ping.
- **TCP connection succeeded:** your computer reached the selected service port.
- **Could not connect:** the hostname, port, service, firewall, or network may be blocking the connection. Check the address and try another known service.

The checks are basic diagnostics, not a full internet speed test or automatic repair tool.

