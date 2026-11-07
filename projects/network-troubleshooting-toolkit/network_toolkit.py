"""Beginner-friendly network checks using only Python's standard library."""
import ipaddress
import platform
import re
import socket
import subprocess
import sys


def read_host(prompt="Enter a hostname or IP address: "):
    host = input(prompt).strip()
    if not host or len(host) > 253 or host.startswith("-") or any(ch.isspace() for ch in host):
        raise ValueError("Enter one hostname or IP address, without spaces.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if not all(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                   for label in host.rstrip(".").split(".")):
            raise ValueError("That does not look like a valid hostname or IP address.")
    return host


def check_dns(host):
    try:
        results = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        addresses = sorted({result[4][0] for result in results})
        print(f"DNS works for {host}. Addresses: {', '.join(addresses)}")
        return True
    except socket.gaierror as error:
        print(f"DNS could not find {host}: {error}")
        return False


def check_ping(host):
    if platform.system().lower() == "windows":
        command = ["ping", "-n", "4", "-w", "2000", host]
    else:
        command = ["ping", "-c", "4", "-W", "2", host]
    try:
        result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=12, check=False)
        print(result.stdout.strip() or result.stderr.strip() or "Ping returned no details.")
        return result.returncode == 0
    except FileNotFoundError:
        print("The ping command is not available on this computer.")
        return False
    except subprocess.TimeoutExpired:
        print("Ping took too long and was stopped.")
        return False


def check_tcp(host, port):
    try:
        with socket.create_connection((host, port), timeout=5):
            print(f"Connection to {host} on port {port} succeeded.")
            return True
    except (OSError, socket.timeout) as error:
        print(f"Could not connect to {host} on port {port}: {error}")
        return False


def get_local_ip():
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("1.1.1.1", 53))
        return probe.getsockname()[0]
    except OSError:
        return "Not available"
    finally:
        probe.close()


def run_quick_check():
    print("\nQuick connection check")
    print(f"Computer: {socket.gethostname()}")
    print(f"Local IPv4 address: {get_local_ip()}")
    print("\n1) Looking up example.com:")
    dns_ok = check_dns("example.com")
    print("\n2) Pinging 1.1.1.1 (Cloudflare DNS):")
    ping_ok = check_ping("1.1.1.1")
    print("\n3) Connecting to example.com on port 443 (HTTPS):")
    tcp_ok = check_tcp("example.com", 443)
    print("\nSummary:")
    print(f"DNS: {'OK' if dns_ok else 'CHECK'} | Ping: {'OK' if ping_ok else 'CHECK'} | HTTPS: {'OK' if tcp_ok else 'CHECK'}")
    print("A failed ping alone does not prove the internet is down; some networks block ping.")


def main():
    while True:
        print("\nNETWORK TROUBLESHOOTING TOOLKIT")
        print("1. Quick connection check")
        print("2. Look up a hostname (DNS)")
        print("3. Ping a hostname or IP")
        print("4. Test a TCP port")
        print("5. Quit")
        choice = input("Choose 1-5: ").strip()

        try:
            if choice == "1":
                run_quick_check()
            elif choice == "2":
                check_dns(read_host())
            elif choice == "3":
                check_ping(read_host())
            elif choice == "4":
                host = read_host()
                port_text = input("Enter a port number (example: 443): ").strip()
                if not port_text.isdigit() or not 1 <= int(port_text) <= 65535:
                    raise ValueError("Port must be a number from 1 to 65535.")
                check_tcp(host, int(port_text))
            elif choice == "5":
                print("Goodbye.")
                return
            else:
                print("Please choose a number from 1 to 5.")
        except ValueError as error:
            print(error)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nStopped.")
        sys.exit(0)

