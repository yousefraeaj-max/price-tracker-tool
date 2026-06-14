"""
scraper.py — سكرابر الأسعار
نفس منطق السكرابر الأصلي، مطوّر ليعمل مع قاعدة البيانات
"""

import re
import json
import logging
import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
from bs4 import BeautifulSoup

import database as db

logger = logging.getLogger(__name__)

CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL_SECONDS", "300"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}


@dataclass
class PriceOffer:
    label: str
    price: float
    original_price: Optional[float] = None
    quantity: Optional[int] = None


@dataclass
class ProductResult:
    url: str
    title: str
    platform: str
    offers: list[PriceOffer] = field(default_factory=list)
    error: Optional[str] = None


# ─────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────

async def scrape_product(url: str, client: httpx.AsyncClient) -> ProductResult:
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        return ProductResult(url=url, title="", platform="error", error=str(e))

    soup = BeautifulSoup(html, "html.parser")
    platform = _detect_platform(soup, url)
    title = _get_title(soup)
    offers: list[PriceOffer] = []

    if platform == "easyorders":
        offers = _scrape_easyorders(soup, html)
    elif platform == "woocommerce":
        offers = _scrape_woocommerce(soup, html)
    elif platform == "shopify":
        offers = _scrape_shopify(soup, html)

    if not offers:
        offers = _scrape_generic(soup, html)

    return ProductResult(url=url, title=title, platform=platform, offers=offers)


# ─────────────────────────────────────────
# PLATFORM DETECTION
# ─────────────────────────────────────────

def _detect_platform(soup: BeautifulSoup, url: str) -> str:
    host = url.split("/")[2].lower()
    if "easyorders" in host or "easy-orders" in host:
        return "easyorders"
    if soup.find(class_=re.compile(r"woocommerce|wc-")):
        return "woocommerce"
    if soup.find(attrs={"data-shopify": True}) or "myshopify" in host:
        return "shopify"
    if soup.find(class_=re.compile(r"product_price|product_name")):
        return "easyorders"
    return "generic"


def _get_title(soup: BeautifulSoup) -> str:
    for sel in ["h1", ".product_name", ".product_title", "title"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)[:200]
    return ""


# ─────────────────────────────────────────
# EASYORDERS
# ─────────────────────────────────────────

def _scrape_easyorders(soup: BeautifulSoup, html: str) -> list[PriceOffer]:
    offers = []
    for btn in soup.find_all(attrs={"data-price": True}):
        price = _parse_price(btn.get("data-price", ""))
        if not price:
            continue
        qty = btn.get("data-quantity") or btn.get("data-qty")
        label = btn.get_text(strip=True) or f"عرض {len(offers)+1}"
        label = re.sub(r"\s+", " ", label)[:80]
        offers.append(PriceOffer(label=label, price=price,
                                  quantity=int(qty) if qty and qty.isdigit() else None))

    if not offers:
        offer_containers = soup.find_all(
            class_=re.compile(r"offer|package|bundle|product_offer|quantity_offer", re.I)
        )
        for cont in offer_containers:
            price_el = cont.find(class_=re.compile(r"price", re.I))
            label_el = cont.find(class_=re.compile(r"title|label|name|qty|quantity", re.I)) or cont
            price = _parse_price(price_el.get_text() if price_el else "")
            if not price:
                continue
            label = label_el.get_text(strip=True)[:80] if label_el else f"عرض {len(offers)+1}"
            offers.append(PriceOffer(label=label, price=price))

    if not offers:
        price_el = soup.select_one(".product_price, [class*='product_price']")
        if price_el:
            price = _parse_price(price_el.get_text())
            if price:
                title_el = soup.select_one(".product_name, h1")
                label = title_el.get_text(strip=True)[:80] if title_el else "السعر الأساسي"
                offers.append(PriceOffer(label=label, price=price))

    if not offers:
        offers = _extract_from_js(html)

    return offers


# ─────────────────────────────────────────
# WOOCOMMERCE
# ─────────────────────────────────────────

