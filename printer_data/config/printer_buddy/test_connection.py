#!/usr/bin/env python3
import urllib.request
import urllib.error

try:
    print("Testing connection to http://localhost:8080...")
    response = urllib.request.urlopen("http://localhost:8080", timeout=5)
    print(f"Status: {response.status}")
    print(f"Headers: {dict(response.headers)}")
    content = response.read()
    print(f"Content length: {len(content)} bytes")
    if len(content) < 500:  # Show short content
        print(f"Content preview: {content[:200]}")
    else:
        print("Content is longer than 500 bytes (looks like HTML)")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
except urllib.error.URLError as e:
    print(f"URL Error: {e.reason}")
except Exception as e:
    print(f"Other Error: {e}")