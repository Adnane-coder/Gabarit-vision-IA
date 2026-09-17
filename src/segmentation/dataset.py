"""
dataset.py

Dataset PyTorch qui charge les patchs generes en Phase 2
(data/processed/patches/TraceeN/...) pour l'entrainement du U-Net.

Permet nativement l'exclusion d'un tracé (parametre exclude_tracees), ce qui
rend la validation leave-one-tracé-out directe : on entraine avec 3 tracés
exclus du dossier de validation, et vice-versa.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

# Moyenne/ecart-type ImageNet : l'encodeur pre-entraine (resnet18) a ete
# entraine avec des images normalisees exactement de cette facon. Sans cette
# normalisation, les activations internes du reseau peuvent devenir tres
# grandes des les premieres couches, et deborder (overflow -> inf -> nan) en
# precision mixte (fp16). C'etait la vraie cause des "train_loss=nan" observes
# a l'entrainement (le fix precedent sur la fonction de perte etait necessaire
# mais pas suffisant : le probleme commencait avant, dans le passage avant du
# modele lui-meme).
IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

# Moyenne/ecart-type ImageNet : l'encodeur pretrained (ResNet18) a ete entraine
# avec des images normalisees ainsi. Sans cette normalisation, les images en
# [0,1] brutes produisent des activations mal calibrees dans les couches
# pretrained, ce qui peut deborder la precision fp16 (entrainement en
# precision mixte) et provoquer des pertes NaN - c'est exactement ce qui
# causait les "train_loss=nan" observes a l'entrainement.
IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


class PatchDataset(Dataset):
    """Charge les triplets (image, masque_interieur, masque_frontiere) depuis
    data/processed/patches/TraceeN/patch_XXXX_[brut|aug]_*.png
    """

    def __init__(
        self,
        patches_dir: str,
        include_tracees: list[str] | None = None,
        exclude_tracees: list[str] | None = None,
    ):
        """
        Args:
            patches_dir: dossier racine des patchs (data/processed/patches).
            include_tracees: si fourni, ne charge QUE ces tracés (ex. ['Tracee2']
                pour la validation).
            exclude_tracees: si fourni, charge tous les tracés SAUF ceux-ci
                (ex. ['Tracee2'] pour l'entrainement, en excluant le tracé de
                validation).
        """
        self.root = Path(patches_dir)
        self.samples: list[Path] = []

        for tracee_dir in sorted(self.root.iterdir()):
            if not tracee_dir.is_dir():
                continue
            if include_tracees is not None and tracee_dir.name not in include_tracees:
                continue
            if exclude_tracees is not None and tracee_dir.name in exclude_tracees:
                continue

            image_files = sorted(tracee_dir.glob("*_image.png"))
            self.samples.extend(image_files)

        if not self.samples:
            raise ValueError(
                f"Aucun patch trouve dans {patches_dir} "
                f"(include={include_tracees}, exclude={exclude_tracees})"
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        image_path = self.samples[idx]
        base = str(image_path).replace("_image.png", "")

        image = cv2.imread(str(image_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask_interieur = cv2.imread(base + "_interieur.png", cv2.IMREAD_GRAYSCALE)
        mask_frontiere = cv2.imread(base + "_frontiere.png", cv2.IMREAD_GRAYSCALE)

        # normalisation image : [0,255] -> [0,1] -> normalisation ImageNet
        # (obligatoire pour un encodeur pre-entraine sur ImageNet)
        image_t = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        image_t = (image_t - IMAGENET_MEAN) / IMAGENET_STD

        # masques empiles en 2 canaux, valeurs 0/1
        mask_t = torch.stack([
            torch.from_numpy(mask_interieur).float() / 255.0,
            torch.from_numpy(mask_frontiere).float() / 255.0,
        ])

        return image_t, mask_t


if __name__ == "__main__":
    # test rapide : charger le dataset complet, verifier une shape
    ds = PatchDataset("../data/processed/patches")
    print(f"{len(ds)} patchs charges au total")
    img, mask = ds[0]
    print(f"Image: {tuple(img.shape)}, valeurs [{img.min():.2f}, {img.max():.2f}]")
    print(f"Masque: {tuple(mask.shape)}, valeurs [{mask.min():.2f}, {mask.max():.2f}]")

    ds_sans_tracee2 = PatchDataset("../data/processed/patches", exclude_tracees=["Tracee2"])
    ds_tracee2_seul = PatchDataset("../data/processed/patches", include_tracees=["Tracee2"])
    print(f"Sans Tracee2: {len(ds_sans_tracee2)} patchs | Tracee2 seul: {len(ds_tracee2_seul)} patchs")
    assert len(ds_sans_tracee2) + len(ds_tracee2_seul) == len(ds), "La partition ne couvre pas tout le dataset !"
    print("Partition leave-one-tracé-out coherente.")
