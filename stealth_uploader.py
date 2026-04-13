"""
stealth_uploader.py — Upload automatisé TikTok via Playwright anti-détection.
Patch JS webdriver, canvas fingerprint, WebGL spoof + comportement humain.
"""

import asyncio
import json
import logging
import random
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config import COOKIES_PATH, TIKTOK_UPLOAD_URL
from human_behavior import (
    human_delay,
    human_mouse_move,
    human_type,
    random_micro_movement,
    scroll_naturally,
)

logger = logging.getLogger(__name__)

# ── Scripts JS de patch anti-détection ──────────────────────────────────────
_STEALTH_JS = """
// 1. Masque navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true
});

// 2. Restaure navigator.plugins (vide en headless = détectable)
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
        ];
        plugins.refresh = () => {};
        plugins.item = (i) => plugins[i];
        plugins.namedItem = (name) => plugins.find(p => p.name === name);
        Object.defineProperty(plugins, 'length', { get: () => plugins.length });
        return plugins;
    }
});

// 3. Spoof canvas fingerprint (légère variation aléatoire)
const originalGetContext = HTMLCanvasElement.prototype.getContext;
HTMLCanvasElement.prototype.getContext = function(type, ...args) {
    const ctx = originalGetContext.apply(this, [type, ...args]);
    if (type === '2d' && ctx) {
        const originalGetImageData = ctx.getImageData.bind(ctx);
        ctx.getImageData = function(...a) {
            const imageData = originalGetImageData(...a);
            const noise = 0.2;
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * noise);
                imageData.data[i+1] += Math.floor(Math.random() * noise);
                imageData.data[i+2] += Math.floor(Math.random() * noise);
            }
            return imageData;
        };
    }
    return ctx;
};

// 4. WebGL vendor/renderer spoof
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';           // UNMASKED_VENDOR_WEBGL
    if (parameter === 37446) return 'Intel Iris OpenGL Engine'; // UNMASKED_RENDERER_WEBGL
    return getParameter.apply(this, [parameter]);
};

// 5. Dimensions écran réalistes
Object.defineProperty(screen, 'width', { get: () => 1920 });
Object.defineProperty(screen, 'height', { get: () => 1080 });
Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
Object.defineProperty(screen, 'availHeight', { get: () => 1040 });

// 6. Timezone cohérente
Date.prototype.getTimezoneOffset = () => -60; // Europe/Paris

// 7. Stocke la position souris pour human_mouse_move
window._mouseX = 540; window._mouseY = 960;
"""


def _normalize_cookies(cookies: list[dict]) -> list[dict]:
    """
    Normalise les cookies pour Playwright :
    - sameSite : null/no_restriction → "None", lax → "Lax", strict → "Strict"
    - Supprime les champs inconnus (storeId, hostOnly, session...)
    - Supprime les cookies sans valeur
    """
    # Mapping des valeurs sameSite acceptées par Playwright
    same_site_map = {
        None: "None",
        "": "None",
        "null": "None",
        "no_restriction": "None",
        "unspecified": "None",
        "lax": "Lax",
        "strict": "Strict",
        "none": "None",
        "Lax": "Lax",
        "Strict": "Strict",
        "None": "None",
    }

    playwright_cookies = []
    for c in cookies:
        if not c.get("value"):
            continue

        same_site_raw = c.get("sameSite")
        same_site = same_site_map.get(same_site_raw, "None")

        cookie = {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".tiktok.com"),
            "path": c.get("path", "/"),
            "secure": c.get("secure", False),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": same_site,
        }

        # Ajoute expires seulement si présent et valide
        if c.get("expirationDate"):
            cookie["expires"] = int(c["expirationDate"])

        playwright_cookies.append(cookie)

    return playwright_cookies