def _scrape_woocommerce(soup: BeautifulSoup, html: str) -> list[PriceOffer]:
    offers = []
    for script in soup.find_all("script"):
        txt = script.string or ""
        var_matches = re.findall(
            r'"display_price"\s*:\s*([\d.]+).*?"attributes"\s*:\s*(\{[^}]*\})', txt, re.S
        )
        for price_str, attrs_str in var_matches:
            price = float(price_str)
            attrs = {}
            for k, v in re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', attrs_str):
                attrs[k] = v
            label = " / ".join(f"{v}" for v in attrs.values() if v) or f"تنويع {len(offers)+1}"
            offers.append(PriceOffer(label=label, price=price))

        if not offers:
            vblock = re.search(r'"variations"\s*:\s*(\[[\s\S]{0,10000}?\])', txt)
            if vblock:
                try:
                    variations = json.loads(vblock.group(1))
                    for v in variations:
                        price = float(v.get("display_price") or v.get("price") or 0)
                        if not price:
                            continue
                        attrs = v.get("attributes", {})
                        label = " / ".join(str(val) for val in attrs.values() if val) or f"تنويع {len(offers)+1}"
                        offers.append(PriceOffer(label=label, price=price))
                except Exception:
                    pass

    if not offers:
        orig_el = soup.select_one(".price del .woocommerce-Price-amount")
        sale_el = soup.select_one(".price ins .woocommerce-Price-amount") or \
                  soup.select_one(".woocommerce-Price-amount")
        price = _parse_price(sale_el.get_text() if sale_el else "")
        orig  = _parse_price(orig_el.get_text() if orig_el else "")
        if price:
            label = soup.select_one(".product_title, h1")
            label = label.get_text(strip=True)[:80] if label else "السعر الأساسي"
            offers.append(PriceOffer(label=label, price=price, original_price=orig or None))

    return offers


# ─────────────────────────────────────────
# SHOPIFY
# ─────────────────────────────────────────

def _scrape_shopify(soup: BeautifulSoup, html: str) -> list[PriceOffer]:
    offers = []
    for script in soup.find_all("script"):
        txt = script.string or ""
        m = re.search(r'ShopifyAnalytics\.meta\s*=\s*(\{[\s\S]{0,5000}?\});', txt)
        if m:
            try:
                meta = json.loads(m.group(1))
                for var in meta.get("product", {}).get("variants", []):
                    price = float(var.get("price", 0)) / 100
                    if not price:
                        continue
                    label = var.get("title") or f"خيار {len(offers)+1}"
                    offers.append(PriceOffer(label=label, price=price))
            except Exception:
                pass

        if not offers:
            m2 = re.search(r'"variants"\s*:\s*(\[[\s\S]{0,8000}?\])', txt)
            if m2:
                try:
                    variants = json.loads(m2.group(1))
                    for var in variants:
                        price = float(var.get("price", 0))
                        if price > 100:
                            price /= 100
                        if not price:
                            continue
                        label = var.get("title") or var.get("option1") or f"خيار {len(offers)+1}"
                        offers.append(PriceOffer(label=label, price=price))
                except Exception:
                    pass

    if not offers:
        price_el = soup.select_one(".price__current, .product__price, [class*='price']")
        price = _parse_price(price_el.get_text() if price_el else "")
        if price:
            label = soup.select_one("h1, .product__title")
            label = label.get_text(strip=True)[:80] if label else "السعر الأساسي"
            offers.append(PriceOffer(label=label, price=price))

    return offers


# ─────────────────────────────────────────
# GENERIC FALLBACK
# ─────────────────────────────────────────

def _scrape_generic(soup: BeautifulSoup, html: str) -> list[PriceOffer]:
    offers = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") != "Product":
                    continue
                raw_offers = item.get("offers", {})
                if isinstance(raw_offers, dict):
                    raw_offers = [raw_offers]
                for off in raw_offers:
                    price = float(off.get("price") or 0)
                    if not price:
                        continue
                    label = off.get("name") or item.get("name") or "السعر الأساسي"
                    offers.append(PriceOffer(label=label[:80], price=price))
        except Exception:
            pass

    if not offers:
        t = soup.find("meta", property="og:title")
        p = soup.find("meta", property="product:price:amount") or \
            soup.find("meta", property="og:price:amount")
        if t and p:
            try:
                price = float(p.get("content", 0))
                if price:
                    offers.append(PriceOffer(label=t.get("content", "")[:80], price=price))
            except Exception:
                pass

    return offers


