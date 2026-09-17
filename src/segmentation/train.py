"""
train.py

Script d'entrainement principal du U-Net (Phase 3). A executer directement
avec Python (pas dans un notebook - un entrainement de plusieurs epoques est
plus stable et plus facile a suivre en script).

Usage :
    python train.py

Strategie de validation : leave-one-tracé-out. Comme on n'a que 4 tracés
sources, un simple split train/test classique n'a pas beaucoup de sens
statistique. A la place, on entraine 4 modeles successifs :
    - modele 1 : entraine sur Tracee2+3+4, valide sur Tracee1 (jamais vu)
    - modele 2 : entraine sur Tracee1+3+4, valide sur Tracee2 (jamais vu)
    - modele 3 : entraine sur Tracee1+2+4, valide sur Tracee3 (jamais vu)
    - modele 4 : entraine sur Tracee1+2+3, valide sur Tracee4 (jamais vu)
Ca donne une estimation (certes limitee avec 4 echantillons) de la capacite
du modele a generaliser a un tracé qu'il n'a jamais vu a l'entrainement -
exactement le scenario du futur usage reel (un nouveau tracé de test).

Le modele final utilise en production sera ensuite ré-entraine sur les 4
tracés (plus de donnees = mieux), une fois qu'on aura confiance dans
l'architecture grace a cette validation croisee.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from torch.amp import autocast, GradScaler

from dataset import PatchDataset
from model import build_model
from losses import DiceBCELoss


# ---------------------------------------------------------------------------
# CONFIGURATION - a ajuster si besoin selon la memoire GPU disponible
# ---------------------------------------------------------------------------
PATCHES_DIR = "../data/processed/patches"
CHECKPOINTS_DIR = "../models/saved"
RESULTS_DIR = "../data/results"

BATCH_SIZE = 8          # adapte a 4Go de VRAM (GTX 1650) ; reduire a 4 si "out of memory"
NUM_EPOCHS = 2
LEARNING_RATE = 1e-4
NUM_WORKERS = 2          # chargement des donnees en parallele ; mettre 0 si probleme sous Windows
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

TRACEES = ["Tracee1", "Tracee2", "Tracee3", "Tracee4"]
# ---------------------------------------------------------------------------


def train_one_fold(fold_tracee_valid: str, epochs: int = NUM_EPOCHS) -> dict:
    """Entraine un modele en excluant fold_tracee_valid du jeu d'entrainement,
    et l'utilise comme validation. Retourne l'historique des pertes.
    """
    print(f"\n{'='*70}")
    print(f"FOLD - validation sur {fold_tracee_valid} (entrainement sur les 3 autres)")
    print(f"{'='*70}")

    train_ds = PatchDataset(PATCHES_DIR, exclude_tracees=[fold_tracee_valid])
    valid_ds = PatchDataset(PATCHES_DIR, include_tracees=[fold_tracee_valid])
    print(f"Entrainement: {len(train_ds)} patchs | Validation: {len(valid_ds)} patchs")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS)

    model = build_model(pretrained=True).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = DiceBCELoss()
    scaler = GradScaler(enabled=(DEVICE == "cuda"))  # precision mixte (fp16) pour economiser la VRAM

    history = {"train_loss": [], "valid_loss": []}
    best_valid_loss = float("inf")

    for epoch in range(1, epochs + 1):
        t0 = time.time()

        # --- entrainement ---
        model.train()
        train_loss_total = 0.0
        for images, masks in train_loader:
            images, masks = images.to(DEVICE), masks.to(DEVICE)
            optimizer.zero_grad()

            with autocast(device_type=DEVICE, enabled=(DEVICE == "cuda")):
                logits = model(images)
                loss = loss_fn(logits, masks)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            train_loss_total += loss.item() * images.size(0)

        train_loss = train_loss_total / len(train_ds)

        # --- validation ---
        model.eval()
        valid_loss_total = 0.0
        with torch.no_grad():
            for images, masks in valid_loader:
                images, masks = images.to(DEVICE), masks.to(DEVICE)
                with autocast(device_type=DEVICE, enabled=(DEVICE == "cuda")):
                    logits = model(images)
                    loss = loss_fn(logits, masks)
                valid_loss_total += loss.item() * images.size(0)
        valid_loss = valid_loss_total / len(valid_ds)

        history["train_loss"].append(train_loss)
        history["valid_loss"].append(valid_loss)

        elapsed = time.time() - t0
        print(f"Epoch {epoch:3d}/{epochs} | train_loss={train_loss:.4f} | "
              f"valid_loss={valid_loss:.4f} | {elapsed:.1f}s")

        if valid_loss < best_valid_loss:
            best_valid_loss = valid_loss
            Path(CHECKPOINTS_DIR).mkdir(parents=True, exist_ok=True)
            checkpoint_path = Path(CHECKPOINTS_DIR) / f"unet_fold_{fold_tracee_valid}_best.pt"
            torch.save(model.state_dict(), checkpoint_path)

    return {
        "fold_valid_tracee": fold_tracee_valid,
        "best_valid_loss": best_valid_loss,
        "history": history,
    }


def main():
    print(f"Device utilise pour l'entrainement : {DEVICE}")
    if DEVICE == "cpu":
        print("ATTENTION : aucun GPU detecte, l'entrainement sur CPU sera tres lent. "
              "Verifier l'installation de PyTorch avec support CUDA.")

    all_results = []
    for tracee in TRACEES:
        result = train_one_fold(fold_tracee_valid=tracee)
        all_results.append(result)

    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    with open(Path(RESULTS_DIR) / "training_leave_one_out_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'='*70}")
    print("RESUME DE LA VALIDATION LEAVE-ONE-TRACE-OUT")
    print(f"{'='*70}")
    for r in all_results:
        print(f"  Validation sur {r['fold_valid_tracee']:10s} -> meilleure perte de validation : {r['best_valid_loss']:.4f}")


if __name__ == "__main__":
    main()
