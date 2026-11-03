import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from camoufox.async_api import AsyncNewBrowser
from playwright.async_api import async_playwright

OUT_DIR = Path(__file__).parent / "artifacts"

MOBILE_VIEWPORT = {"width": 390, "height": 844}
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Camoufox headed agent runner")
    parser.add_argument(
        "--device", choices=["desktop", "mobile"], default="desktop",
        help="form factor to emulate (default: desktop)",
    )
    parser.add_argument(
        "--os", choices=["windows", "macos", "linux", "android"],
        default="windows", help="spoofed OS fingerprint (default: windows)",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="launch with a real/virtual display (required for cloud parity)",
    )
    parser.add_argument(
        "--headless-mode", choices=["auto", "virtual", "native"], default="auto",
        help="auto: real DISPLAY if present else Xvfb; virtual: always Xvfb; "
        "native: always real DISPLAY",
    )
    parser.add_argument(
        "--url", default="about:blank",
        help="page to visit (default: about:blank)",
    )
    parser.add_argument(
        "--screenshot", action="store_true", help="save a screenshot to artifacts/",
    )
    parser.add_argument(
        "--timeout", type=int, default=60, help="page load timeout in seconds",
    )
    parser.add_argument(
        "--proxy", default=None,
        help="proxy for geo egress, e.g. 'http://user:pass@host:port' or "
        "'socks5://host:port'",
    )
    return parser.parse_args()


def parse_proxy(value: str) -> dict:
    from urllib.parse import urlparse

    parts = urlparse(value if "://" in value else f"http://{value}")
    proxy: dict = {"server": value}
    if parts.username is not None:
        proxy["username"] = parts.username
    if parts.password is not None:
        proxy["password"] = parts.password
    return proxy


def render_table(results: dict) -> str:
    lines = ["", f"{'test':<30} {'result':<10}", "-" * 42]
    for key, value in sorted(results.items()):
        if key == "webdriver":
            label = "undetected" if value is False else f"DETECTED ({value})"
        elif isinstance(value, bool):
            label = "passed" if value else "FAILED"
        else:
            label = str(value)[:64]
        lines.append(f"{key:<30} {label:<10}")
    return "\n".join(lines)


async def run(args: argparse.Namespace) -> int:
    OUT_DIR.mkdir(exist_ok=True)

    launch: dict = {
        "os": args.os,
        "humanize": True,
    }
    if args.proxy:
        launch["proxy"] = parse_proxy(args.proxy)
        launch["geoip"] = True
    mode = args.headless_mode
    if mode == "native":
        launch["headless"] = False
    elif mode == "virtual":
        launch["headless"] = "virtual"
    elif os.environ.get("DISPLAY"):
        launch["headless"] = False
    else:
        launch["headless"] = "virtual"

    results: dict = {}
    async with async_playwright() as p:
        browser = await AsyncNewBrowser(p, **launch)
        if args.device == "mobile":
            context = await browser.new_context(
                viewport=MOBILE_VIEWPORT, user_agent=MOBILE_UA,
            )
        else:
            context = await browser.new_context()
        page = await context.new_page()

        await page.goto(args.url, wait_until="networkidle", timeout=args.timeout * 1000)
        await page.wait_for_timeout(1500)

        results["url"] = args.url
        results["user_agent"] = await page.evaluate("navigator.userAgent")
        results["webdriver"] = await page.evaluate("navigator.webdriver")
        results["device"] = args.device
        results["os"] = args.os
        if args.proxy:
            results["proxy"] = args.proxy

        for sel, key in {
            "#webdriver": "webdriver_test",
            "#chrome": "chrome_perm",
            "#plugins": "plugins",
            "#languages": "languages",
            "#permissions": "permissions",
        }.items():
            el = await page.query_selector(sel)
            if el:
                results[key] = (await el.inner_text()).strip()

        statuses = await page.evaluate(
            "Array.from(document.querySelectorAll('table tr')).map(r => "
            "Array.from(r.querySelectorAll('td')).map(c => c.innerText))"
        )
        for row in statuses:
            if len(row) >= 2 and row[0]:
                results.setdefault(f"test:{row[0]}", row[1])

        if args.screenshot:
            shot = OUT_DIR / f"{args.device}-{args.os}.png"
            await page.screenshot(path=str(shot))
            results["screenshot"] = str(shot)

        await browser.close()

    print(render_table(results))
    print(json.dumps(results, indent=2, default=str))
    return 0


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(run(args))
    except Exception as exc:  # noqa: BLE001
        print(f"runner failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())