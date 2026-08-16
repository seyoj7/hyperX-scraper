import os
import json
import urllib.parse
import requests
from dotenv import load_dotenv

def test_fetch():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    session_file = os.path.join(script_dir, '..', 'login_session.json')
    env_file = os.path.join(script_dir, '..', '.env')
    
    if not os.path.exists(session_file):
        print(f"Error: {session_file} not found. Please log in first.")
        return

    with open(session_file, 'r', encoding='utf-8') as f:
        d = json.load(f)
        cookies = {c['name']: c['value'] for c in d.get('cookies', [])}
    
    ct0 = cookies.get('ct0', '')
    load_dotenv(env_file)
    bearer_token = os.getenv('X_BEARER_TOKEN')
    
    headers = {
        'authorization': bearer_token,
        'x-csrf-token': ct0,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'en'
    }

    # 2. Test UserByScreenName
    print("Testing UserByScreenName for @elonmusk")
    variables = {"screen_name": "elonmusk", "withSafetyModeUserFields": True}
    features = {"hidden_profile_likes_enabled": True, "hidden_profile_subscriptions_enabled": True, "responsive_web_graphql_exclude_directive_enabled": True, "verified_phone_label_enabled": False, "subscriptions_verification_info_is_identity_verified_enabled": True, "subscriptions_verification_info_verified_since_enabled": True, "highlights_tweets_tab_ui_enabled": True, "creator_subscriptions_tweet_preview_api_enabled": True, "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False, "responsive_web_graphql_timeline_navigation_enabled": True}
    
    url = f"https://x.com/i/api/graphql/Gb-d6r0vxPOADdG62OEBpQ/UserByScreenName?variables={urllib.parse.quote(json.dumps(variables))}&features={urllib.parse.quote(json.dumps(features))}"
    
    res = requests.get(url, headers=headers, cookies=cookies)
    if res.status_code != 200:
        print("Failed to fetch UserByScreenName:", res.status_code, res.text)
        return
        
    data = res.json()
    try:
        rest_id = data['data']['user']['result']['rest_id']
        print(f"Success! Found rest_id: {rest_id}\n")
    except KeyError:
        print("Failed to parse rest_id from response.", data)
        return

    # 3. Test UserTweets
    print("Testing UserTweets...")
    variables_tweets = {
        "userId": rest_id,
        "count": 5,
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
        print("Failed to fetch UserTweets:", res.status_code, res.text)
        return
        
    data = res.json()
    user_result = data['data']['user']['result']
    
    print("Keys in user result:", user_result.keys())
    
    if 'timeline_v2' in user_result:
        print("Schema uses 'timeline_v2'")
    elif 'timeline' in user_result:
        print("Schema uses 'timeline'")
    else:
        print("Unknown timeline schema!")
        
    dump_file = os.path.join(script_dir, '..', 'dump.json')
    with open(dump_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"\nDumped full GraphQL response to: {os.path.abspath(dump_file)}")
        
    print("\nFetch test completed successfully!")

if __name__ == '__main__':
    test_fetch()
