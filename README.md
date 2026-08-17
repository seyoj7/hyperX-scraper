# X-Scraper

X-Scraper is a Python-based scraping tool designed to extract tweets, profile data, and quoted tweets from X (formerly Twitter) without relying on the official developer API. 

## How It Bypasses X Protections (The "Nitter" Approach)

In the past, alternative frontends like Nitter relied heavily on Twitter's guest tokens to read data without logging in. After X aggressively blocked guest token access, scraping required a new approach.

This project bypasses X's API protections by **mimicking the official X Web Client**. It does this by leveraging the exact same internal GraphQL endpoints that the browser uses, rather than the restricted public developer API.

### Key Techniques Used:

1. **Internal GraphQL Endpoints:** Instead of hitting `api.twitter.com/2/...`, the scraper hits the undocumented `x.com/i/api/graphql/...` endpoints. These are the same endpoints the React-based web frontend uses, granting access to full timeline data, quote tweets, and threads.
2. **Web Client Authentication:** The script uses the official static Bearer Token assigned to the X web app, combined with a dynamic `x-csrf-token` (`ct0` cookie) and user session cookies.
3. **Feature Flags & Variables:** The script perfectly replicates the complex JSON payload of `variables` and `features` required by the GraphQL API. These flags inform X's backend that the request is originating from a fully-featured, official web client.
4. **Automated Session Handling:** By maintaining a valid session state (`login_x.py`), the scraper avoids the strict rate-limits and blocks imposed on unauthenticated (guest) requests.

## Prerequisites

- Python 3.x
- `requests`
- `python-dotenv`

## Installation

1. Clone or download the repository.
2. Install the required Python packages:
   ```bash
   pip install requests python-dotenv
   ```
3. Set up your `.env` file with the official Web Client Bearer Token:
   ```env
   X_BEARER_TOKEN="Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
   ```
   *(Note: This specific Bearer Token is a well-known constant used globally by the X Web Client).*

## Usage

Run the main script:

```bash
python main.py
```

1. **Authentication:** On the first run, the script will execute the login flow (via `login_x.py`) to generate a valid session and save your cookies.
2. **Scraping:** You will be prompted to enter a target X username (e.g., `elonmusk`).
3. **Data Extraction:** The script will fetch the user's latest tweets, parse the GraphQL response, and print the tweet content, URLs, and any quoted tweets perfectly formatted to your console.

## Disclaimer
This tool is for educational purposes. Scraping X is against their Terms of Service. Use at your own risk.