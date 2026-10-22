"""Phase 2 smoke test: walk through the card flow on a phone-sized screen, screenshot
each state, then reload offline. Needs the built app served (vite preview) with the
fixture deck; run with Playwright and its browsers from nixpkgs:

    nix shell --impure --expr 'with import <nixpkgs> {}; [ (python3.withPackages (ps: [ ps.playwright ])) ]' \\
      --command env PLAYWRIGHT_BROWSERS_PATH=$(nix build --no-link --print-out-paths nixpkgs#playwright-driver.browsers) \\
      python3 app/smoke/screens.py http://127.0.0.1:4173/
"""

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:4173/"
OUT = Path.cwd() / "data" / "work" / "screens"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="de-DE")
    page = context.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL)
    page.wait_for_selector("text=Bereit!")
    page.screenshot(path=OUT / "1-bereit.png")
    page.click("text=Bereit!")
    time.sleep(0.25)
    page.screenshot(path=OUT / "2-shuffle.png")
    time.sleep(1.2)
    page.screenshot(path=OUT / "3-laeuft.png")
    page.click("button:has-text('Satz')")
    time.sleep(0.3)
    page.screenshot(path=OUT / "4-satz-tippt.png")  # typing; the button flashes -20
    time.sleep(1.2)
    page.screenshot(path=OUT / "4-satz.png")  # typed; the word has not moved
    # The card flip (D38): a scan line brings in the back (the name), which holds
    # while the title rests at the right as etraK; a second sweep brings the new front.
    page.click("button:has-text('Weiß ich'):not(:has-text('nicht'))")
    time.sleep(0.2)
    page.screenshot(path=OUT / "5a-flip-scan.png")
    time.sleep(0.4)
    page.screenshot(path=OUT / "5b-flip-back.png")
    time.sleep(0.8)
    page.screenshot(path=OUT / "5-beantwortet.png")
    page.click("button:has-text('Weiter')")
    time.sleep(1.0)
    page.screenshot(path=OUT / "5c-flip-bereit.png")  # the second sweep uncovering Bereit
    page.click("text=Bereit!")  # fahren
    time.sleep(1.3)
    page.click("button:has-text('Formen')")
    time.sleep(0.9)  # a charged hint's sheet waits for its deduction to show
    page.screenshot(path=OUT / "6-formen.png")
    page.click("button:has-text('Schließen')")
    page.click("button:has-text('Weiß ich nicht')")
    time.sleep(1.4)
    page.screenshot(path=OUT / "7-nicht.png")
    page.click("button:has-text('Weiter')")
    page.click("text=Bereit!")  # Hand
    time.sleep(1.3)
    page.screenshot(path=OUT / "8-hand.png")
    page.click("button:has-text('Weiß ich'):not(:has-text('nicht'))")
    time.sleep(1.3)
    page.click("button[aria-label='English']")
    time.sleep(0.6)
    page.screenshot(path=OUT / "10-english.png")
    page.click("button[aria-label='Deutsch']")
    # Thema (D37): the button turns first, then a Latte circle grows from it;
    # back to Mocha, the Latte view shrinks into the button.
    page.click("button[aria-label='Thema']")
    time.sleep(0.45)
    page.screenshot(path=OUT / "11a-thema-grow.png")
    time.sleep(0.8)
    page.screenshot(path=OUT / "11-thema.png")
    page.click("button[aria-label='Thema']")
    time.sleep(0.5)
    page.screenshot(path=OUT / "11b-thema-shrink.png")
    time.sleep(0.8)
    page.screenshot(path=OUT / "11c-thema-mocha.png")
    page.click("button[aria-label='Thema']")
    page.click("button[aria-label='Thema']")  # ignored while the first runs
    time.sleep(1.2)
    assert page.evaluate("document.documentElement.dataset.theme") == "latte"
    assert page.evaluate("document.documentElement.dataset.reveal") is None

    # Offline: once the service worker controls the page, a reload without network must still work.
    page.evaluate("navigator.serviceWorker.ready")
    page.reload()
    page.wait_for_selector("text=Bereit!")
    time.sleep(1.0)
    context.set_offline(True)
    page.reload()
    page.wait_for_selector("text=Bereit!", timeout=10_000)
    page.click("text=Bereit!")
    time.sleep(1.3)
    page.screenshot(path=OUT / "12-offline.png")
    print("console errors:", errors)
    browser.close()
