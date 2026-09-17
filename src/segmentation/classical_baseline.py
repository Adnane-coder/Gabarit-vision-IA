"""
classical_baseline.py

Reimplementation du systeme classique (Raspberry Pi + OpenCV) documente dans le
rapport PFE precedent (SARTEX). Ce module est volontairement conserve tel quel
(Canny + approxPolyDP + calibration par objet de reference) pour servir de
POINT DE COMPARAISON QUANTITATIF face au futur pipeline IA (U-Net + points-cles).

Ne pas "ameliorer" ce fichier avec des techniques modernes : il doit rester le
reflet fidele de l'existant pour que le rapport de stage puisse chiffrer le gain
apporte par la modernisation.
"""

from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass, field


@dataclass
class PieceDetection:
    """Une piece detectee par le pipeline classique."""
    contour: np.ndarray
    polygon: np.ndarray          # points apres approxPolyDP
    bbox: tuple                  # (x, y, w, h)
    area_px: float
    perimeter_px: float


@dataclass
class BaselineResult:
    image_shape: tuple
    pieces: list = field(default_factory=list)
    scale_cm_per_px: float | None = None
    calibration_found: bool = False


def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Impossible de lire l'image: {path}")
    return img


def preprocess_classical(img: np.ndarray) -> np.ndarray:
    """Pipeline classique: niveaux de gris -> flou -> Canny.
    Reproduit fidelement l'etape documentee dans le rapport (chap.3).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    # dilatation legere pour fermer les contours discontinus (texte / bruit papier)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    return edges


def find_pieces(
    edges: np.ndarray,
    min_area_px: float = 2000.0,
    max_area_ratio: float = 0.5,
    scale_cm_per_px: float | None = None,
    min_area_cm2: float = 15.0,
) -> list[PieceDetection]:
    """Detecte les contours et les approxime en polygones (approxPolyDP).

    IMPORTANT : utilise RETR_TREE (et non RETR_EXTERNAL) car les plans de coupe
    ont souvent un cadre complet autour de toute la feuille. Avec RETR_EXTERNAL,
    ce cadre est vu comme LE contour externe et toutes les pieces a l'interieur
    sont ignorees (considerees "imbriquees" dedans). RETR_TREE recupere tous les
    niveaux d'imbrication, donc les pieces individuelles sont bien retournees.

    Deux sources de bruit supplementaires sont filtrees :
    1. Les petits symboles losange (reperes de montage) : filtres par aire
       physique (min_area_cm2) plutot que par aire en pixels, pour rester valide
       quel que soit le DPI de rasterisation.
    2. Les doublons trait-plein/trait-pointille : chaque piece est dessinee avec
       un bord de coupe (plein) ET une marge de couture (pointille) tres proches,
       ce qui cree deux contours quasi-identiques (parent/enfant dans la hierarchie
       RETR_TREE) pour la meme piece. On ne garde que le contour parent (le plus
       exterieur des deux) quand leurs aires sont proches (>80%).

    Args:
        min_area_px: seuil de bruit en pixels, utilise seulement si scale_cm_per_px
            n'est pas fourni (retro-compatibilite).
        max_area_ratio: filtre les contours du type "cadre de la feuille entiere"
            (relatif a la taille de l'image).
        scale_cm_per_px: si fourni, active le filtrage par aire physique reelle
            (min_area_cm2) au lieu du filtrage en pixels bruts.
        min_area_cm2: aire minimale reelle (cm2) pour qu'un contour soit considere
            comme une piece (et non un repere/symbole). 15 cm2 exclut les losanges
            de repere (~15-17 cm2 mesures) tout en gardant les plus petites vraies
            pieces (ex. PATCH, plusieurs dizaines de cm2).
    """
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    img_area = edges.shape[0] * edges.shape[1]
    max_area_px = img_area * max_area_ratio
    hierarchy = hierarchy[0] if hierarchy is not None else []

    # --- Etape 1 : filtre d'aire (physique si echelle connue, sinon en pixels) ---
    candidates = []  # (index, contour, area_px)
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area > max_area_px:
            continue
        if scale_cm_per_px is not None:
            area_cm2 = area * (scale_cm_per_px ** 2)
            if area_cm2 < min_area_cm2:
                continue
        else:
            if area < min_area_px:
                continue
        candidates.append((i, cnt, area))

    # --- Etape 2 : dedup hierarchique (trait plein vs trait pointille) ---
    kept_indices = set(i for i, _, _ in candidates)
    area_by_idx = {i: a for i, _, a in candidates}
    discarded = set()
    for i, cnt, area in candidates:
        parent = hierarchy[i][3] if len(hierarchy) > i else -1
        if parent in kept_indices and parent not in discarded:
            parent_area = area_by_idx.get(parent)
            if parent_area and area / parent_area > 0.80:
                # ce contour est un doublon (pointille) de son parent (plein) -> on l'ecarte
                discarded.add(i)

    pieces: list[PieceDetection] = []
    for i, cnt, area in candidates:
        if i in discarded:
            continue
        perimeter = cv2.arcLength(cnt, True)
        epsilon = 0.01 * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        x, y, w, h = cv2.boundingRect(cnt)
        pieces.append(
            PieceDetection(
                contour=cnt,
                polygon=approx.reshape(-1, 2),
                bbox=(x, y, w, h),
                area_px=area,
                perimeter_px=perimeter,
            )
        )
    return pieces


def calibrate_with_reference_card(img: np.ndarray, pieces: list[PieceDetection]):
    """Calibration classique par carte bancaire (ratio ~1.586).
    Cherche parmi les pieces detectees un rectangle dont le ratio L/l est proche
    de celui d'une carte bancaire standard (85.60 x 53.98 mm).
    Retourne (scale_cm_per_px, found_bool).
    """
    CARD_RATIO = 85.60 / 53.98
    CARD_WIDTH_CM = 8.560

    best_diff = float("inf")
    best_scale = None
    for p in pieces:
        x, y, w, h = p.bbox
        if h == 0:
            continue
        ratio = max(w, h) / min(w, h)
        diff = abs(ratio - CARD_RATIO)
        if diff < best_diff and diff < 0.15:  # tolerance de forme
            best_diff = diff
            best_scale = CARD_WIDTH_CM / max(w, h)

    if best_scale is not None:
        return best_scale, True
    return None, False


def run_baseline(image_path: str, min_area_px: float = 2000.0) -> BaselineResult:
    """Point d'entree unique du baseline classique, pour reproduire
    exactement ce que faisait le systeme Raspberry Pi + OpenCV original.
    """
    img = load_image(image_path)
    edges = preprocess_classical(img)
    pieces = find_pieces(edges, min_area_px=min_area_px)
    scale, found = calibrate_with_reference_card(img, pieces)

    return BaselineResult(
        image_shape=img.shape,
        pieces=pieces,
        scale_cm_per_px=scale,
        calibration_found=found,
    )


def draw_result(img: np.ndarray, result: BaselineResult) -> np.ndarray:
    """Dessine les polygones detectes sur une copie de l'image, pour inspection visuelle."""
    out = img.copy()
    for p in result.pieces:
        cv2.polylines(out, [p.polygon], isClosed=True, color=(0, 255, 0), thickness=2)
        for (x, y) in p.polygon:
            cv2.circle(out, (int(x), int(y)), 4, (0, 0, 255), -1)
    return out
