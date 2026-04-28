import difflib
import time
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


KNOWN_PLATFORM_SLUGS = {

#######NES
    "nes": "nes",
    "nintendo": "nes",
    "nintendo entertainment system": "nes",

#######SNES
    "snes": "super-nintendo",
    "super nes": "super-nintendo",
    "super nintendo": "super-nintendo",
    "super nintendo entertainment system": "super-nintendo",

#######N64
    "nintendo 64": "nintendo-64",
    "n64": "nintendo-64",
    "64": "nintendo-64",

#######GCN
    "gamecube": "gamecube",
    "gcn": "gamecube",

#######Wii
    "wii": "wii",
    "wii u": "wii-u",
    "wiiu": "wii-u",

#######Switch
    "switch": "nintendo-switch",
    "nsw": "nintendo-switch",
    "sw": "nintendo-switch",
    "nintendo switch": "nintendo-switch",
    "switch 2": "nintendo-switch-2",
    "nintendo switch 2": "nintendo-switch-2",
    "nsw2": "nintendo-switch-2",
    "sw2": "nintendo-switch-2",

#######GB
    "gameboy": "gameboy",
    "gb": "gameboy",

#######GBC
    "gameboy color": "gameboy-color",
    "gbc": "gameboy-color",

#######GBA
    "gameboy advance": "gameboy-advance",
    "gba": "gameboy-advance",

#######DS
    "nds": "nintendo-ds",
    "ds": "nintendo-ds",

#######3DS
    "n3ds": "nintendo-3ds",
    "3ds": "nintendo-3ds",

#######Virtual Boy
    "virtual boy": "virtual-boy",
    "vb": "virtual-boy",

#######Game & Watch
    "game & watch": "game-&-watch",
    "g&w": "game-&-watch",

#######PlayStation
    "playstation": "playstation",
    "ps1": "playstation",
    "ps": "playstation",
    "playstation 2": "playstation-2",
    "ps2": "playstation-2",
    "playstation 3": "playstation-3",
    "ps3": "playstation-3",
    "playstation 4": "playstation-4",
    "ps4": "playstation-4",
    "playstation 5": "playstation-5",
    "ps5": "playstation-5",
    "psp": "psp",
    "vita": "playstation-vita",
    "psv": "playstation-vita",
    "psvita": "playstation-vita",
    "playstation vita": "playstation-vita",
    "psp2": "playstation-vita",

#######Xbox
    "xbox": "xbox",
    "xb": "xbox",
    "xbox 360": "xbox-360",
    "x360": "xbox-360",
    "360": "xbox-360",
    "xbox one": "xbox-one",
    "xbo": "xbox-one",
    "xbone": "xbox-one",
    "xbox series x": "xbox-series-x",
    "xsx": "xbox-series-x",
    "xbx": "xbox-series-x",
    "xbsx": "xbox-series-x",
    "series x": "xbox-series-x",

#######Sega Master System
    "mastersystem": "sega-master-system",
    "master system": "sega-master-system",
    "sms": "sega-master-system",

#######Game Gear
    "sega game gear": ["sega-game-gear", "jp-sega-game-gear"],
    "game gear": ["sega-game-gear", "jp-sega-game-gear"],
    "gg": ["sega-game-gear", "jp-sega-game-gear"],

#######Sega Genesis/Mega Drive
    "sega": ["sega-genesis", "jp-sega-mega-drive"],
    "sega genesis": ["sega-genesis", "jp-sega-mega-drive"],
    "genesis": ["sega-genesis", "jp-sega-mega-drive"],
    "mega drive": ["sega-genesis", "jp-sega-mega-drive"],
    "md": ["sega-genesis", "jp-sega-mega-drive"],
    "smd": ["sega-genesis", "jp-sega-mega-drive"],

#######Sega Saturn
    "sega saturn": ["sega-saturn", "jp-sega-saturn"],
    "saturn": ["sega-saturn", "jp-sega-saturn"],
    "sat": ["sega-saturn", "jp-sega-saturn"],

#######Dreamcast
    "dreamcast": "sega-dreamcast",
    "dc": "sega-dreamcast",

#######Atari
    "atari": ["atari-2600", "atari-5200", "atari-7800"],
    "atari 2600": "atari-2600",
    "2600": "atari-2600",
    "atari 5200": "atari-5200",
    "5200": "atari-5200",
    "atari 7800": "atari-7800",
    "7800": "atari-7800",

#######Neo Geo
    "neo geo": ["neo-geo-mvs", "neo-geo-aes", "jp-neo-geo-mvs", "jp-neo-geo-aes"],
    "ng": ["neo-geo-mvs", "neo-geo-aes", "jp-neo-geo-mvs", "jp-neo-geo-aes"],
    "neogeo": ["neo-geo-mvs", "neo-geo-aes", "jp-neo-geo-mvs", "jp-neo-geo-aes"],
    "ngp": ["neo-geo-pocket", "jp-neo-geo-pocket", "neo-geo-pocket-color", "jp-neo-geo-pocket-color"],
    "neogeopocket": ["neo-geo-pocket", "jp-neo-geo-pocket", "neo-geo-pocket-color", "jp-neo-geo-pocket-color"],
    "neo geo pocket": ["neo-geo-pocket", "jp-neo-geo-pocket", "neo-geo-pocket-color", "jp-neo-geo-pocket-color"],
    "ngpc": ["neo-geo-pocket-color", "jp-neo-geo-pocket-color"],
    "neogeopocketcolor": ["neo-geo-pocket-color", "jp-neo-geo-pocket-color"],
    "neo geo pocket color": ["neo-geo-pocket-color", "jp-neo-geo-pocket-color"],
    "ngcd": ["neo-geo-cd", "jp-neo-geo-cd"],
    "neo geo cd": ["neo-geo-cd", "jp-neo-geo-cd"],
    "ncd": ["neo-geo-cd", "jp-neo-geo-cd"],

#######NEC
    "pc engine": ["jp-pc-engine", "jp-pc-engine-cd"],
    "pce": ["jp-pc-engine", "jp-pc-engine-cd"],
    "pc-engine": ["jp-pc-engine", "jp-pc-engine-cd"],
    "pcengine": ["jp-pc-engine", "jp-pc-engine-cd"],
    "pc engine cd": "jp-pc-engine-cd",
    "pc engine cd-rom": "jp-pc-engine-cd",
    "pc engine cd rom": "jp-pc-engine-cd",
    "pce cd": "jp-pc-engine-cd",
    "pce cd-rom": "jp-pc-engine-cd",
    "pcecd": "jp-pc-engine-cd",
    "turbo": ["turbografx-16", "turbografx-cd"],
    "turbografx": ["turbografx-16", "turbografx-cd"],
    "turbografx 16": ["turbografx-16", "turbografx-cd"],
    "turbografx-16": ["turbografx-16", "turbografx-cd"],
    "turbografx16": ["turbografx-16", "turbografx-cd"],
    "tg16": ["turbografx-16", "turbografx-cd"],
    "turbo cd": "turbografx-cd",
    "tcd": "turbografx-cd",
    "turbocd": "turbografx-cd",
    "tg-cd": "turbografx-cd",
    "turbografx cd": "turbografx-cd",
    "turbografx-cd": "turbografx-cd",
    "turbografxcd": "turbografx-cd",
    "tgcd": "turbografx-cd",
    "tg16cd": "turbografx-cd",

#######Others
    "c64": "commodore-64",
    "commodore 64": "commodore-64",

}


