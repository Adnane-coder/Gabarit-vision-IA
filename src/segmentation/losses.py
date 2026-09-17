"""
losses.py

Fonction de perte pour l'entrainement du U-Net : combinaison Dice + BCE,
standard pour la segmentation binaire/multi-canal avec desequilibre
pieces/fond (la plupart des pixels d'un patch sont "fond", pas "piece").

- BCE (Binary Cross-Entropy) : penalise chaque pixel individuellement.
- Dice : mesure le chevauchement global masque predit / masque reel, moins
  sensible au desequilibre de classes que la BCE seule.
La combinaison des deux est une pratique standard qui donne generalement de
meilleurs resultats que l'une ou l'autre isolement.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class DiceBCELoss(nn.Module):
    def __init__(self, dice_weight: float = 0.5, bce_weight: float = 0.5, smooth: float = 1.0):
        super().__init__()
        self.dice_weight = dice_weight
        self.bce_weight = bce_weight
        self.smooth = smooth

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Args:
            logits: sortie brute du modele (avant sigmoid), shape (B, C, H, W).
            targets: masques reels, valeurs 0/1, meme shape.
        """
        # IMPORTANT : on force le calcul en float32, quel que soit le contexte
        # d'appel (meme si appele sous torch.amp.autocast en fp16). En fp16,
        # sommer des dizaines de milliers de pixels (ex. 256*256) peut depasser
        # la valeur max representable (~65504) et produire un overflow -> inf
        # -> nan sur toute la perte. C'est exactement ce qui causait les
        # "train_loss=nan" observes a l'entrainement.
        logits = logits.float()
        targets = targets.float()

        bce = F.binary_cross_entropy_with_logits(logits, targets)

        probs = torch.sigmoid(logits)
        probs_flat = probs.reshape(probs.shape[0], probs.shape[1], -1)
        targets_flat = targets.reshape(targets.shape[0], targets.shape[1], -1)

        intersection = (probs_flat * targets_flat).sum(dim=2)
        union = probs_flat.sum(dim=2) + targets_flat.sum(dim=2)
        dice_score = (2.0 * intersection + self.smooth) / (union + self.smooth)
        dice_loss = 1.0 - dice_score.mean()

        return self.bce_weight * bce + self.dice_weight * dice_loss


if __name__ == "__main__":
    # test rapide : la perte doit etre proche de 0 quand prediction == cible,
    # et significativement plus grande sinon
    loss_fn = DiceBCELoss()

    targets = torch.randint(0, 2, (2, 2, 64, 64)).float()
    logits_parfaits = (targets * 20) - 10  # logits qui donnent sigmoid ~0 ou ~1 correctement
    logits_aleatoires = torch.randn(2, 2, 64, 64)

    loss_parfaite = loss_fn(logits_parfaits, targets)
    loss_aleatoire = loss_fn(logits_aleatoires, targets)

    print(f"Perte avec prediction quasi-parfaite : {loss_parfaite.item():.4f} (doit etre proche de 0)")
    print(f"Perte avec prediction aleatoire       : {loss_aleatoire.item():.4f} (doit etre nettement plus grande)")
    assert loss_parfaite.item() < 0.05, "La perte devrait etre quasi nulle pour une prediction parfaite !"
    assert loss_aleatoire.item() > loss_parfaite.item(), "La perte aleatoire devrait etre pire que la parfaite !"
    print("Test de coherence de la fonction de perte reussi.")
