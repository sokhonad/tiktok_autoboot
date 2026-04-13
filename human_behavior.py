"""
human_behavior.py — Simulation de comportement humain pour Playwright.
Mouvements souris Bézier, frappe humaine, délais gaussiens, scroll naturel.
"""

import asyncio
import math
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


def _bezier_point(t: float, p0: tuple, p1: tuple, p2: tuple, p3: tuple) -> tuple[float, float]:
    """
    Calcule un point sur une courbe de Bézier cubique.

    Args:
        t: Paramètre [0, 1]
        p0..p3: Points de contrôle (x, y)

    Returns:
        Tuple (x, y) du point sur la courbe
    """
    mt = 1 - t
    x = (mt**3 * p0[0] + 3 * mt**2 * t * p1[0]
         + 3 * mt * t**2 * p2[0] + t**3 * p3[0])
    y = (mt**3 * p0[1] + 3 * mt**2 * t * p1[1]
         + 3 * mt * t**2 * p2[1] + t**3 * p3[1])
    return x, y


async def human_mouse_move(page: "Page", target_x: int, target_y: int) -> None:
    """
    Déplace la souris vers (target_x, target_y) avec une courbe de Bézier cubique.
    Simule le mouvement naturel humain avec légère variation de vitesse.

    Args:
        page: Instance Playwright Page
        target_x: Coordonnée X de destination
        target_y: Coordonnée Y de destination
    """
    # Position actuelle (estimée depuis le centre de la page si inconnue)
    try:
        current = await page.evaluate("() => ({x: window._mouseX || 540, y: window._mouseY || 960})")
        start_x, start_y = current.get("x", 540), current.get("y", 960)
    except Exception:
        start_x, start_y = random.randint(400, 680), random.randint(800, 1100)

    # Points de contrôle Bézier avec décalage aléatoire pour courbe naturelle
    ctrl_offset = random.randint(50, 200)
    p0 = (start_x, start_y)
    p1 = (start_x + random.randint(-ctrl_offset, ctrl_offset),
          start_y + random.randint(-ctrl_offset, ctrl_offset))
    p2 = (target_x + random.randint(-ctrl_offset, ctrl_offset),
          target_y + random.randint(-ctrl_offset, ctrl_offset))
    p3 = (target_x, target_y)

    # Nombre de steps : plus la distance est grande, plus il y en a
    distance = math.sqrt((target_x - start_x)**2 + (target_y - start_y)**2)
    steps = max(15, min(60, int(distance / 10)))

    for i in range(steps + 1):
        t = i / steps
        # Easing : accélération/décélération naturelle (ease-in-out)
        t_eased = t * t * (3 - 2 * t)
        x, y = _bezier_point(t_eased, p0, p1, p2, p3)

        await page.mouse.move(int(x), int(y))
        # Délai variable entre les steps (mouvement non uniforme)
        await asyncio.sleep(random.uniform(0.005, 0.025))

    # Mise à jour de la position JS
    await page.evaluate(f"() => {{ window._mouseX = {target_x}; window._mouseY = {target_y}; }}")


async def human_type(page: "Page", selector: str, text: str) -> None:
    """
    Tape un texte dans un champ avec des délais inter-caractères humains.
    Varie entre 50ms et 180ms par caractère avec quelques pauses naturelles.

    Args:
        page: Instance Playwright Page
        selector: Sélecteur CSS de l'élément
        text: Texte à taper
    """
    element = page.locator(selector)
    await element.click()
    await asyncio.sleep(random.uniform(0.2, 0.5))

    for i, char in enumerate(text):
        await element.press(char)

        # Délai de base entre 50-180ms
        delay = random.gauss(100, 35)
        delay = max(50, min(180, delay)) / 1000

        # Pause occasionnelle plus longue (simulation réflexion/erreur)
        if random.random() < 0.04:  # 4% de chance
            delay += random.uniform(0.3, 0.8)

        await asyncio.sleep(delay)


async def human_delay(min_ms: int = 500, max_ms: int = 2000) -> None:
    """
    Pause gaussienne simulant un délai de réflexion humain.

    Args:
        min_ms: Délai minimum en millisecondes
        max_ms: Délai maximum en millisecondes
    """
    mean = (min_ms + max_ms) / 2
    std = (max_ms - min_ms) / 6  # ~99.7% dans l'intervalle
    delay_ms = random.gauss(mean, std)
    delay_ms = max(min_ms, min(max_ms, delay_ms))
    await asyncio.sleep(delay_ms / 1000)


async def scroll_naturally(page: "Page", distance: int = 300, direction: str = "down") -> None:
    """
    Effectue un scroll naturel avec accélération et décélération.

    Args:
        page: Instance Playwright Page
        distance: Distance de scroll en pixels
        direction: 'down' ou 'up'
    """
    sign = 1 if direction == "down" else -1
    steps = random.randint(5, 10)

    for i in range(steps):
        # Accélération sinusoïdale
        progress = (i + 1) / steps
        step_size = distance / steps * math.sin(progress * math.pi)
        await page.mouse.wheel(0, sign * step_size)
        await asyncio.sleep(random.uniform(0.05, 0.15))


async def random_micro_movement(page: "Page") -> None:
    """
    Effectue de micro-mouvements aléatoires pour simuler la présence humaine.
    À appeler pendant les temps d'attente pour paraître moins bot.
    """
    for _ in range(random.randint(2, 5)):
        # Micro-déplacement dans un rayon de 30px
        current_x = random.randint(200, 880)
        current_y = random.randint(300, 1620)
        offset_x = random.randint(-30, 30)
        offset_y = random.randint(-30, 30)

        await page.mouse.move(current_x + offset_x, current_y + offset_y)
        await asyncio.sleep(random.uniform(0.1, 0.4))
