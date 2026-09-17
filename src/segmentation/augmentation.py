"""
augmentation.py

Phase 2 du plan U-Net : genere le jeu de donnees d'entrainement final, a partir
des masques (Phase 1), par deux mecanismes complementaires :

1. DECOUPAGE EN PATCHS (patch extraction)
   Les tracés complets font ~1500px de cote, bien plus grand que ce qu'un U-Net
   traite typiquement en entrainement (memoire GPU limitee). On decoupe donc
   chaque tracé en patchs de taille fixe (par defaut 512x512), centres soit sur
   une piece (pour garantir que chaque piece apparait dans le jeu de donnees),
   soit a une position aleatoire (pour la diversite de fond/texte/bruit).
   Ca a aussi un effet positif secondaire important : 4 tracés deviennent
   plusieurs centaines de patchs d'entrainement.

2. AUGMENTATION (albumentations)
   Chaque patch peut etre transforme aleatoirement (rotation, symetrie,
   luminosite, bruit...) pour multiplier artificiellement la variete visuelle
   et limiter le surapprentissage sur nos 4 tracés sources. Utilise la
   librairie 'albumentations', standard du secteur pour la vision par
   ordinateur : elle applique EXACTEMENT la meme transformation geometrique a
   l'image et a ses masques simultanement (garantit qu'ils restent alignes
   apres transformation - un desalignement image/masque est l'erreur la plus
   frequente et la plus silencieuse dans ce genre de pipeline).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import albumentations as A
import cv2
import numpy as np

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from segmentation.dataset_prep import TraceeMasks, masks_to_instances


@dataclass
class Patch:
    image: np.ndarray
    mask_interieur: np.ndarray
    mask_frontiere: np.ndarray
    tracee_source: str
    est_augmente: bool


def get_train_transform(patch_size: int = 256) -> A.Compose:
    """Pipeline d'augmentation. Chaque transformation geometrique (flip,
    rotation) s'applique identiquement a l'image ET aux 2 masques grace a
    `additional_targets` - c'est ce qui garantit l'alignement.
    """
    return A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.5),
            A.RandomRotate90(p=0.5),
            A.Affine(
                rotate=(-10, 10),
                scale=(0.9, 1.1),
                border_mode=cv2.BORDER_REFLECT_101,
                p=0.5,
            ),
            A.RandomBrightnessContrast(brightness_limit=0.15, contrast_limit=0.15, p=0.5),
            A.GaussNoise(std_range=(0.02, 0.08), p=0.3),
            A.OneOf([
                A.GaussianBlur(blur_limit=(3, 5), p=1.0),
                A.Sharpen(alpha=(0.1, 0.3), p=1.0),
            ], p=0.3),
            A.CoarseDropout(
                num_holes_range=(1, 3),
                hole_height_range=(0.03, 0.08),
                hole_width_range=(0.03, 0.08),
                fill=255,
                p=0.2,
            ),
        ],
        additional_targets={'mask_interieur': 'mask', 'mask_frontiere': 'mask'},
    )


def _random_crop_centered(
    image: np.ndarray, mask_int: np.ndarray, mask_front: np.ndarray,
    center_x: int, center_y: int, patch_size: int, jitter_px: int = 60,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extrait un patch de taille fixe autour d'un centre donne, avec un peu de
    jitter aleatoire pour ne pas toujours cadrer la piece pile au milieu."""
    h, w = image.shape[:2]
    cx = center_x + random.randint(-jitter_px, jitter_px)
    cy = center_y + random.randint(-jitter_px, jitter_px)

    x0 = max(0, min(w - patch_size, cx - patch_size // 2))
    y0 = max(0, min(h - patch_size, cy - patch_size // 2))
    x1, y1 = x0 + patch_size, y0 + patch_size

    return image[y0:y1, x0:x1], mask_int[y0:y1, x0:x1], mask_front[y0:y1, x0:x1]


def extract_raw_patches(masks: TraceeMasks, patch_size: int = 256, n_random_patches: int = 10) -> list[Patch]:
    """Extrait les patchs BRUTS (sans augmentation) d'un tracé :
    - un patch centre sur chaque piece (garantit une couverture complete)
    - n_random_patches patchs a des positions aleatoires (diversite de fond)

    Si l'image est plus petite que patch_size dans une dimension, elle est
    d'abord agrandie (letterbox) pour eviter tout patch de taille incorrecte.
    """
    h, w = masks.image.shape[:2]
    image, mi, mf = masks.image, masks.mask_interieur, masks.mask_frontiere

    if h < patch_size or w < patch_size:
        pad_h, pad_w = max(0, patch_size - h), max(0, patch_size - w)
        image = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT_101)
        mi = cv2.copyMakeBorder(mi, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=0)
        mf = cv2.copyMakeBorder(mf, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=0)
        h, w = image.shape[:2]

    labels, n_instances = masks_to_instances(mi, mf, min_area_px=150)

    patches = []
    for i in range(1, n_instances + 1):
        ys, xs = np.where(labels == i)
        cx, cy = int(xs.mean()), int(ys.mean())
        p_img, p_mi, p_mf = _random_crop_centered(image, mi, mf, cx, cy, patch_size)
        patches.append(Patch(p_img, p_mi, p_mf, masks.tracee_name, est_augmente=False))

    for _ in range(n_random_patches):
        cx = random.randint(patch_size // 2, w - patch_size // 2)
        cy = random.randint(patch_size // 2, h - patch_size // 2)
        p_img, p_mi, p_mf = _random_crop_centered(image, mi, mf, cx, cy, patch_size, jitter_px=0)
        patches.append(Patch(p_img, p_mi, p_mf, masks.tracee_name, est_augmente=False))

    return patches


def augment_patch(patch: Patch, transform: A.Compose) -> Patch:
    """Applique une augmentation aleatoire a un patch (image + 2 masques,
    de facon synchronisee)."""
    result = transform(image=patch.image, mask_interieur=patch.mask_interieur, mask_frontiere=patch.mask_frontiere)
    return Patch(
        image=result['image'],
        mask_interieur=result['mask_interieur'],
        mask_frontiere=result['mask_frontiere'],
        tracee_source=patch.tracee_source,
        est_augmente=True,
    )


def build_dataset(
    all_masks: dict[str, TraceeMasks],
    patch_size: int = 256,
    n_random_patches_per_tracee: int = 10,
    n_augmentations_per_patch: int = 3,
) -> list[Patch]:
    """Construit le jeu de donnees complet : patchs bruts + versions augmentees.
    Retourne la liste de tous les patchs (bruts + augmentes), avec leur tracé
    source conserve (necessaire pour la validation leave-one-tracé-out en Phase 4).
    """
    transform = get_train_transform(patch_size)
    dataset = []

    for name, masks in all_masks.items():
        raw_patches = extract_raw_patches(masks, patch_size, n_random_patches_per_tracee)
        dataset.extend(raw_patches)
        for patch in raw_patches:
            for _ in range(n_augmentations_per_patch):
                dataset.append(augment_patch(patch, transform))

    return dataset


def save_dataset(dataset: list[Patch], out_dir: str) -> None:
    """Sauvegarde tous les patchs sur disque, organises par tracé source
    (necessaire pour pouvoir plus tard exclure facilement un tracé entier lors
    de la validation leave-one-tracé-out)."""
    out_path = Path(out_dir)
    counters: dict[str, int] = {}

    for patch in dataset:
        tracee_dir = out_path / patch.tracee_source
        tracee_dir.mkdir(parents=True, exist_ok=True)
        idx = counters.get(patch.tracee_source, 0)
        counters[patch.tracee_source] = idx + 1

        suffix = "aug" if patch.est_augmente else "brut"
        base = tracee_dir / f"patch_{idx:04d}_{suffix}"
        cv2.imwrite(str(base) + "_image.png", patch.image)
        cv2.imwrite(str(base) + "_interieur.png", patch.mask_interieur)
        cv2.imwrite(str(base) + "_frontiere.png", patch.mask_frontiere)
