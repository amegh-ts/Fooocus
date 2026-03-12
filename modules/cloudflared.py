import os
import subprocess
import time
import requests
import platform
import stat
from threading import Thread

def install_cloudflared():
    path = os.getcwd()
    if platform.system() == "Windows":
        file_name = "cloudflared.exe"
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    elif platform.system() == "Linux":
        file_name = "cloudflared"
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    elif platform.system() == "Darwin":
        file_name = "cloudflared"
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-universal"
    else:
        print(f"Unsupported OS: {platform.system()}")
        return None

    full_path = os.path.join(path, file_name)

    if not os.path.exists(full_path):
        print(f"Downloading {file_name} from {url} ...")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(full_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if platform.system() != "Windows":
                st = os.stat(full_path)
                os.chmod(full_path, st.st_mode | stat.S_IEXEC)
            print(f"Successfully downloaded {file_name}")
        else:
            print(f"Failed to download {file_name}. Status code: {response.status_code}")
            return None
    
    return full_path

def start_cloudflare_tunnel(port):
    cloudflared_path = install_cloudflared()
    if not cloudflared_path:
        return None

    print(f"Starting Cloudflare Tunnel on port {port} ...")
    
    # Use -tunnel --url because it's the quick tunnel command
    command = [cloudflared_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
    
    # Start the process and capture output to find the URL
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    url = None
    
    def monitor_output():
        nonlocal url
        for line in iter(process.stdout.readline, ""):
            if "trycloudflare.com" in line:
                # Example line: |  https://some-name.trycloudflare.com                      |
                parts = line.split()
                for part in parts:
                    if "trycloudflare.com" in part:
                        url = part
                        print(f"\nCloudflare Tunnel is live at: {url}\n")
                        break
            # print(line, end="") # Debug: print cloudflared output

    thread = Thread(target=monitor_output, daemon=True)
    thread.start()

    # Wait for URL to be found or process to exit
    start_time = time.time()
    while url is None and process.poll() is None:
        if time.time() - start_time > 30:
            print("Timeout waiting for Cloudflare Tunnel URL")
            break
        time.sleep(0.5)

    return url
