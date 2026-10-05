import os
import sys
stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
if stdout_reconfigure is not None:
    stdout_reconfigure(encoding="utf-8")
import json
import urllib.parse
import requests
from dotenv import load_dotenv
from login_x import (
    login_session,
    load_credentials,
    perform_login
)

def get_graphql_headers():
    with open(login_session, 'r', encoding='utf-8') as f:
        d = json.load(f)
        cookies = {c['name']: c['value'] for c in d.get('cookies', [])}
    
    ct0 = cookies.get('ct0', '')
    load_dotenv()
    bearer_token = os.getenv('X_BEARER_TOKEN')
    
    headers = {
        'authorization': bearer_token,
        'x-csrf-token': ct0,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'en'
    }
    return headers, cookies

def check_if_following(username):
    print(f"\nChecking if @{username} is following you...")
    headers, cookies = get_graphql_headers()
    
    variables = {"screen_name": username, "withSafetyModeUserFields": True}
    features = {"hidden_profile_likes_enabled": True, "hidden_profile_subscriptions_enabled": True, "responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": False, "subscriptions_verification_info_is_identity_verified_enabled": True, "subscriptions_verification_info_verified_since_enabled": True, "highlights_tweets_tab_ui_enabled": True, "creator_subscriptions_tweet_preview_api_enabled": True, "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False, "responsive_web_graphql_timeline_navigation_enabled": True}
    
    url = f"https://x.com/i/api/graphql/Gb-d6r0vxPOADdG62OEBpQ/UserByScreenName?variables={urllib.parse.quote(json.dumps(variables))}&features={urllib.parse.quote(json.dumps(features))}"
    
    res = requests.get(url, headers=headers, cookies=cookies)
    if res.status_code != 200:
        print("Failed to get user profile. The session might be expired or the username is invalid.")
        return False
        
    data = res.json()
    try:
        user_result = data['data']['user']['result']
        
        # Look for followed_by in legacy or elsewhere
        legacy = user_result.get('legacy', {})
        print("Legacy keys available:", list(legacy.keys()))
        followed_by = legacy.get('followed_by', False)
        
        if followed_by:
            print(f"Yes, @{username} is FOLLOWING you.")
        else:
            print(f"No, @{username} is NOT following you.")
            
        return followed_by
    except (KeyError, TypeError):
        print("User not found.")
        return False

def main():
    credentials = load_credentials()

    username = input("\nEnter the X (Twitter) username to check (e.g. elonmusk): ").strip()
    if not username:
        print("No username provided. Exiting.")
        return

    needs_login = True
    if os.path.exists(login_session):
        try:
            headers, cookies = get_graphql_headers()
            variables = {"screen_name": "elonmusk", "withSafetyModeUserFields": True}
            features = {"hidden_profile_likes_enabled": True, "hidden_profile_subscriptions_enabled": True, "responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": False, "subscriptions_verification_info_is_identity_verified_enabled": True, "subscriptions_verification_info_verified_since_enabled": True, "highlights_tweets_tab_ui_enabled": True, "creator_subscriptions_tweet_preview_api_enabled": True, "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False, "responsive_web_graphql_timeline_navigation_enabled": True}
            url = f"https://x.com/i/api/graphql/Gb-d6r0vxPOADdG62OEBpQ/UserByScreenName?variables={urllib.parse.quote(json.dumps(variables))}&features={urllib.parse.quote(json.dumps(features))}"
            res = requests.get(url, headers=headers, cookies=cookies)
            if res.status_code == 200:
                needs_login = False
                print("Already logged in. Skipping login process.")
            else:
                print("Session invalid or expired. Proceeding to login...")
        except Exception as e:
            print("Session invalid or expired. Proceeding to login...")

    if needs_login:
        perform_login(credentials)

    check_if_following(username)
    print("\n--- Check complete ---")

if __name__ == "__main__":
    main()
