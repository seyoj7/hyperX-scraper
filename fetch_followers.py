import os
import json
import urllib.parse
import requests
from dotenv import load_dotenv

# Import the login session variable from the existing login_x module
from login_x import login_session

def get_v1_headers():
    """Load session cookies and create the headers needed for X's v1.1 API."""
    if not os.path.exists(login_session):
        print("Login session not found. Please run main.py first to log in.")
        return None, None
        
    with open(login_session, 'r', encoding='utf-8') as f:
        d = json.load(f)
        cookies = {c['name']: c['value'] for c in d.get('cookies', [])}
    
    ct0 = cookies.get('ct0', '')
    load_dotenv()
    bearer_token = os.getenv('X_BEARER_TOKEN')
    
    if not bearer_token:
        # Default fallback bearer token for X web client
        bearer_token = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
        
    headers = {
        'authorization': bearer_token,
        'x-csrf-token': ct0,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'x-twitter-active-user': 'yes'
    }
    return headers, cookies


def fetch_list_v1(username, list_type, headers, cookies, max_total=None, per_page=200):
    """
    Fetch the followers or following list for a given username using the v1.1 API
    with cursor-based pagination.
    
    list_type should be "Followers" or "Following".
    max_total: Maximum number of users to fetch. None = fetch all.
    per_page: Users per API request (max 200 for v1.1).
    """
    
    # Map to the correct v1.1 endpoint
    if list_type == "Followers":
        endpoint = "followers/list.json"
    elif list_type == "Following":
        # Twitter internally calls 'following' -> 'friends' in the v1.1 API
        endpoint = "friends/list.json"
    else:
        print("Invalid list type. Use 'Followers' or 'Following'.")
        return []

    # Clamp per_page to the API maximum of 200
    per_page = min(per_page, 200)

    extracted_users = []
    cursor = -1  # -1 is the starting cursor for the first page
    page = 0

    while cursor != 0:
        page += 1
        # If we have a max_total, only request what we still need
        request_count = per_page
        if max_total is not None:
            remaining = max_total - len(extracted_users)
            if remaining <= 0:
                break
            request_count = min(per_page, remaining)

        url = (
            f"https://api.twitter.com/1.1/{endpoint}"
            f"?screen_name={urllib.parse.quote(username)}"
            f"&count={request_count}"
            f"&cursor={cursor}"
        )
        
        res = requests.get(url, headers=headers, cookies=cookies)
        if res.status_code != 200:
            print(f"Failed to get {list_type} for @{username}. Status code: {res.status_code}")
            print(res.text)
            break

        data = res.json()
        
        try:
            users = data.get('users', [])
            if not users:
                break
            for u in users:
                extracted_users.append({
                    "screen_name": u.get('screen_name'),
                    "name": u.get('name'),
                    "description": u.get('description', '')
                })
            print(f"  Page {page}: fetched {len(users)} users (total so far: {len(extracted_users)})")
        except (KeyError, TypeError) as e:
            print(f"Error parsing response for {list_type}: {e}")
            break

        # Advance to the next page using the cursor
        cursor = data.get('next_cursor', 0)

        # Stop if we've reached our target
        if max_total is not None and len(extracted_users) >= max_total:
            break
        
    return extracted_users

def main():
    headers, cookies = get_v1_headers()
    if not headers:
        return
        
    username = input("\nEnter the X (Twitter) username to fetch followers/following for: ").strip()
    if not username:
        print("No username provided. Exiting.")
        return

    max_input = input("Max users to fetch per list (press Enter for all): ").strip()
    max_total = int(max_input) if max_input else None
    label = f"up to {max_total}" if max_total else "all"
        
    # Fetch Followers
    print(f"\nFetching {label} followers for @{username} using v1.1 API...")
    followers = fetch_list_v1(username, "Followers", headers, cookies, max_total=max_total)
    print(f"--- Retrieved {len(followers)} followers ---")
    for i, user in enumerate(followers, 1):
        print(f"[{i}] @{user['screen_name']} ({user['name']})")
        
    # Fetch Following
    print(f"\nFetching {label} following for @{username} using v1.1 API...")
    following = fetch_list_v1(username, "Following", headers, cookies, max_total=max_total)
    print(f"--- Retrieved {len(following)} following ---")
    for i, user in enumerate(following, 1):
        print(f"[{i}] @{user['screen_name']} ({user['name']})")

if __name__ == "__main__":
    main()
