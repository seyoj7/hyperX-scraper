import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
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
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'en'
    }
    return headers, cookies

def fetch_recent_tweet_links(username, count=5):
    print(f"\nFetching profile and recent tweets for @{username} via GraphQL...")
    headers, cookies = get_graphql_headers()
    
    variables = {"screen_name": username, "withSafetyModeUserFields": True}
    features = {"hidden_profile_likes_enabled": True, "hidden_profile_subscriptions_enabled": True, "responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": False, "subscriptions_verification_info_is_identity_verified_enabled": True, "subscriptions_verification_info_verified_since_enabled": True, "highlights_tweets_tab_ui_enabled": True, "creator_subscriptions_tweet_preview_api_enabled": True, "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False, "responsive_web_graphql_timeline_navigation_enabled": True}
    
    url = f"https://x.com/i/api/graphql/Gb-d6r0vxPOADdG62OEBpQ/UserByScreenName?variables={urllib.parse.quote(json.dumps(variables))}&features={urllib.parse.quote(json.dumps(features))}"
    
    res = requests.get(url, headers=headers, cookies=cookies)
    if res.status_code != 200:
        print("Failed to get user profile. The session might be expired or the username is invalid.")
        return []
        
    data = res.json()
    try:
        user_result = data['data']['user']['result']
        rest_id = user_result['rest_id']
        
        relationship_counts = user_result.get('relationship_counts', {})
        followers_count = relationship_counts.get('followers')
        following_count = relationship_counts.get('following')
        
        if followers_count is None and following_count is None:
            legacy = user_result.get('legacy', {})
            followers_count = legacy.get('followers_count', 0)
            following_count = legacy.get('friends_count', 0)
            
        print(f"Followers: {followers_count} | Following: {following_count}")
    except (KeyError, TypeError):
        print("User not found.")
        return []

    variables_tweets = {
        "userId": rest_id,
        "count": count,
        "includePromotedContent": True,
        "withQuickPromoteEligibilityTweetFields": True,
        "withVoice": True,
        "withV2Timeline": True
    }
    features_tweets = {
        "rweb_tipjar_consumption_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "communities_web_enable_tweet_community_results_fetch": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "articles_preview_enabled": True,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "creator_subscriptions_quote_tweet_preview_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "rweb_video_timestamps_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_enhance_cards_enabled": False
    }

    url_tweets = f"https://x.com/i/api/graphql/SXVCYB8XHSS25nzIljNtZA/UserTweets?variables={urllib.parse.quote(json.dumps(variables_tweets))}&features={urllib.parse.quote(json.dumps(features_tweets))}"
    
    res = requests.get(url_tweets, headers=headers, cookies=cookies)
    if res.status_code != 200:
        print("Failed to get tweets.")
        return []

    data = res.json()
    posts = []
    try:
        user_result = data['data']['user']['result']
        if 'timeline_v2' in user_result:
            instructions = user_result['timeline_v2']['timeline']['instructions']
        else:
            instructions = user_result['timeline']['timeline']['instructions']
            
        for inst in instructions:
            if inst['type'] == 'TimelineAddEntries':
                for entry in inst['entries']:
                    if entry['entryId'].startswith('tweet-'):
                        try:
                            itemContent = entry['content']['itemContent']
                            tweet_results = itemContent.get('tweet_results', {}).get('result', {})
                            
                            # Handle TweetWithVisibilityResults wrapper
                            if tweet_results.get('__typename') == 'TweetWithVisibilityResults':
                                tweet_results = tweet_results.get('tweet', {})
                                
                            t_rest_id = tweet_results.get('rest_id')
                            user_result = tweet_results.get('core', {}).get('user_results', {}).get('result', {})
                            
                            legacy = tweet_results.get('legacy', {})
                            screen_name = user_result.get('legacy', {}).get('screen_name')
                            if not screen_name:
                                screen_name = user_result.get('core', {}).get('screen_name')
                                
                            full_text = legacy.get('full_text', '')
                            
                            is_retweet = 'retweeted_status_result' in legacy or full_text.startswith('RT @')
                            if is_retweet and not full_text.startswith('[Retweet]'):
                                full_text = f"[Retweet] {full_text}"
                            
                            # Check for a quoted tweet link
                            quote_url = legacy.get('quoted_status_permalink', {}).get('expanded_url')
                            if not quote_url:
                                quoted_status = tweet_results.get('quoted_status_result', {}).get('result', {})
                                if quoted_status:
                                    q_rest_id = quoted_status.get('rest_id')
                                    q_screen_name = quoted_status.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {}).get('screen_name')
                                    if not q_screen_name:
                                        q_screen_name = quoted_status.get('core', {}).get('user_results', {}).get('result', {}).get('core', {}).get('screen_name')
                                    if q_rest_id and q_screen_name:
                                        quote_url = f"https://x.com/{q_screen_name}/status/{q_rest_id}"
                                        
                            if quote_url:
                                full_text += f"\n[Quoted: {quote_url}]"
                                
                            if t_rest_id and screen_name:
                                posts.append({
                                    "url": f"https://x.com/{screen_name}/status/{t_rest_id}",
                                    "text": full_text,
                                    "is_retweet": is_retweet
                                })
                        except (KeyError, TypeError):
                            continue
    except (KeyError, TypeError) as e:
        pass

    if posts:
        print(f"\nFound {len(posts)} tweet(s) in this single request:")
        for i, post in enumerate(posts, 1):
            print(f"\n[{i}] URL: {post['url']}")
            print(f"Text:\n{post['text']}")
    else:
        print("No tweets found.")
        
    return posts

def main():
    credentials = load_credentials()

    username = input("\nEnter the X (Twitter) username to visit (e.g. elonmusk): ").strip()
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

    tweet_links = fetch_recent_tweet_links(username, count=5)

    print("\n--- Scraping complete ---")
    if tweet_links:
        print(f"Collected {len(tweet_links)} tweet link(s) from @{username.lstrip('@')}.")

if __name__ == "__main__":
    main()