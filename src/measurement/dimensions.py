"""
dimensions.py

Calcule les dimensions physiques reelles (cm) d'une piece a partir de son polygone
de points de contour (annote a la main via l'outil d'annotation) et de l'echelle
cm/pixel du tracé d'origine.

Ce module ne fait aucune hypothese sur la forme de la piece (rectangle, courbe,
etc.) : les mesures extraites sont generiques et s'appliquent a n'importe quel
polygone ferme.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class PieceMeasurements:
    """Mesures physiques d'une piece, toutes en cm (ou cm2 pour l'aire)."""
    largeur_cm: float       # etendue en x (bounding box)
    hauteur_cm: float       # etendue en y (bounding box)
    perimetre_cm: float     # longueur totale du contour
    aire_cm2: float         # aire du polygone
    diagonale_cm: float     # plus grande distance entre 2 points du contour
    n_points: int


def polygon_area(points_px: list[list[float]]) -> float:
    """Aire d'un polygone ferme via la formule du lacet (shoelace formula), en px^2."""
    n = len(points_px)
    area = 0.0
    for i in range(n):
        x1, y1 = points_px[i]
        x2, y2 = points_px[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def polygon_perimeter(points_px: list[list[float]]) -> float:
    """Perimetre d'un polygone ferme, en px."""
    n = len(points_px)
    total = 0.0
    for i in range(n):
        x1, y1 = points_px[i]
        x2, y2 = points_px[(i + 1) % n]
        total += math.hypot(x2 - x1, y2 - y1)
    return total


def polygon_bbox(points_px: list[list[float]]) -> tuple[float, float]:
    """Largeur et hauteur de la boite englobante (bounding box), en px."""
    xs = [p[0] for p in points_px]
    ys = [p[1] for p in points_px]
    return max(xs) - min(xs), max(ys) - min(ys)


def polygon_diagonal(points_px: list[list[float]]) -> float:
    """Plus grande distance entre deux points du contour (diagonale), en px.
    Utile comme mesure robuste de la 'taille' globale d'une piece, independante
    de son orientation.
    """
    n = len(points_px)
    max_dist = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            x1, y1 = points_px[i]
            x2, y2 = points_px[j]
            d = math.hypot(x2 - x1, y2 - y1)
            if d > max_dist:
                max_dist = d
    return max_dist


def measure_piece(points_px: list[list[float]], scale_cm_per_px: float) -> PieceMeasurements:
    """Calcule toutes les mesures physiques d'une piece a partir de son polygone
    (en pixels de l'image originale) et de l'echelle du tracé.
    """
    w_px, h_px = polygon_bbox(points_px)
    perimeter_px = polygon_perimeter(points_px)
    area_px2 = polygon_area(points_px)
    diagonal_px = polygon_diagonal(points_px)

    return PieceMeasurements(
        largeur_cm=round(w_px * scale_cm_per_px, 2),
        hauteur_cm=round(h_px * scale_cm_per_px, 2),
        perimetre_cm=round(perimeter_px * scale_cm_per_px, 2),
        aire_cm2=round(area_px2 * (scale_cm_per_px ** 2), 2),
        diagonale_cm=round(diagonal_px * scale_cm_per_px, 2),
        n_points=len(points_px),
    )
