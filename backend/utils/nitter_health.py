# utils/nitter_health.py
# ntscraper auto-picks instances, but this gives you manual control
# if you want to pin a specific Nitter node or rotate on failure.

import requests
import logging

log = logging.getLogger(__name__)

# Public Nitter instances (update list from https://github.com/zedeus/nitter/wiki/Instances)
NITTER_INSTANCES = [
    "nitter.net",
    "nitter.privacydev.net",
    "nitter.poast.org",
    "nitter.lucabased.space",
    "nitter.moomoo.me",
    "nitter.cz",
]

def find_healthy_instance(timeout: int = 5) -> str | None:
    """
    Ping each Nitter instance and return the first one that responds.
    Use this to pass a specific instance= to Nitter() if auto-detection fails.

    Usage:
        from utils.nitter_health import find_healthy_instance
        from ntscraper import Nitter

        instance = find_healthy_instance()
        scraper = Nitter(log_level=1, skip_instance_check=False)
        # OR pin manually:
        # scraper = Nitter(log_level=1)  # auto-select (default)
    """
    for host in NITTER_INSTANCES:
        try:
            url = f"https://{host}"
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200 and "nitter" in r.text.lower():
                log.info(f"Healthy Nitter instance found: {host}")
                return host
        except Exception as e:
            log.debug(f"Instance {host} unreachable: {e}")
            continue
    log.warning("No healthy Nitter instance found — ntscraper will auto-select")
    return None


def get_scraper_with_fallback():
    """
    Returns a Nitter scraper, optionally pinned to a healthy instance.
    Falls back to ntscraper's auto-selection if none found.
    """
    from ntscraper import Nitter

    # ntscraper handles instance selection internally.
    # Pass log_level=0 for silent, 1 for INFO.
    scraper = Nitter(log_level=1)
    return scraper
