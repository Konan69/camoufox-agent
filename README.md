# camoufox-agent

Open a page in a browser that does not look like a bot.

Loads one URL in [Camoufox](https://github.com/daijro/camoufox), a patched Firefox with a spoofed fingerprint and human-like cursor movement, and prints what the page could see: `navigator.webdriver`, platform, plugins, screen size. I use it to check what a detection page sees before pointing an agent at a real site.

![A terminal runs main.py with a macOS fingerprint against a local test page; the page reports a Mac platform and no WebDriver](docs/media/hero.gif)

## Install

Linux with an X display or Xvfb, Python 3.11+, and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run python -m camoufox fetch      # downloads the patched Firefox build and its addons
```

Or in a container, which pins the engine, addons and Xvfb so a laptop and a server run the same browser:

```bash
docker build -t camoufox-agent .
docker run --rm camoufox-agent --url https://example.com
```

## Use

```bash
uv run python main.py                                    # about:blank, Windows fingerprint
uv run python main.py --os macos --url https://example.com
uv run python main.py --device mobile --screenshot      # 390x844, saves artifacts/mobile-windows.png
uv run python main.py --proxy socks5://host:1080        # proxy, with geoip matched to it
```

```console
test:Platform                  MacIntel
test:Plugins length            5
test:Screen                    1470x956
test:WebDriver                 missing (passed)
webdriver                      undetected
```

The table is followed by the same report as JSON.

| Flag | Default | |
| --- | --- | --- |
| `--url` | `about:blank` | Page to open |
| `--os` | `windows` | `windows`, `macos` or `linux` |
| `--device` | `desktop` | `mobile` sets a 390x844 viewport and an iPhone user agent |
| `--headless-mode` | `auto` | `auto`, `virtual` (own Xvfb) or `native` (`DISPLAY`) |
| `--screenshot` | off | Save `artifacts/<device>-<os>.png` |
| `--timeout` | `60` | Page load timeout in seconds |
| `--proxy` | none | `http://user:pass@host:port` or `socks5://host:port` |

## Limits

- It loads one URL and reports. No clicking, typing or scripted steps.
- `--os android` is listed but Camoufox 0.5.4 rejects it.
- `--device mobile` changes only the viewport and user agent; platform and screen still come from `--os`, and a page can see the mismatch.
- Under WSLg, `virtual` mode fails because `/tmp/.X11-unix` is read-only. Run `Xvfb :97 -nolisten unix -listen tcp`, set `DISPLAY=localhost:97`, and use `auto`.
- The Docker image was not built and tested for this README; the runs used `uv` on WSL2.

How the runner works: [docs/internals.md](docs/internals.md).

## License

MIT. Camoufox and Playwright keep their own licenses.
