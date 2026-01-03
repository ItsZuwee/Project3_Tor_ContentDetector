import requests

proxies = {
    "http": "socks5h://127.0.0.1:9150",
    "https": "socks5h://127.0.0.1:9150",
}

r = requests.get(
    "https://check.torproject.org/api/ip",
    proxies=proxies,
    timeout=30
)

print(r.status_code)
print(r.text)