# ─────────────────────────────────────────
# JS EXTRACTION
# ─────────────────────────────────────────

def _extract_from_js(html: str) -> list[PriceOffer]:
    offers = []
    patterns = [
        r'"price"\s*:\s*([\d.]+)',
        r'price\s*[=:]\s*([\d.]+)',
        r"'price'\s*:\s*([\d.]+)",
    ]
    found_prices = set()
    for pat in patterns:
        for m in re.finditer(pat, html):
            p = float(m.group(1))
            if 1 < p < 9_999_999 and p not in found_prices:
                found_prices.add(p)
    for i, p in enumerate(sorted(found_prices)[:5]):
        offers.append(PriceOffer(label=f"سعر {i+1}", price=p))
    return offers


# ─────────────────────────────────────────
# PRICE PARSER
# ─────────────────────────────────────────

def _parse_price(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.,]", "", text.strip())
    if re.search(r",\d{1,2}$", cleaned):
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        val = float(cleaned)
        return val if 0 < val < 9_999_999 else None
    except ValueError:
        return None


# ─────────────────────────────────────────
# WORKER LOOP — يشتغل في الخلفية
# ─────────────────────────────────────────

def _build_alert_message(url: str, title: str, changes: list[dict]) -> str:
    lines = [f"🔔 *تغيير سعر!*", f"🌐 [{title or url}]({url})", ""]
    for ch in changes:
        arrow = "📈" if ch["diff"] > 0 else "📉"
        direction = "ارتفع" if ch["diff"] > 0 else "انخفض"
        lines.append(
            f"{arrow} *{ch['label']}*\n"
            f"   كان: `{ch['old']:.2f}` ← بقى: `{ch['new']:.2f}`\n"
            f"   {direction} بنسبة {abs(ch['pct']):.1f}%"
        )
    return "\n".join(lines)


async def check_all_urls():
    """يفحص كل الروابط المسجّلة ويبعت تنبيهات"""
    from bot import send_alert  # lazy import لتجنب circular

    rows = db.get_all_urls_with_users()
    if not rows:
        logger.info("مفيش روابط مسجّلة بعد")
        return

    logger.info("بيفحص %d رابط...", len(rows))

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=20,
        limits=httpx.Limits(max_connections=5),
    ) as client:

        for row in rows:
            url_id   = row["id"]
            url      = row["url"]
            user_id  = row["user_id"]
            chat_id  = row["telegram_chat_id"]

            logger.info("فحص: %s", url)
            result = await scrape_product(url, client)

            if result.error or not result.offers:
                logger.warning("خطأ أو لا يوجد أسعار: %s", url)
                await asyncio.sleep(1)
                continue

            changes = []
            for offer in result.offers:
                offer_key = f"{offer.label}"
                old_price = db.get_last_price(url_id, offer_key)
                db.save_price(url_id, offer_key, offer.price)

                if old_price is not None and abs(old_price - offer.price) > 0.01:
                    diff = offer.price - old_price
                    pct  = (diff / old_price) * 100
                    changes.append({
                        "label": offer.label,
                        "old": old_price,
                        "new": offer.price,
                        "diff": diff,
                        "pct": pct,
                    })

            if changes:
                msg = _build_alert_message(url, result.title, changes)
                await send_alert(chat_id, msg)
                db.log_alert(user_id, url, msg)
                logger.info("✅ تنبيه أُرسل لـ chat_id=%s", chat_id)

            await asyncio.sleep(2)

    logger.info("✅ دورة الفحص انتهت — الدورة الجاية بعد %d ثانية", CHECK_INTERVAL)


async def run_worker():
    logger.info("=== Price Scraper Worker شغّال ===")
    while True:
        start = time.monotonic()
        try:
            await check_all_urls()
        except Exception as e:
            logger.error("خطأ في الـ worker: %s", e, exc_info=True)
        elapsed = time.monotonic() - start
        await asyncio.sleep(max(0, CHECK_INTERVAL - elapsed))


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(run_worker())
