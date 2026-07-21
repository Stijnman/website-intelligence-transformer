#!/usr/bin/env python3
"""
Website Intelligence Transformer v6.2 — Dark Mode
Autonomous website analysis: SEO signals, performance hints, content structure, and actionable fixes.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

APP_VERSION = "6.2.0"
USER_AGENT = (
    "WebsiteIntelligenceTransformer/6.2 (+https://github.com/Stijnman/website-intelligence-transformer)"
)


@dataclass
class PageIntel:
    url: str
    status_code: int
    title: str
    meta_description: str
    canonical: str
    h1: List[str]
    h2: List[str]
    word_count: int
    images: int
    images_missing_alt: int
    internal_links: int
    external_links: int
    has_viewport: bool
    has_og: bool
    has_json_ld: bool
    load_bytes: int
    score: int
    issues: List[str]
    wins: List[str]


def fetch(url: str, timeout: int = 20) -> tuple[Optional[requests.Response], Optional[str]]:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            allow_redirects=True,
        )
        return resp, None
    except requests.RequestException as exc:
        return None, str(exc)


def analyze_html(url: str, html: str, status_code: int, load_bytes: int) -> PageIntel:
    soup = BeautifulSoup(html, "lxml")
    issues: List[str] = []
    wins: List[str] = []

    title = (soup.title.string or "").strip() if soup.title else ""
    if not title:
        issues.append("Missing <title>")
    elif len(title) < 15:
        issues.append("Title is very short (<15 chars)")
    elif len(title) > 60:
        issues.append("Title may be truncated in SERPs (>60 chars)")
    else:
        wins.append("Solid title length")

    meta_desc = ""
    md = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if md and md.get("content"):
        meta_desc = md["content"].strip()
    if not meta_desc:
        issues.append("Missing meta description")
    elif len(meta_desc) < 50:
        issues.append("Meta description short (<50 chars)")
    elif len(meta_desc) > 160:
        issues.append("Meta description long (>160 chars)")
    else:
        wins.append("Meta description present with good length")

    canonical = ""
    link_can = soup.find("link", rel=lambda v: v and "canonical" in str(v).lower())
    if link_can and link_can.get("href"):
        canonical = link_can["href"]
        wins.append("Canonical link present")
    else:
        issues.append("No canonical link")

    h1 = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    h2 = [h.get_text(" ", strip=True) for h in soup.find_all("h2")]
    if not h1:
        issues.append("No H1 heading")
    elif len(h1) > 1:
        issues.append(f"Multiple H1 tags ({len(h1)})")
    else:
        wins.append("Single H1")

    text = soup.get_text(" ", strip=True)
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    if word_count < 150:
        issues.append("Thin content (<150 words)")
    else:
        wins.append(f"Content depth: {word_count} words")

    images = soup.find_all("img")
    missing_alt = sum(1 for img in images if not (img.get("alt") or "").strip())
    if images and missing_alt:
        issues.append(f"{missing_alt}/{len(images)} images missing alt text")
    elif images:
        wins.append("All images have alt text")

    base_host = urlparse(url).netloc
    internal = external = 0
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        abs_url = urljoin(url, href)
        host = urlparse(abs_url).netloc
        if host == base_host or not host:
            internal += 1
        else:
            external += 1

    viewport = bool(soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)}))
    if viewport:
        wins.append("Viewport meta for mobile")
    else:
        issues.append("Missing viewport meta (mobile)")

    has_og = bool(soup.find("meta", property=re.compile("^og:", re.I)))
    if has_og:
        wins.append("Open Graph tags present")
    else:
        issues.append("No Open Graph tags")

    has_json_ld = bool(soup.find("script", attrs={"type": "application/ld+json"}))
    if has_json_ld:
        wins.append("JSON-LD structured data found")
    else:
        issues.append("No JSON-LD structured data")

    # Score 0-100
    score = 100
    score -= min(40, 6 * len(issues))
    score += min(15, 3 * len(wins))
    score = max(0, min(100, score))

    return PageIntel(
        url=url,
        status_code=status_code,
        title=title,
        meta_description=meta_desc,
        canonical=canonical,
        h1=h1,
        h2=h2[:12],
        word_count=word_count,
        images=len(images),
        images_missing_alt=missing_alt,
        internal_links=internal,
        external_links=external,
        has_viewport=viewport,
        has_og=has_og,
        has_json_ld=has_json_ld,
        load_bytes=load_bytes,
        score=score,
        issues=issues,
        wins=wins,
    )


def keyword_hints(text: str, n: int = 15) -> List[tuple[str, int]]:
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "your", "are", "was",
        "you", "not", "have", "has", "but", "all", "can", "our", "will", "their",
        "about", "into", "more", "also", "than", "when", "what", "which", "they",
    }
    tokens = [t.lower() for t in re.findall(r"[A-Za-zÀ-ÿ]{3,}", text)]
    tokens = [t for t in tokens if t not in stop]
    return Counter(tokens).most_common(n)


def recommendations(intel: PageIntel) -> List[str]:
    recs: List[str] = []
    if any("title" in i.lower() for i in intel.issues):
        recs.append("Rewrite the title to 30–55 characters with primary keyword near the front.")
    if any("meta description" in i.lower() for i in intel.issues):
        recs.append("Add a 120–155 character meta description with a clear CTA.")
    if any("H1" in i for i in intel.issues):
        recs.append("Use exactly one descriptive H1 matching search intent.")
    if intel.images_missing_alt:
        recs.append("Add descriptive alt text to all informational images.")
    if not intel.has_json_ld:
        recs.append("Add JSON-LD (Organization / WebSite / FAQ) for rich results eligibility.")
    if not intel.has_og:
        recs.append("Add og:title, og:description, og:image for social sharing.")
    if intel.word_count < 300:
        recs.append("Expand body copy with unique value, FAQs, and internal links.")
    if not recs:
        recs.append("Strong baseline — next: Core Web Vitals, crawl budget, and content freshness.")
    return recs


def main() -> None:
    st.set_page_config(
        page_title="Website Intelligence Transformer",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("◈ Website Intelligence Transformer")
    st.caption(f"v{APP_VERSION} · Dark mode · Free & self-hostable")

    with st.sidebar:
        st.header("Analyze")
        url = st.text_input("Website URL", placeholder="https://example.com")
        run = st.button("Run intelligence scan", type="primary", use_container_width=True)
        st.markdown("---")
        st.markdown(
            "Local Streamlit app. No data is stored server-side. "
            "Respect robots.txt and site terms when scanning."
        )

    if not run:
        st.info("Enter a public URL and run a scan to get SEO, structure, and content intelligence.")
        st.markdown(
            """
            ### What you get
            - Title / meta / headings health
            - Content depth & image accessibility
            - Internal vs external link mix
            - Open Graph & JSON-LD presence
            - Actionable fix list + keyword hints
            """
        )
        return

    if not url.strip():
        st.error("Please enter a URL.")
        return

    with st.spinner("Fetching and analyzing…"):
        resp, err = fetch(url.strip())
        if err or resp is None:
            st.error(f"Fetch failed: {err or 'unknown error'}")
            return
        if resp.status_code >= 400:
            st.warning(f"HTTP {resp.status_code} — analyzing body anyway if present.")
        html = resp.text or ""
        intel = analyze_html(resp.url, html, resp.status_code, len(resp.content or b""))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Intelligence score", f"{intel.score}/100")
    c2.metric("HTTP status", intel.status_code)
    c3.metric("Words", intel.word_count)
    c4.metric("Payload", f"{intel.load_bytes / 1024:.1f} KB")

    left, right = st.columns(2)
    with left:
        st.subheader("Issues")
        if intel.issues:
            for i in intel.issues:
                st.markdown(f"- ⚠️ {i}")
        else:
            st.success("No major on-page issues detected.")
        st.subheader("Wins")
        for w in intel.wins:
            st.markdown(f"- ✅ {w}")
    with right:
        st.subheader("On-page snapshot")
        st.write(f"**Title:** {intel.title or '—'}")
        st.write(f"**Meta:** {intel.meta_description or '—'}")
        st.write(f"**Canonical:** {intel.canonical or '—'}")
        st.write(f"**H1:** {', '.join(intel.h1) or '—'}")
        st.write(
            f"**Links:** {intel.internal_links} internal · {intel.external_links} external · "
            f"**Images:** {intel.images} ({intel.images_missing_alt} missing alt)"
        )

    st.subheader("Recommended actions")
    for r in recommendations(intel):
        st.markdown(f"1. {r}")

    soup = BeautifulSoup(html, "lxml")
    body_text = soup.get_text(" ", strip=True)
    hints = keyword_hints(body_text)
    if hints:
        st.subheader("Keyword hints (frequency)")
        st.dataframe(
            pd.DataFrame(hints, columns=["token", "count"]),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Raw JSON"):
        st.json(asdict(intel))


if __name__ == "__main__":
    main()
