from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.sync_api import sync_playwright


def scrape_ekantipur(
    *,
    url: str = "https://ekantipur.com",
    headless: bool = True,
    timeout_ms: int = 60_000,
) -> Dict[str, Any]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.wait_for_load_state("networkidle", timeout=timeout_ms)

            page.get_by_role("main").get_by_role("link", name="मनोरञ्जन").first.click(
                timeout=timeout_ms
            )
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
            page.wait_for_selector(".category", timeout=timeout_ms)

            data: Dict[str, Any] = {
                "entertainment_news": [],
                "cartoon_of_the_day": None,
            }

            cards = page.locator(".category")
            count = min(cards.count(), 5)
            for i in range(count):
                card = cards.nth(i)

                title_locator = card.locator("h2 a").first
                if title_locator.count() == 0:
                    title = None
                else:
                    title_text = title_locator.inner_text().strip()
                    title = title_text or None

                img = card.locator(".category-image img").first
                if img.count() == 0:
                    image_url = None
                else:
                    image_url = (
                        (img.get_attribute("src") or "").strip()
                        or (img.get_attribute("data-src") or "").strip()
                        or (img.get_attribute("data-lazy-src") or "").strip()
                        or None
                    )

                author_locator = card.locator(".author-name a").first
                author: Optional[str]
                if author_locator.count() == 0:
                    author = None
                else:
                    author_text = author_locator.inner_text().strip()
                    author = author_text or None

                data["entertainment_news"].append(
                    {
                        "title": title,
                        "image_url": image_url,
                        "category": "मनोरञ्जन",
                        "author": author,
                    }
                )

            try:
                page.goto(
                    f"{url.rstrip('/')}/cartoon",
                    wait_until="networkidle",
                    timeout=timeout_ms,
                )
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
                page.wait_for_selector(".cartoon-wrapper", timeout=timeout_ms)

                wrapper = page.locator(".cartoon-wrapper").first

                cartoon_img = wrapper.locator(".cartoon-image img").first
                if cartoon_img.count() == 0:
                    cartoon_image_url = None
                else:
                    cartoon_image_url = (
                        (cartoon_img.get_attribute("src") or "").strip()
                        or (cartoon_img.get_attribute("data-src") or "").strip()
                        or (cartoon_img.get_attribute("data-lazy-src") or "").strip()
                        or None
                    )

                desc = wrapper.locator(".cartoon-description p").first
                if desc.count() == 0:
                    title = None
                    author = None
                else:
                    raw_text = desc.inner_text().strip()
                    if " - " in raw_text:
                        left, right = raw_text.split(" - ", 1)
                        title = left.strip() or None
                        author = right.strip() or None
                    else:
                        title = raw_text or None
                        author = None

                data["cartoon_of_the_day"] = {
                    "title": title,
                    "image_url": cartoon_image_url,
                    "author": author,
                }
            except Exception:
                print("Cartoon not found")
            return data
        finally:
            context.close()
            browser.close()


def save_to_json(
    data: Dict[str, Any],
    output_path: Union[str, Path] = "output.json",
    *,
    indent: int = 2,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    return path


if __name__ == "__main__":
    scraped = scrape_ekantipur()
    save_to_json(scraped, "output.json")
    print("Scraping finished, data saved to output.json")