@dataclass
class GameData:
    title: str
    platform: str
    price: Optional[float] = None
    suggested_price: Optional[float] = None
    sale_info: Optional[str] = None


class Scraper:
    def __init__(self, pause_time: float = 1.5) -> None:
        self.pause_time = pause_time

    def fetch_game_data(self, title: str, platform: str, condition: str | None = None) -> Dict[str, any]:
        scraped_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        
        slug = self._normalize_platform(platform)
        if not slug:
            return self._build_no_match_response(title, platform, scraped_at, "Platform not recognized")

        slug_candidates = slug if isinstance(slug, list) else [slug]
        match = None
        scrape_error = None
        used_slug = slug_candidates[0]

        for candidate_slug in slug_candidates:
            try:
                games = self._scrape_console_page(candidate_slug)
            except Exception as exc:
                scrape_error = exc
                continue

            match = self._find_best_match(title, games)
            if match:
                used_slug = candidate_slug
                break

        if not match:
            if scrape_error:
                return self._build_no_match_response(title, platform, scraped_at, f"PriceCharting scrape failed: {scrape_error}")
            return self._build_no_match_response(title, platform, scraped_at, "No close match found on PriceCharting")

        # === Successful scrape ===
        price, price_type = self._select_price(match, condition)
        suggested_price = round(price) if isinstance(price, (int, float)) else None
        region = self._determine_region(used_slug)

        return {
            "title": match["title"],
            "platform": platform,
            "region": region,
            "price": price,
            "price_type": price_type,
            "condition": condition or price_type,
            "suggested_price": suggested_price,
            "sale_info": f"Matched: {match['title']} ({used_slug}) - {price_type} pricing",
            "scraped_at": scraped_at,
            "scraped_data": {
                "complete_price": match.get("complete_price"),
                "loose_price": match.get("loose_price"),
                "new_price": match.get("new_price"),
            },
        }

    def _build_no_match_response(self, title: str, platform: str, scraped_at: str, message: str):
        return {
            "title": title,
            "platform": platform,
            "region": "NTSC-U",
            "price": None,
            "price_type": "CIB",
            "suggested_price": None,
            "sale_info": message,
            "scraped_at": scraped_at,
            "scraped_data": {},
        }

    def _normalize_platform(self, platform: str) -> Optional[str | list[str]]:
        normalized = platform.strip().lower()
        normalized = normalized.replace("_", " ").replace("/", " ")
        normalized = " ".join(normalized.split())
        if normalized in KNOWN_PLATFORM_SLUGS:
            return KNOWN_PLATFORM_SLUGS[normalized]
        candidate = normalized.replace(" ", "-")
        return candidate if candidate in KNOWN_PLATFORM_SLUGS.values() else None

    def _make_browser(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-images")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--disable-javascript")   # Try this if you don't need JS heavily

        # Aggressive resource blocking - this is the key speedup
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.javascript": 1,
            "profile.managed_default_content_settings.plugins": 2,
            "profile.managed_default_content_settings.popups": 2,
        }
        options.add_experimental_option("prefs", prefs)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.set_page_load_timeout(25)
        return driver

    def _scroll_to_bottom(self, browser) -> None:
        """Scroll with shorter delays."""
        prev_height = browser.execute_script("return document.body.scrollHeight")
        stable_count = 0
        max_attempts = 8   # safety limit

        while stable_count < 3 and max_attempts > 0:
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.7)                    # Reduced from 1.5s
            curr_height = browser.execute_script("return document.body.scrollHeight")
            
            if curr_height == prev_height:
                stable_count += 1
            else:
                stable_count = 0
                prev_height = curr_height
            max_attempts -= 1

    def _scrape_console_page(self, slug: str) -> List[Dict[str, Optional[str]]]:
        browser = self._make_browser()
        try:
            browser.get(f"https://www.pricecharting.com/console/{slug}")
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.ID, "games_table"))
            )
            self._scroll_to_bottom(browser)
            soup = BeautifulSoup(browser.page_source, "html.parser")
            table = soup.find("table", {"id": "games_table"})
            if not table:
                return []

            games = []
            for row in table.select("tbody tr"):
                title_cell = row.find("td", class_="title")
                if not title_cell:
                    continue
                title_tag = title_cell.find("a")
                title_text = title_tag.get_text(strip=True) if title_tag else title_cell.get_text(strip=True)
                games.append(
                    {
                        "title": title_text,
                        "loose_price": self._parse_price(row, "used_price"),
                        "complete_price": self._parse_price(row, "cib_price"),
                        "new_price": self._parse_price(row, "new_price"),
                    }
                )
            return games
        finally:
            browser.quit()

    def _determine_region(self, slug: str | None) -> str:
        """Determine region from PriceCharting console slug.
        - Starts with 'jp'  → NTSC-J
        - Starts with 'pal' → PAL
        - Otherwise        → NTSC-U (default for US consoles)
        """
        if not slug:
            return "NTSC-U"
        
        slug_lower = slug.strip().lower()
        
        if slug_lower.startswith("jp"):
            return "NTSC-J"
        elif slug_lower.startswith("pal"):
            return "PAL"
        else:
            return "NTSC-U"

    def _parse_price(self, row, css_class: str) -> Optional[float]:
        td = row.find("td", class_=css_class)
        if not td:
            return None
        text = td.get_text(strip=True).replace("$", "").replace(",", "")
        if not text or text.upper() == "N/A":
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _find_best_match(self, query: str, games: List[Dict[str, Optional[str]]]) -> Optional[Dict[str, Optional[str]]]:
        """Return best match only if it's a strong match. Otherwise return None so GUI can show options."""
        if not games:
            return None

        query = query.strip().lower()
        query_words = set(query.split())

        best_score = -1
        best_match = None
        good_matches = []

        for game in games:
            title = game.get("title", "").strip()
            if not title:
                continue
            title_lower = title.lower()

            # 1. Exact match (highest priority)
            if title_lower == query:
                return game

            # 2. Score based on word overlap + difflib
            title_words = set(title_lower.split())
            common_words = len(query_words & title_words)

            # Bonus for longer common substring
            seq_ratio = difflib.SequenceMatcher(None, query, title_lower).ratio()

            score = common_words * 10 + seq_ratio * 100

            # Strong match threshold
            if seq_ratio > 0.85 or (common_words >= 2 and seq_ratio > 0.65):
                good_matches.append((score, game))
                if score > best_score:
                    best_score = score
                    best_match = game

        # If we have one very strong best match, return it automatically
        if best_match and best_score > 140:   # adjust this threshold if needed
            return best_match

        # If we have several decent matches, let the GUI show them
        if good_matches:
            # Sort by score descending
            good_matches.sort(key=lambda x: x[0], reverse=True)
            # Return None → GUI will show selection dialog with top candidates
            return None

        return None

    def _choose_match(self, query: str, matches: List[Dict[str, Optional[str]]]) -> Optional[Dict[str, Optional[str]]]:
        """Return all matches so the GUI can let the user choose.
        If called from CLI/tests, it falls back to the old behavior."""
        if not matches:
            return None
        # For now, return the first one (GUI will handle selection)
        # In the future we can enhance this further
        return matches[0]

    def _select_price(self, game: Dict[str, Optional[str]], condition: str | None = None) -> tuple[Optional[float], str]:
        order_map = {
            "CIB": (("complete_price", "CIB"), ("loose_price", "Loose"), ("new_price", "New")),
            "Loose": (("loose_price", "Loose"), ("complete_price", "CIB"), ("new_price", "New")),
            "New": (("new_price", "New"), ("complete_price", "CIB"), ("loose_price", "Loose")),
        }
        order = order_map.get(condition, (("complete_price", "CIB"), ("loose_price", "Loose"), ("new_price", "New")))
        for key, label in order:
            if game.get(key) is not None:
                return game[key], label
        return None, condition or "CIB"

    def _select_suggested_price(self, game: Dict[str, Optional[str]]) -> Optional[float]:
        for key in ("new_price", "complete_price", "loose_price"):
            if game.get(key) is not None:
                return game[key]
        return None

    def search_games(self, title: str, platform: str, preferred_region: str = "NTSC-U") -> List[Dict]:
        """Search with optional region preference."""
        base_slug = self._normalize_platform(platform)
        if not base_slug:
            return []

        slug_candidates = []
        if isinstance(base_slug, list):
            slug_candidates.extend(base_slug)
        else:
            slug_candidates.append(base_slug)

        normalized_platform = platform.strip().lower()

        # Always include JP and PAL for Saturn and similar platforms
        if "saturn" in normalized_platform or "neo geo" in normalized_platform:
            for extra in ["jp-sega-saturn", "pal-sega-saturn", "jp-neo-geo"]:
                if extra not in slug_candidates:
                    slug_candidates.append(extra)

        # Limit to maximum 2 pages to scrape
        slug_candidates = list(dict.fromkeys(slug_candidates))[:2]

        all_matches = []
        query_lower = title.strip().lower()

        for candidate_slug in slug_candidates:
            try:
                games = self._scrape_console_page(candidate_slug)
                if games:
                    region = self._determine_region(candidate_slug)
                    for game in games:
                        game_title = game.get("title", "").strip()
                        if not game_title:
                            continue

                        # Add metadata
                        game["region"] = region
                        game["platform"] = platform
                        game["console_slug"] = candidate_slug

                        # Compute match quality
                        title_lower = game_title.lower()
                        seq_ratio = difflib.SequenceMatcher(None, query_lower, title_lower).ratio()
                        word_overlap = len(set(query_lower.split()) & set(title_lower.split()))

                        game["match_score"] = round(seq_ratio * 100, 1)
                        game["word_overlap"] = word_overlap

                        # === IMPORTANT: Compute suggested_price like the old code did ===
                        price, price_type = self._select_price(game, None)   # Use default condition logic
                        suggested_price = round(price) if isinstance(price, (int, float)) else None
                        game["suggested_price"] = suggested_price
                        game["price_type"] = price_type

                        all_matches.append(game)
            except Exception as e:
                print(f"Warning scraping {candidate_slug}: {e}")
                continue

        # Deduplicate by (title, region)
        seen = set()
        unique = []
        for game in all_matches:
            key = (game.get("title", "").strip().lower(), game.get("region", ""))
            if key not in seen:
                seen.add(key)
                unique.append(game)

        # Sort: best match first
        unique.sort(key=lambda x: (x.get("match_score", 0), x.get("word_overlap", 0)), reverse=True)

        return unique[:12]