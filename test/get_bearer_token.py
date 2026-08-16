from playwright.sync_api import sync_playwright
import time

def fetch_bearer_token():
    print("Launching headless browser to intercept X (Twitter) network traffic...")
    
    bearer_token = None
    
    def intercept_request(request):
        nonlocal bearer_token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer AAAAAAAAAAAAAAAAAAAA"):
            if not bearer_token:
                bearer_token = auth_header

    try:
        with sync_playwright() as p:
            # We use standard playwright to avoid any Camoufox viewport bugs
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Listen to all network requests
            page.on("request", intercept_request)
            
            print("Navigating to https://x.com/ ...")
            page.goto("https://x.com/", wait_until="networkidle")
            
            for _ in range(10):
                if bearer_token:
                    break
                time.sleep(0.5)
                
            browser.close()
            
    except Exception as e:
        print(f"Error during browser session: {e}")

    if bearer_token:
        print("\n--- Successfully Extracted Bearer Token ---")
        print(bearer_token)
        print("-------------------------------------------\n")
    else:
        print("Could not find the Bearer token in the network traffic.")

if __name__ == '__main__':
    fetch_bearer_token()