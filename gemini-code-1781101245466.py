import os
import sys
import requests
import base64
from playwright.sync_api import sync_playwright

# 1. Configuration & Security Checklist
TARGET_REPO = os.getenv("GITHUB_REPOSITORY") # Format: "username/repo-name"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SHOPIFY_URL = "https://apps.shopify.com/stories/new-and-notable"

if not TARGET_REPO or not GITHUB_TOKEN:
    print("[ERROR] Missing required environment variables: GITHUB_REPOSITORY or GITHUB_TOKEN.")
    sys.exit(1)

def fetch_current_pipeline():
    """Retrieves pipeline.md from GitHub or creates one if it doesn't exist."""
    url = f"https://api.github.com/repos/{TARGET_REPO}/contents/pipeline.md"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["sha"]
    return "# Target Pipeline\n\n", None

def commit_pipeline_update(new_content, sha=None):
    """Commits the freshly updated markdown back to GitHub."""
    url = f"https://api.github.com/repos/{TARGET_REPO}/contents/pipeline.md"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    payload = {
        "message": "automation: appended newly discovered marketplace micro-opps",
        "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
    }
    if sha:
        payload["sha"] = sha

    res = requests.put(url, headers=headers, json=payload)
    if res.status_code in [200, 201]:
        print("[SUCCESS] Successfully updated pipeline.md on GitHub.")
    else:
        print(f"[ERROR] GitHub Commit failed: {res.text}")

def scrape_marketplace():
    """Launches headless browser to scan apps matching solopreneur thresholds."""
    discovered_leads = []
    
    with sync_playwright() as p:
        # Launching with specific arguments to prevent bot blocks
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page()
        
        print(f"[INFO] Accessing Shopify Marketplace: {SHOPIFY_URL}")
        page.goto(SHOPIFY_URL, wait_until="networkidle")
        
        # Select individual app cards out of the listings grid
        cards = page.query_selector_all("div.yc-app-card, grid-item") # Adjusted for typical engine footprints
        
        for card in cards[:15]: # Scan the top 15 trending selections
            try:
                title_element = card.query_selector("h3, .app-title")
                review_element = card.query_selector(".review-count, span.text-sm")
                
                if not title_element:
                    continue
                    
                title = title_element.inner_text().strip()
                raw_reviews = review_element.inner_text() if review_element else "0"
                
                # Sanitize review figures down to absolute integers (e.g., "(45)" -> 45)
                review_count = int(''.join(filter(str.isdigit, raw_reviews))) if any(c.isdigit() for c in raw_reviews) else 0
                
                # CRITERIA FILTER: Active validate signaling, but not an entrenched incumbent
                if 5 <= review_count <= 150:
                    discovered_leads.append({
                        "title": title,
                        "reviews": review_count,
                        "link": SHOPIFY_URL
                    })
                    print(f"[VALIDATED TARGETFOUND] {title} ({review_count} reviews)")
            except Exception as e:
                continue
                
        browser.close()
    return discovered_leads

def main():
    print("[INFO] Initializing C2C Marketplace Scan Phase...")
    leads = scrape_marketplace()
    
    if not leads:
        print("[INFO] Scan complete. No unbundled targets matched safety criteria filters today.")
        sys.exit(0)
        
    current_markdown, sha = fetch_current_pipeline()
    
    # Construct update payload
    append_str = ""
    for lead in leads:
        append_str += f"## {lead['title']}\n"
        append_str += f"- **Source Platform:** Shopify App Store\n"
        append_str += f"- **Current Reviews:** {lead['reviews']}\n"
        append_str += f"- **Assigned Vehicle:** [Micro-SaaS | AI Service | Programmatic Asset]\n"
        append_str += f"- **Action Status:** [Cue]\n\n"
        
    updated_markdown = current_markdown + append_str
    commit_pipeline_update(updated_markdown, sha)
    
    print("[INFO] Session complete. Terminating container cleanly.")
    sys.exit(0) # Informs Railway process ended without errors

if __name__ == "__main__":
    main()