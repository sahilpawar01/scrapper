import requests
import re
import time

GITHUB_TOKEN = "" #input your github token here
headers = {"Accept": "application/vnd.github+json", "Authorization": f"token {GITHUB_TOKEN}" if GITHUB_TOKEN else None}
API_KEY_PATTERN = re.compile(r'(["\'])?(sk-[a-zA-Z0-9]{20,})\1|(["\'])?(sk-ant-[a-zA-Z0-9]{20,})\3|(["\'])?(dsk-[a-zA-Z0-9]{20,})\5')

OUTPUT_FILE = "api_keys.txt"
MAX_KEYS = 5 #input as many as you want

def search_github(query, page=1):
    url = "https://api.github.com/search/code"
    params = {"q": query, "per_page": 100, "page": page}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        print("Rate limit exceeded. Waiting 60 seconds...")
        time.sleep(60)
        return search_github(query, page)
    elif response.status_code == 422:
        print(f"Query parsing error: {response.text}")
        return None
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def extract_keys_from_file(file_url):
    raw_response = requests.get(file_url)
    if raw_response.status_code == 200:
        content = raw_response.text
        keys = API_KEY_PATTERN.findall(content)
        return keys if keys else None
    return None

def save_keys_to_file(keys):
    with open(OUTPUT_FILE, "w") as f:
        for key in keys:
            f.write(f'API_KEY = "{key}"\n')
    print(f"Saved {len(keys)} unique keys to {OUTPUT_FILE}")

def main():
    query = '"API_KEY"'
    page = 1
    found_keys = set()
    print(f"Searching GitHub for up to {MAX_KEYS} unique API keys with query: {query}...")
    while len(found_keys) < MAX_KEYS:
        result = search_github(query, page)
        if not result or "items" not in result or len(result["items"]) == 0:
            print("No more results found.")
            break
        for item in result["items"]:
            repo_name = item["repository"]["full_name"]
            file_path = item["path"]
            raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            print(f"Checking {repo_name}/{file_path}...")
            keys = extract_keys_from_file(raw_url)
            if keys:
                print(f"Found keys in {repo_name}/{file_path}: {keys}")
                found_keys.update(keys)
            if len(found_keys) >= MAX_KEYS:
                break
        page += 1
        time.sleep(1)
    if found_keys:
        save_keys_to_file(found_keys)
        print(f"\nFound and saved {len(found_keys)} unique keys.")
    else:
        print("No API keys found matching the pattern.")

if __name__ == "__main__":
    main()