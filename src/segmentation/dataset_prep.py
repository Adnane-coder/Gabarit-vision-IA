"""
dataset_prep.py

Prepare les donnees d'entrainement pour le futur modele U-Net, a partir des
annotations manuelles (polygones de points de contour).

CHOIX TECHNIQUE IMPORTANT : masques a 2 canaux (interieur + frontiere)
-----------------------------------------------------------------------
Le probleme principal du baseline classique etait de separer des pieces qui se
TOUCHENT sur le plan de coupe (cf. Phase 1 du projet, bug RETR_EXTERNAL puis
doublons trait plein/pointille). Un U-Net a une seule sortie binaire
("piece" vs "fond") aurait exactement le meme probleme : deux pieces adjacentes
fusionneraient en une seule tache dans le masque.

La solution standard (utilisee par ex. en segmentation de cellules qui se
touchent, meme probleme geometrique) est d'entrainer le modele a predire
DEUX canaux :
  1. INTERIEUR de la piece (la piece retrecie de quelques pixels)
  2. FRONTIERE de la piece (une bande fine autour du contour)

A l'inference, on fait : masque_final = interieur ET NON(frontiere).
Meme si deux pieces se touchent, leurs frontieres (qui se chevauchent a
l'endroit du contact) les separent quand on soustrait les frontieres des
interieurs -> les composantes connexes redeviennent des pieces individuelles.

Ce module genere ces masques a partir des polygones annotes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class TraceeMasks:
    tracee_name: str
    image: np.ndarray          # image originale (BGR), redimensionnee a TARGET_SIZE
    mask_interieur: np.ndarray  # 0/255, meme taille que image
    mask_frontiere: np.ndarray  # 0/255, meme taille que image
    scale_cm_per_px: float      # a la resolution de TARGET_SIZE (pas la resolution originale)
    n_pieces: int


def generate_masks(
    image_original: np.ndarray,
    annotations_path: str,
    scale_cm_per_px_original: float,
    target_max_dim: int = 1536,
    boundary_thickness_px: int = 3,
    erosion_px: int = 2,
) -> TraceeMasks:
    """Genere les masques interieur/frontiere pour UN tracé complet.

    Args:
        image_original: image rasterisee du tracé, pleine resolution (BGR).
        annotations_path: fichier JSON d'annotations (points_original_px en
            coordonnees de l'image originale).
        scale_cm_per_px_original: echelle cm/px a la resolution originale.
        target_max_dim: les masques et l'image sont redimensionnes pour que le
            plus grand cote fasse cette taille (limite la memoire necessaire a
            l'entrainement ; 1536px reste largement suffisant pour la precision
            visee avec une tolerance de +/-3cm).
        boundary_thickness_px: epaisseur de la bande "frontiere", a la
            resolution cible (apres redimensionnement).
        erosion_px: de combien de pixels on retrecit chaque piece pour obtenir
            son "interieur" (a la resolution cible).
    """
    with open(annotations_path, encoding='utf-8') as f:
        data = json.load(f)

    h_orig, w_orig = image_original.shape[:2]
    scale_resize = target_max_dim / max(h_orig, w_orig)
    if scale_resize > 1.0:
        scale_resize = 1.0  # ne jamais agrandir une image plus petite que la cible

    new_w, new_h = int(w_orig * scale_resize), int(h_orig * scale_resize)
    image_resized = cv2.resize(image_original, (new_w, new_h), interpolation=cv2.INTER_AREA)
    scale_cm_per_px_target = scale_cm_per_px_original / scale_resize

    mask_interieur = np.zeros((new_h, new_w), dtype=np.uint8)
    mask_frontiere = np.zeros((new_h, new_w), dtype=np.uint8)

    kernel_erosion = np.ones((erosion_px * 2 + 1, erosion_px * 2 + 1), np.uint8)

    for piece in data['pieces']:
        pts = np.array(piece['points_original_px'], dtype=np.float32) * scale_resize
        pts = pts.astype(np.int32)

        piece_mask = np.zeros((new_h, new_w), dtype=np.uint8)
        cv2.fillPoly(piece_mask, [pts], 255)

        # interieur = piece erodee (retrecie), pour laisser une marge a la frontiere
        interieur = cv2.erode(piece_mask, kernel_erosion)
        mask_interieur = cv2.bitwise_or(mask_interieur, interieur)

        # frontiere = contour de la piece, epaissi
        contour_mask = np.zeros((new_h, new_w), dtype=np.uint8)
        cv2.polylines(contour_mask, [pts], isClosed=True, color=255, thickness=boundary_thickness_px)
        mask_frontiere = cv2.bitwise_or(mask_frontiere, contour_mask)

    return TraceeMasks(
        tracee_name=data.get('tracé', Path(annotations_path).stem),
        image=image_resized,
        mask_interieur=mask_interieur,
        mask_frontiere=mask_frontiere,
        scale_cm_per_px=scale_cm_per_px_target,
        n_pieces=len(data['pieces']),
    )


def masks_to_instances(
    mask_interieur: np.ndarray,
    mask_frontiere: np.ndarray,
    min_area_px: int = 150,
) -> tuple[np.ndarray, int]:
    """Reconstruit des instances de pieces individuelles a partir des 2 masques
    (technique interieur - frontiere -> composantes connexes).

    min_area_px filtre les fragments trop petits pour etre une vraie piece :
    l'erosion peut occasionnellement couper une toute petite piece en 2
    morceaux dont un minuscule (quelques dizaines de px) - ce n'est pas une
    vraie instance, juste un artefact de la technique.

    Retourne (masque_labels, nombre_instances) ; masque_labels a un entier
    different par piece (0 = fond), avec les fragments filtres remis a 0.
    """
    final = cv2.bitwise_and(mask_interieur, cv2.bitwise_not(mask_frontiere))
    n_labels, labels = cv2.connectedComponents(final, connectivity=8)

    n_instances = 0
    clean_labels = np.zeros_like(labels)
    for i in range(1, n_labels):
        size = np.sum(labels == i)
        if size >= min_area_px:
            n_instances += 1
            clean_labels[labels == i] = n_instances

    return clean_labels, n_instances


def save_masks(masks: TraceeMasks, out_dir: str) -> None:
    """Sauvegarde l'image et les 2 masques en PNG, pour inspection et pour
    l'entrainement (charges ensuite par le DataLoader PyTorch)."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path / f"{masks.tracee_name}_image.png"), masks.image)
    cv2.imwrite(str(out_path / f"{masks.tracee_name}_interieur.png"), masks.mask_interieur)
    cv2.imwrite(str(out_path / f"{masks.tracee_name}_frontiere.png"), masks.mask_frontiere)
