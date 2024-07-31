from flask import Flask, request, jsonify
import requests
from requests.auth import HTTPProxyAuth

app = Flask(__name__)

def parse_proxy(proxy_string):
    parts = proxy_string.split(':')
    if len(parts) == 2:
        host = parts[0]
        port = int(parts[1])
        user = None
        password = None
    elif len(parts) == 4:
        host = parts[0]
        port = int(parts[1])
        user = parts[2]
        password = parts[3]
    else:
        raise ValueError("Invalid proxy format.")
    
    return host, port, user, password

def check_http_proxy_with_search(proxy_string, query):
    host, port, user, password = parse_proxy(proxy_string)
    test_url = "https://api.ipapi.is/"
    search_url = "https://www.google.com/search"
    params = {"q": query}
    
    if user and password:
        proxy_auth = f"{user}:{password}@"
    else:
        proxy_auth = ""
    
    proxies = {
        "http": f"http://{proxy_auth}{host}:{port}",
        "https": f"http://{proxy_auth}{host}:{port}"
    }
    auth = HTTPProxyAuth(user, password) if user and password else None

    try:
        # Check the proxy by making a request to ipinfo.io
        response = requests.get(test_url, proxies=proxies, auth=auth, timeout=10)
        if response.status_code == 200:
            ip = response.json().get('ip')
            proxy = response.json().get("company", {}).get("type", "unknown")
            if ip:

        
                # Perform the search to check for CAPTCHA trigger
                search_response = requests.get(search_url, params=params, proxies=proxies, auth=auth, timeout=10)
                if "captcha" in search_response.text.lower():
                    return {
                        "working": True,
                        "ip": ip,
                        "proxy": proxy,
                        "message": "Proxy triggers CAPTCHA."
                    }
                elif search_response.status_code == 200:
                    return {
                        "working": True,
                        "ip": ip,
                        "proxy_type": proxy,
                        "message": "Proxy does not trigger CAPTCHA."
                    }
                else:
                    return {
                        "working": False,
                        "ip": ip,
                        "proxy": proxy,
                        "message": f"Unexpected response status code: {search_response.status_code}"
                    }
            else:
                return {
                    "working": False,
                    "message": "Unable to retrieve IP details."
                }
        else:
            return {
                "working": False,
                "message": f"Unexpected response status code: {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        return {
            "working": False,
            "message": f"Request failed: {e}"
        }

def get_ip_details(ip):
    api_url = f"https://api.ipapi.is/{ip}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Unexpected response status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {e}"}

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    proxy_string = data.get('proxy')
    query = data.get('query')
    if not proxy_string or not query:
        return jsonify({"error": "Proxy string and query are required."}), 400
    
    result = check_http_proxy_with_search(proxy_string, query)
    return jsonify(result)

if __name__ == '__main__':
    app.run()
