import requests
import json
import time

def fetch_and_validate_apps():
    
    url = "https://raw.githubusercontent.com/Loto-dev1/applifey-store/refs/heads/main/apps.json"
    
    fallback_apps = [
        ("Microsoft 365", "https://www.office.com"),
        ("iCloud", "https://www.icloud.com"),
        ("WhatsApp Web", "https://web.whatsapp.com")
    ]
    
    unique_url = f"{url}?nocache={int(time.time())}"
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache', 'Pragma': 'no-cache'
    }
    
    try:
        response = requests.get(unique_url, timeout=5, headers=browser_headers)
        if response.status_code == 200:
            raw_data = response.json()
            validated_apps = []
            for item in raw_data:
                if isinstance(item, dict) and "name" in item and "url" in item:
                    validated_apps.append((item["name"], item["url"]))
            return validated_apps
        return fallback_apps
    except:
        return fallback_apps
