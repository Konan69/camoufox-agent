# Camoufox headed agent — reproducible image.
#
# Parity contract: this image produces the same Camoufox behavior on a laptop,
# a VPS, Railway, or any container host. Everything the browser needs is baked
# in at build time (engine, addons, Xvfb, system libs, pinned deps), so the
# only runtime variable left is the network egress IP of the host.

FROM python:3.12-slim-bookworm

ARG CAMOUFOX_VERSION=0.5.4

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Xvfb (virtual display so headed mode works without a monitor) + the full
# set of libs the patched Firefox build needs at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        xvfb \
        xauth \
        libgtk-3-0 \
        libdbus-glib-1-2 \
        libasound2 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libxtst6 \
        libxss1 \
        libnss3 \
        libcups2 \
        libpango-1.0-0 \
        libcairo2 \
        libglib2.0-0 \
        libgdk-pixbuf-2.0-0 \
        fonts-liberation \
        fonts-dejavu \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir "camoufox[geoip]==${CAMOUFOX_VERSION}"

# Bake the browser engine + addons into the image at build time.
RUN python3 -m camoufox fetch

COPY main.py /app/main.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
