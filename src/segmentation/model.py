"""
model.py

Definition du modele de segmentation pour la Phase 3 du projet.

Architecture retenue : U-Net avec encodeur ResNet18 pre-entraine (ImageNet).
- U-Net : standard pour la segmentation avec peu de donnees (skip connections
  qui preservent le detail spatial fin, important pour des contours precis).
- Encodeur pre-entraine : avec seulement 660 patchs d'entrainement (issus de
  4 images sources), un encodeur entraine depuis zero apprendrait mal les
  filtres de bas niveau (bords, textures). Le pre-entrainement ImageNet lui
  donne deja ces filtres de base ; l'entrainement n'a plus qu'a les adapter
  a notre domaine (patrons de couture).
- ResNet18 (pas ResNet34/50) : le plus leger de la famille ResNet, choisi
  pour tenir confortablement dans les 4 Go de VRAM de la GTX 1650 cible.
- 2 canaux de sortie : intérieur de piece + frontiere (cf. Phase 1,
  dataset_prep.py) - permet de separer les pieces qui se touchent.

Utilise la librairie 'segmentation-models-pytorch' (implementation standard
et maintenue), plutot que reimplementer un U-Net a la main.
"""

from __future__ import annotations

import segmentation_models_pytorch as smp
import torch
import torch.nn as nn


def build_model(encoder_name: str = "resnet18", pretrained: bool = True) -> nn.Module:
    """Construit le modele U-Net.

    Args:
        encoder_name: backbone de l'encodeur. 'resnet18' par defaut (leger,
            adapte a une GPU 4 Go). 'resnet34' est une option si plus de VRAM
            est disponible.
        pretrained: si True, charge les poids ImageNet (fortement recommande
            vu la taille limitee du jeu de donnees).
    """
    model = smp.Unet(
        encoder_name=encoder_name,
        encoder_weights="imagenet" if pretrained else None,
        in_channels=3,
        classes=2,  # canal 0 = interieur, canal 1 = frontiere
        activation=None,  # on applique sigmoid manuellement (loss BCEWithLogits + Dice sur logits)
    )
    return model


def count_parameters(model: nn.Module) -> tuple[int, int]:
    """Retourne (nombre total de parametres, nombre de parametres entrainables)."""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


if __name__ == "__main__":
    # test rapide de coherence des formes (executable sur CPU, sans GPU)
    model = build_model()
    total, trainable = count_parameters(model)
    print(f"Modele cree : {total:,} parametres ({trainable:,} entrainables)")

    dummy_input = torch.randn(2, 3, 256, 256)
    output = model(dummy_input)
    print(f"Entree: {tuple(dummy_input.shape)} -> Sortie: {tuple(output.shape)}")
    assert output.shape == (2, 2, 256, 256), "Forme de sortie inattendue !"
    print("Test de coherence des formes reussi.")