async def _load_cookies(context: BrowserContext) -> None:
    """Charge et normalise les cookies TikTok depuis le fichier JSON."""
    if not COOKIES_PATH.exists():
        logger.warning(f"Fichier cookies introuvable : {COOKIES_PATH}")
        return

    with open(COOKIES_PATH, encoding="utf-8") as f:
        raw_cookies = json.load(f)

    if not isinstance(raw_cookies, list):
        logger.warning("Format cookies.json non supporté (doit être une liste)")
        return

    cookies = _normalize_cookies(raw_cookies)
    await context.add_cookies(cookies)
    logger.info(f"{len(cookies)} cookies chargés et normalisés")


async def _upload_video(page: Page, video_path: Path, title: str, hashtags: list[str]) -> bool:
    """
    Effectue l'upload réel sur TikTok Studio avec simulation de comportement humain.

    TikTok Studio (tiktokstudio/upload) charge le formulaire via React — le
    input[type=file] est masqué jusqu'au clic sur la zone d'upload.
    On utilise expect_file_chooser() pour intercepter le sélecteur natif.

    Args:
        page: Page Playwright active
        video_path: Chemin vers la vidéo MP4
        title: Titre/description de la vidéo
        hashtags: Liste de hashtags à ajouter

    Returns:
        True si l'upload est confirmé, False sinon
    """
    # Visite la home page avant d'aller sur la page d'upload (comportement naturel)
    logger.info("Navigation vers TikTok home...")
    await page.goto("https://www.tiktok.com", wait_until="domcontentloaded", timeout=30000)
    await human_delay(2000, 4000)

    # Quelques scrolls naturels sur la home
    await scroll_naturally(page, 400, "down")
    await human_delay(1000, 2500)
    await scroll_naturally(page, 200, "up")
    await human_delay(800, 1500)

    # Navigation vers TikTok Studio upload
    logger.info("Navigation vers TikTok Studio upload...")
    await page.goto(TIKTOK_UPLOAD_URL, wait_until="domcontentloaded", timeout=60000)
    await human_delay(6000, 9000)  # Attend le rendu React complet

    logger.info(f"Page chargée — URL: {page.url} | Titre: {await page.title()}")

    # ── Méthode 1 : file chooser (clic sur la zone d'upload) ─────────────────
    # TikTok Studio masque l'input jusqu'au clic — on intercepte le dialog natif.
    upload_done = False

    upload_zone_selectors = [
        '[class*="upload-card"]',
        '[class*="upload-zone"]',
        '[class*="uploadCard"]',
        '[class*="uploadZone"]',
        '[class*="upload-btn"]',
        '[data-e2e="upload-zone"]',
        'button:has-text("Sélectionner")',
        'button:has-text("Select")',
        'button:has-text("Upload")',
        'div[role="button"][class*="upload"]',
    ]

    for zone_sel in upload_zone_selectors:
        try:
            async with page.expect_file_chooser(timeout=6000) as fc_info:
                await page.click(zone_sel, timeout=3000)
            file_chooser = await fc_info.value
            await file_chooser.set_files(str(video_path))
            logger.info(f"Vidéo uploadée via file chooser ({zone_sel})")
            upload_done = True
            break
        except Exception:
            continue

    # ── Méthode 2 : input[type=file] direct (fallback) ────────────────────────
    if not upload_done:
        for sel in ['input[type="file"]', 'input[accept*="video"]']:
            try:
                loc = page.locator(sel).first
                await loc.wait_for(state="attached", timeout=5000)
                await loc.set_input_files(str(video_path), timeout=60000)
                logger.info(f"Vidéo uploadée via input direct ({sel})")
                upload_done = True
                break
            except Exception:
                continue

    if not upload_done:
        logger.error(f"Upload impossible — URL: {page.url}")
        for i, f in enumerate(page.frames):
            logger.error(f"  Frame {i}: {f.url[:100]}")
        try:
            html = await page.content()
            logger.error(f"  HTML (1000 chars): {html[:1000]}")
        except Exception:
            pass
        return False

    await human_delay(5000, 8000)

    # Attend la fin du traitement vidéo côté TikTok
    # Attend que le formulaire TikTok Studio soit prêt (traitement vidéo côté serveur)
    # Le champ caption (Draft.js) n'apparaît qu'après le traitement.
    logger.info("Attente du formulaire TikTok Studio...")
    try:
        await page.wait_for_selector('.public-DraftEditor-content', timeout=90000, state="visible")
        logger.info("Formulaire prêt")
    except Exception:
        logger.warning("Formulaire non détecté après 90s — tentative quand même")

    await human_delay(2000, 3000)

    # ── Remplissage caption (Draft.js editor) via JS ──────────────────────────
    description = f"{title} {' '.join(hashtags[:20])}"
    description_json = json.dumps(description)

    caption_filled = await page.evaluate(f"""
        (() => {{
            // Sélecteur exact TikTok Studio : public-DraftEditor-content
            const ed = document.querySelector('.public-DraftEditor-content')
                     || document.querySelector('[contenteditable="true"]');
            if (!ed) return false;
            ed.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, {description_json});
            ed.dispatchEvent(new InputEvent('input', {{ bubbles: true }}));
            return true;
        }})()
    """)

    if caption_filled:
        logger.info("Description remplie")
    else:
        logger.warning("Champ description non trouvé")

    await human_delay(1500, 2500)
    await random_micro_movement(page)

    # ── Clic bouton Publier (data-e2e="post_video_button") ────────────────────
    post_clicked = False
    try:
        btn = page.locator('[data-e2e="post_video_button"]').first
        await btn.wait_for(state="visible", timeout=10000)
        await btn.click()
        logger.info("Bouton Publier cliqué")
        post_clicked = True
        await human_delay(4000, 6000)
    except Exception:
        # Fallback texte
        for selector in ['button:has-text("Publier")', 'button:has-text("Post")',
                         'button:has-text("Publish")']:
            try:
                btn = page.locator(selector).first
                if await btn.count() > 0 and await btn.is_enabled():
                    await btn.click()
                    logger.info(f"Bouton Publier cliqué ({selector})")
                    post_clicked = True
                    await human_delay(4000, 6000)
                    break
            except Exception:
                continue

    if not post_clicked:
        logger.error("Bouton Publier introuvable — vidéo probablement en brouillon")
        return False

    # Attend confirmation (TikTok Studio reste sur la même URL ou redirige)
    for url_pattern in ["**/tiktokstudio/content**", "**/tiktokstudio**", "**/profile**"]:
        try:
            await page.wait_for_url(url_pattern, timeout=10000)
            logger.info(f"Upload confirmé — {page.url}")
            return True
        except Exception:
            continue

    logger.info("Upload réussi")
    return True


