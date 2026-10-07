import os
import sys

stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
if stdout_reconfigure is not None:
    stdout_reconfigure(encoding="utf-8")

import json
import requests
from dotenv import load_dotenv
from login_x import login_session, load_credentials, perform_login

API_URL = "https://x.com/i/api/1.1/friendships/show.json"
DEFAULT_SOURCE_USERNAME = "elonmusk"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def load_saved_cookies():
    with open(login_session, "r", encoding="utf-8") as session_file:
        session_data = json.load(session_file)
    return {
        cookie["name"]: cookie["value"]
        for cookie in session_data.get("cookies", [])
        if "name" in cookie and "value" in cookie
    }


def get_request_headers(cookies):
    load_dotenv()
    token = (os.getenv("X_BEARER_TOKEN") or "").strip()
    if not token:
        raise ValueError("X_BEARER_TOKEN is missing from the environment.")

    if token.lower().startswith("bearer "):
        authorization = token
    else:
        authorization = f"Bearer {token}"

    csrf_token = cookies.get("ct0", "")
    if not csrf_token:
        raise ValueError("The saved session does not contain a ct0 cookie.")

    return {
        "authorization": authorization,
        "x-csrf-token": csrf_token,
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-active-user": "yes",
        "user-agent": USER_AGENT,
    }


def check_if_following(source_username, target_username):
    try:
        cookies = load_saved_cookies()
        headers = get_request_headers(cookies)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Could not load the saved X session: {error}")
        return None

    try:
        response = requests.get(
            API_URL,
            params={
                "source_screen_name": source_username,
                "target_screen_name": target_username,
            },
            headers=headers,
            cookies=cookies,
            timeout=30,
        )
    except requests.RequestException as error:
        print(f"Request to X failed: {error}")
        return None

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        message = "X rate limited this request (HTTP 429)."
        if retry_after:
            message += f" Retry after {retry_after} seconds."
        print(message)
        return None
    if response.status_code in (401, 403):
        print(
            f"X rejected the saved session (HTTP {response.status_code}). "
            "The session may have expired or lack access."
        )
        return None
    if response.status_code != 200:
        details = response.text.strip().replace("\n", " ")[:500]
        print(f"X returned HTTP {response.status_code} while checking the relationship.")
        if details:
            print(f"Response: {details}")
        return None

    try:
        data = response.json()
        is_following = data["relationship"]["source"]["following"]
    except (ValueError, KeyError, TypeError):
        print("X returned an unexpected response; the follow status was not available.")
        return None

    if is_following:
        print(f"Yes, @{source_username} follows @{target_username}.")
    else:
        print(f"No, @{source_username} does not follow @{target_username}.")
    return bool(is_following)


def main():
    if not os.path.exists(login_session):
        print("No saved X login session was found. Starting login...")
        try:
            perform_login(load_credentials())
        except Exception as error:
            print(f"Login failed: {error}")
            return

        if not os.path.exists(login_session):
            print("Login finished, but no saved session file was created.")
            return

    target_username = input("Enter your X username (the target): ").strip().lstrip("@")
    if not target_username:
        print("No target username provided. Exiting.")
        return

    source_username = input(
        f"Enter the account to check (source, default {DEFAULT_SOURCE_USERNAME}): "
    ).strip().lstrip("@")
    if not source_username:
        source_username = DEFAULT_SOURCE_USERNAME

    check_if_following(source_username, target_username)
    print("\n--- Check complete ---")


if __name__ == "__main__":
    main()
