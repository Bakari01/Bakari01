#!/usr/bin/env python3
"""
Simple README updater:
- Inserts latest blog post from BLOG_RSS (if provided)
- Inserts recent GitHub events for the user in RECENT_ACTIVITY section
"""

import os
import re
import sys
import requests
import feedparser
from datetime import datetime

GITHUB_USER = os.environ.get("GITHUB_USER", "Bakari01")
BLOG_RSS = os.environ.get("BLOG_RSS")

README = "README.md"

def fetch_latest_blog(rss_url):
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            e = feed.entries[0]
            title = e.get("title", "Untitled")
            link = e.get("link", "")
            published = e.get("published", "") or e.get("updated", "")
            return {"title": title, "link": link, "published": published}
    except Exception as ex:
        print("Blog fetch error:", ex)
    return None

def fetch_recent_activity(user, token=None, per_page=5):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/users/{user}/events/public?per_page={per_page}"
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code == 200:
        events = r.json()
        items = []
        for ev in events[:per_page]:
            t = ev.get("type", "Event")
            repo = ev.get("repo", {}).get("name", "")
            created = ev.get("created_at", "")
            created_dt = created and created.split("T")[0]
            items.append(f"- **{t}** on `{repo}` ({created_dt})")
        return items
    else:
        print("GitHub API error", r.status_code, r.text)
    return []

def replace_section(content, start_marker, end_marker, new_text):
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    replacement = start_marker + "\n" + new_text.strip() + "\n" + end_marker
    new_content, n = pattern.subn(replacement, content)
    if n == 0:
        # markers not found, append
        new_content = content + "\n\n" + replacement
    return new_content

def main():
    with open(README, "r", encoding="utf-8") as f:
        content = f.read()

    # Update blog section
    blog_text = "_No blog RSS configured yet. To enable: add a repo secret named `BLOG_RSS` with your blog RSS URL._"
    if BLOG_RSS:
        latest = fetch_latest_blog(BLOG_RSS)
        if latest:
            blog_text = f"- [{latest['title']}]({latest['link']}) — {latest['published']}"
    content = replace_section(content, "<!--BLOG_START-->", "<!--BLOG_END-->", blog_text)

    # Update activity section
    token = os.environ.get("GITHUB_TOKEN")
    activities = fetch_recent_activity(GITHUB_USER, token=token)
    if activities:
        act_text = "\\n".join(activities)
    else:
        act_text = "_No recent activity snapshot yet. When the Action runs it will populate this section._"
    content = replace_section(content, "<!--ACTIVITY_START-->", "<!--ACTIVITY_END-->", act_text)

    with open(README, "w", encoding="utf-8") as f:
        f.write(content)

    print("README updated.")

if __name__ == '__main__':
    main()
