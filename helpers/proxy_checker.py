# proxy_checker.py

import socket
import ssl
import json
import re
import pycountry
import time

IP_RESOLVER = "speed.cloudflare.com"
PATH_RESOLVER = "/meta"

def check(host, path, proxy):
    """Melakukan koneksi SSL ke host tertentu dan mengambil respons JSON."""
    start_time = time.time()  # Catat waktu mulai koneksi

    payload = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "User-Agent: Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240\r\n"
        "Connection: close\r\n\r\n"
    )

    ip = proxy.get("ip", host)
    port = int(proxy.get("port", 443))

    conn = None
    try:
        ctx = ssl.create_default_context()
        conn = socket.create_connection((ip, port), timeout=5)
        conn = ctx.wrap_socket(conn, server_hostname=host)

        conn.sendall(payload.encode())

        resp = b""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            resp += data

        resp = resp.decode("utf-8", errors="ignore")
        headers, body = resp.split("\r\n\r\n", 1)

        end_time = time.time()  # Catat waktu selesai koneksi
        connection_time = (end_time - start_time) * 1000  # Waktu koneksi dalam milidetik

        try:
            json_body = json.loads(body)
            http_protocol = json_body.get("httpProtocol", "Unknown")
            return json_body, http_protocol, connection_time
        except (json.JSONDecodeError, KeyError):
            error_message = f"Error parsing JSON dari {ip}:{port}"
            print(error_message)
            return {"error": error_message}, "Unknown", connection_time
    except (socket.error, ssl.SSLError) as e:
        error_message = f"Error koneksi dari {ip}:{port}: {e}"
        print(error_message)
        return {"error": error_message}, "Unknown", 0
    finally:
        if conn:
            conn.close()

    return {}, "Unknown", 0

def clean_org_name(org_name):
    return re.sub(r'[^a-zA-Z0-9\s]', '', org_name) if org_name else org_name

def get_country_info(alpha_2):
    try:
        country = pycountry.countries.get(alpha_2=alpha_2)
        if country:
            country_name = country.name
            country_flag = country.flag if hasattr(country, 'flag') else None # Cek jika flag ada.
            return country_name, country_flag
        else:
            return "Unknown", None
    except Exception:
        return "Unknown", None

def process_proxy(ip, port):
    proxy_data = {"ip": ip, "port": port}

    ori, ori_protocol, ori_connection_time = check(IP_RESOLVER, PATH_RESOLVER, {})
    pxy, pxy_protocol, pxy_connection_time = check(IP_RESOLVER, PATH_RESOLVER, proxy_data)

    if ori and not ori.get("error") and pxy and not pxy.get("error") and ori.get("clientIp") != pxy.get("clientIp"):
        org_name = clean_org_name(pxy.get("asOrganization"))
        proxy_country_code = pxy.get("country")
        proxy_asn = pxy.get("asn")

        proxy_country_code = proxy_country_code if proxy_country_code else "Unknown"
        proxy_asn = proxy_asn if proxy_asn else "Unknown"

        proxy_country_name, proxy_country_flag = get_country_info(proxy_country_code)

        result_message = f"Cloudflare Proxy Alive {ip}:{port}"
        print(result_message)

        return True, result_message, proxy_country_code, proxy_asn, proxy_country_name, proxy_country_flag, pxy_protocol, org_name, pxy_connection_time
    else:
        dead_message = f"Cloudflare  Proxy Dead!: {ip}:{port}"
        print(dead_message)
        return False, dead_message, "Unknown", "Unknown", "Unknown", None, "Unknown", "Unknown", 0