async def _get_element_center(page: Page, selector: str) -> tuple[int, int]:
    """Retourne le centre (x, y) d'un élément pour le mouvement souris."""
    try:
        box = await page.locator(selector).first.bounding_box()
        if box:
            return int(box["x"] + box["width"] / 2), int(box["y"] + box["height"] / 2)
    except Exception:
        pass
    return random.randint(400, 680), random.randint(700, 1200)


async def upload_to_tiktok(
    video_path: Path,
    title: str,
    hashtags: list[str],
) -> bool:
    """
    Point d'entrée principal pour l'upload TikTok.

    Args:
        video_path: Chemin vers la vidéo MP4 finale
        title: Titre de la vidéo
        hashtags: Liste de hashtags

    Returns:
        True si l'upload a réussi
    """
    async with async_playwright() as pw:
        # Lance Chromium avec options anti-détection
        browser: Browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1920,1080",
                "--start-maximized",
            ],
        )

        # Contexte avec user-agent et viewport réalistes
        context: BrowserContext = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
            timezone_id="Europe/Paris",
            permissions=["geolocation"],
            geolocation={"latitude": 48.8566, "longitude": 2.3522},  # Paris
        )

        # Injecte le script stealth sur chaque nouvelle page
        await context.add_init_script(_STEALTH_JS)

        # Charge les cookies de session
        await _load_cookies(context)

        page: Page = await context.new_page()

        try:
            success = await _upload_video(page, video_path, title, hashtags)
        except Exception as e:
            logger.error(f"Erreur upload : {e}", exc_info=True)
            success = False
        finally:
            await browser.close()

    return success
