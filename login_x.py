import os
import time
import random
import json
from dotenv import load_dotenv
from camoufox.sync_api import Camoufox

CURRENT_MOUSE_X = None
CURRENT_MOUSE_Y = None
login_session = "login_session.json"

def load_credentials():
    load_dotenv()
    return {
        "username": os.getenv("X_USERNAME"),
        "password": os.getenv("X_PASSWORD"),
        "email": os.getenv("X_EMAIL")
    }

def human_cursor(page, selector):
    global CURRENT_MOUSE_X, CURRENT_MOUSE_Y
    
    print(f"Looking for element: {selector}...")
    element = page.wait_for_selector(selector, state="visible")
    box = element.bounding_box()
    
    if not box:
        print("Could not find the position of the element.")
        return

    x = box["x"] + (box["width"] / 2) + random.uniform(-5, 5)
    y = box["y"] + (box["height"] / 2) + random.uniform(-5, 5)
    
    print(f"Moving mouse naturally to X: {x:.2f}, Y: {y:.2f}...")
    
    if CURRENT_MOUSE_X is None:
        CURRENT_MOUSE_X = random.randint(10, 500)
        CURRENT_MOUSE_Y = random.randint(10, 500)
        page.mouse.move(CURRENT_MOUSE_X, CURRENT_MOUSE_Y)
        
    start_x = CURRENT_MOUSE_X
    start_y = CURRENT_MOUSE_Y
    
    control_x = (start_x + x) / 2 + random.uniform(-100, 100)
    control_y = (start_y + y) / 2 + random.uniform(-100, 100)
    
    steps = random.randint(45, 75)
    for i in range(steps):
        t = i / steps
        ease_t = 1 - (1 - t) * (1 - t)
        
        curve_x = (1 - ease_t)**2 * start_x + 2 * (1 - ease_t) * ease_t * control_x + ease_t**2 * x
        curve_y = (1 - ease_t)**2 * start_y + 2 * (1 - ease_t) * ease_t * control_y + ease_t**2 * y
        
        page.mouse.move(curve_x, curve_y)
        time.sleep(random.uniform(0.002, 0.008))
        
    CURRENT_MOUSE_X = x
    CURRENT_MOUSE_Y = y
        
    time.sleep(random.uniform(0.2, 0.5))
    
    print("Clicking the element...")
    page.mouse.down()
    time.sleep(random.uniform(0.05, 0.15))
    page.mouse.up()
    
    element.focus()
    time.sleep(random.uniform(1.0, 2.0))

def human_type(page, text):
    print(f"Typing text naturally...")
    for char in text:
        page.keyboard.type(char)
        
        delay = random.uniform(0.10, 0.25)
        
        if random.random() < 0.10:
            delay += random.uniform(0.2, 0.5)
            
        time.sleep(delay)

def apply_anti_crash_script(page):
    page.add_init_script("""
        window.addEventListener('error', function(e) {
            e.stopImmediatePropagation();
        }, true);
        window.addEventListener('unhandledrejection', function(e) {
            e.stopImmediatePropagation();
        }, true);
    """)

def login_to_x(page, credentials):
    if "login" not in page.url and "onboarding" not in page.url:
        page.goto(
            "https://x.com/i/jf/onboarding/web?mode=login",
            wait_until="domcontentloaded",
            timeout=60000
        )
        print("URL:", page.url)
        time.sleep(5)

    human_cursor(page, 'input[name="username_or_email"]')
    if credentials["username"]:
        human_type(page, credentials["username"])
    else:
        print("Warning: X_USERNAME is not set in the .env file!")
        
    time.sleep(1)
    print("Pressing Enter to continue...")
    page.keyboard.press("Enter")
    
    time.sleep(3)
    human_cursor(page, 'input[name="password"]')
    if credentials["password"]:
        human_type(page, credentials["password"])
    else:
        print("Warning: X_PASSWORD is not set in the .env file!")

    print("Pressing Enter to continue...")
    page.keyboard.press("Enter")

    print("Waiting for login to complete...")
    try:
        page.wait_for_url("https://x.com/home", timeout=60000)
        print("Login successful!")
    except Exception as e:
        print(f"Wait for home page timed out or failed: {e}")

def check_login_status(page):
    if os.path.exists(login_session):
        print(f"Found {login_session}. Opening https://x.com/home ...")
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)
        if "login" not in page.url and "onboarding" not in page.url:
            print("Already logged in. Skipping login process.")
            return True
        print("Session invalid or expired. Proceeding to login...")
        return False
        
    print(f"No {login_session} found. Proceeding to login...")
    return False

def perform_login(credentials):
    with Camoufox(headless=False) as browser:
        context_kwargs = {"no_viewport": True}
        if os.path.exists(login_session):
            context_kwargs["storage_state"] = login_session

        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        apply_anti_crash_script(page)
        login_to_x(page, credentials)
        
        print(f"Saving login session to {login_session}...")
        state = context.storage_state()
        with open(login_session, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)
        print("Session saved successfully.")
        time.sleep(2)

