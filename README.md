# camoufox-agent

A small runner that opens a page in [Camoufox](https://github.com/daijro/camoufox), a patched Firefox with a spoofed fingerprint and human-like cursor movement, and prints what the page could see of the browser.

![A terminal runs main.py with a macOS fingerprint against a local test page; the page reports a Mac platform and no WebDriver](docs/media/hero.gif)

## Why

Pages that check for automation read `navigator.webdriver`, the platform, the plugin list and the screen size. `main.py` launches Camoufox with `humanize=True` and a chosen OS fingerprint, loads one URL, and reports each of those values as a table and as JSON. You see what a detection page sees before you point an agent at a real site. The Dockerfile pins the engine, the addons, Xvfb and the system libraries at build time, so a laptop and a container host run the same browser and only the egress IP differs.

## Install

Requirements:

- Linux with an X display or Xvfb (tested on WSL2).
- Python 3.11 or later (tested with 3.12).
- [uv](https://docs.astral.sh/uv/) (tested with 0.11.7).

```bash
git clone <this repo> camoufox-agent && cd camoufox-agent
uv sync
uv run python -m camoufox fetch    # downloads the patched Firefox build and its addons
```

`uv.lock` pins `camoufox` 0.5.4 and `playwright` 1.60.0.

To build the container image instead:

```bash
docker build -t camoufox-agent .
docker run --rm camoufox-agent --url https://example.com
```

The entrypoint starts Xvfb on `:99`, sets `DISPLAY`, and runs `python3 main.py --headed` with your arguments.

## Quick start

With no arguments, `main.py` opens `about:blank` with a Windows fingerprint. This run had `DISPLAY` set to an Xvfb server:

```console
$ uv run python main.py

test                           result
------------------------------------------
device                         desktop
os                             windows
url                            about:blank
user_agent                     Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/201001
webdriver                      undetected
{
  "url": "about:blank",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
  "webdriver": false,
  "device": "desktop",
  "os": "windows"
}
```

Against a page with checks, every element with id `webdriver`, `chrome`, `plugins`, `languages` or `permissions` and every two-cell table row lands in the report. The hero above is this run against a local test page, with a macOS fingerprint:

```console
$ uv run python main.py --os macos --url file:///tmp/cfx/checks.html
...
test:Platform                  MacIntel
test:Plugins length            5
test:Screen                    1470x956
test:WebDriver                 missing (passed)
user_agent                     Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:152.0) Gecko/20
webdriver                      undetected
```

The table truncates each value at 64 characters. The JSON after it holds the full values.

## How it works

![main.py launches Camoufox through AsyncNewBrowser, which opens a display or Xvfb and a browser context; the page's checks become the report](docs/media/diagram.png)

`main.py` builds the launch options and calls `AsyncNewBrowser` from `camoufox.async_api` inside Playwright's `async_playwright()`. The options are `os` from `--os` and `humanize=True`. With `--proxy`, they also carry the parsed proxy and `geoip=True`. `pyproject.toml` installs the `camoufox[geoip]` extra for it.

`--headless-mode` picks the display:

- `native` runs headed on the current `DISPLAY`.
- `virtual` asks Camoufox to start its own Xvfb.
- `auto`, the default, runs on `DISPLAY` when it is set and on Xvfb otherwise.

`--device mobile` opens the context with a 390x844 viewport and an iPhone Safari user agent. `--device desktop` uses Camoufox's defaults.

The runner calls `page.goto(url, wait_until="networkidle")`, waits 1.5 seconds, then reads `navigator.userAgent`, `navigator.webdriver`, the five element ids above and every table row. `--screenshot` writes `artifacts/<device>-<os>.png`. The report prints as a sorted table and then as JSON. A launch or page error prints `runner failed: <error>` to stderr and exits with code 1.

## Configuration

All configuration is by flag. There is no config file and no environment variable beyond `DISPLAY`.

| Flag | Default | What it does |
| --- | --- | --- |
| `--url` | `about:blank` | Page to open |
| `--os` | `windows` | Fingerprint OS: `windows`, `macos`, `linux` or `android` |
| `--device` | `desktop` | `mobile` sets a 390x844 viewport and an iPhone user agent |
| `--headless-mode` | `auto` | `auto`, `virtual` (always Xvfb) or `native` (always `DISPLAY`) |
| `--headed` | off | Accepted and set by the Docker entrypoint. `main.py` does not read it |
| `--screenshot` | off | Save `artifacts/<device>-<os>.png` |
| `--timeout` | `60` | Page load timeout in seconds |
| `--proxy` | none | `http://user:pass@host:port` or `socks5://host:port`. Also turns on `geoip` |

## Limits

- `--os android` is in the flag's choices, but Camoufox 0.5.4 rejects it with `Camoufox does not support the OS: 'android'`.
- `--device mobile` changes only the viewport and the user agent. `navigator.platform` and the screen size still come from the `--os` fingerprint, so a page can see the mismatch.
- It loads one URL and reports. It does not click, type or run a script of steps.
- `virtual` mode needs a writable `/tmp/.X11-unix`. Under WSLg that directory is read-only and Camoufox's own Xvfb fails. Start Xvfb yourself with `Xvfb :97 -nolisten unix -listen tcp`, set `DISPLAY=localhost:97`, and use `native` or `auto`.
- The Docker image was not built for this README. The runs above used `uv` on Linux (WSL2).

## License

MIT. See [LICENSE](LICENSE). Camoufox and Playwright keep their own licenses.
