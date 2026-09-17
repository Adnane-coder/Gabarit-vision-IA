"""Real conformity control pipeline.

Ported directly from notebooks/10_pipeline_conformite.ipynb (validated
against notebooks/09_comparaison_canny_unet.ipynb for the tiling strategy,
and notebooks/02_reference_table.ipynb / 03_conformity_check.ipynb for the
reference table and matching logic). Kept functionally identical to the
notebook version — no visualization/matplotlib here since this runs
server-side, but the measurement, matching and verdict logic is unchanged.

`build_model()` reconstructs the exact architecture confirmed by strict
`load_state_dict` against a real checkpoint (segmentation-models-pytorch
U-Net, ResNet18 encoder, 3 input channels, 2 output classes, ~14.3M params).
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover
    raise ImportError("PyMuPDF manquant. Installer avec : pip install pymupdf") from exc

from app.core.logging import get_logger

logger = get_logger(__name__)

# Same normalization used at training time (ImageNet stats).
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)


def build_model(pretrained: bool = False) -> torch.nn.Module:
    return smp.Unet(
        encoder_name="resnet18",
        encoder_weights="imagenet" if pretrained else None,
        in_channels=3,
        classes=2,
    )


def find_pdf_for_tracee(tracee: str, pdf_dir: str) -> Optional[Path]:
    pdf_dir_path = Path(pdf_dir)
    if not pdf_dir_path.exists():
        return None
    for candidate in sorted(pdf_dir_path.glob("*.pdf")):
        if tracee.lower() in candidate.stem.lower():
            return candidate
    return None


def get_scale_and_target_size(tracee: str, pdf_path: Path, annotations_dir: str, results_dir: str):
    """Reuses the Phase 1 calibrated scale for the 4 known tracés. For an
    unknown tracé, computes scale directly from the 1:1 vector PDF geometry."""
    annot_path = Path(annotations_dir) / f"{tracee}_annotations.json"
    bench_path = Path(results_dir) / "01_baseline_benchmark.json"

    if annot_path.exists() and bench_path.exists():
        with open(annot_path) as f:
            annot = json.load(f)
        with open(bench_path) as f:
            bench = json.load(f)[tracee]
        w_px, h_px = annot["image_original_size_px"]
        w_cm, h_cm = bench["taille_physique_reelle_cm"]
        scale_cm_par_px = ((w_cm / w_px) + (h_cm / h_px)) / 2
        return w_px, h_px, scale_cm_par_px

    doc = fitz.open(str(pdf_path))
    page_w_pt, page_h_pt = doc[0].rect.width, doc[0].rect.height
    doc.close()
    target_long_side = 4000
    if page_w_pt >= page_h_pt:
        w_px = target_long_side
        h_px = int(target_long_side * page_h_pt / page_w_pt)
    else:
        h_px = target_long_side
        w_px = int(target_long_side * page_w_pt / page_h_pt)
    scale_cm_par_px = (page_w_pt * 2.54 / 72) / w_px
    return w_px, h_px, scale_cm_par_px


def render_page_matching_original(pdf_path: Path, target_w_px: int, target_h_px: int, page_number: int = 0):
    doc = fitz.open(str(pdf_path))
    page = doc[page_number]
    page_w_pt, page_h_pt = page.rect.width, page.rect.height
    zoom_x = target_w_px / page_w_pt
    zoom_y = target_h_px / page_h_pt
    mat = fitz.Matrix(zoom_x, zoom_y)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    doc.close()
    if img.shape[1] != target_w_px or img.shape[0] != target_h_px:
        img = cv2.resize(img, (target_w_px, target_h_px), interpolation=cv2.INTER_AREA)
    return img


def unet_predict_full_image(model, image_rgb, device: str, patch_size: int = 256, stride: int = 128):
    """Overlapping tiles (50% overlap) + probability averaging — best config
    found in notebook 09 (avoids tile-boundary artifacts)."""
    h, w, _ = image_rgb.shape
    prob_accum = np.zeros((h, w), dtype=np.float32)
    count_accum = np.zeros((h, w), dtype=np.float32)

    ys = list(range(0, max(h - patch_size, 0) + 1, stride)) or [0]
    xs = list(range(0, max(w - patch_size, 0) + 1, stride)) or [0]
    if ys[-1] != max(h - patch_size, 0):
        ys.append(max(h - patch_size, 0))
    if xs[-1] != max(w - patch_size, 0):
        xs.append(max(w - patch_size, 0))

    for y in ys:
        for x in xs:
            patch = image_rgb[y:y + patch_size, x:x + patch_size]
            ph, pw = patch.shape[:2]
            if ph < patch_size or pw < patch_size:
                padded = np.zeros((patch_size, patch_size, 3), dtype=np.uint8)
                padded[:ph, :pw] = patch
                patch = padded
            patch_norm = (patch.astype(np.float32) / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
            tensor = torch.from_numpy(patch_norm).permute(2, 0, 1).float().unsqueeze(0).to(device)
            with torch.no_grad():
                logits = model(tensor)
                probs = torch.sigmoid(logits)[0, 0].cpu().numpy()
            prob_accum[y:y + ph, x:x + pw] += probs[:ph, :pw]
            count_accum[y:y + ph, x:x + pw] += 1.0

    count_accum[count_accum == 0] = 1.0
    prob_moyenne = prob_accum / count_accum
    return (prob_moyenne > 0.5).astype(np.uint8) * 255


def detect_pieces(mask_full, scale_cm_par_px: float, min_area_cm2: float):
    min_area_px = min_area_cm2 / (scale_cm_par_px ** 2)
    contours, _ = cv2.findContours(mask_full, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pieces = []
    for c in contours:
        aire = cv2.contourArea(c)
        if aire < min_area_px:
            continue
        x, y, w, h = cv2.boundingRect(c)
        pieces.append({
            "bbox_px": (x, y, w, h),
            "largeur_cm": round(w * scale_cm_par_px, 2),
            "hauteur_cm": round(h * scale_cm_par_px, 2),
        })
    return pieces


def apparier_et_verifier_conformite(
    pieces_detectees: List[Dict[str, Any]],
    pieces_reference_dict: Dict[str, Dict[str, Any]],
    tolerance_cm: float,
) -> List[Dict[str, Any]]:
    """Greedy one-to-one matching (same method validated in notebook 09).
    Each reference piece ends up matched (CONFORME/NON CONFORME) or MANQUANTE;
    each unmatched detection is INATTENDUE."""
    references = []
    for nom, p in pieces_reference_dict.items():
        for _ in range(p.get("n_instances", 1)):
            references.append({"nom": nom, "largeur_cm": p["largeur_cm"], "hauteur_cm": p["hauteur_cm"]})

    paires = []
    for i, det in enumerate(pieces_detectees):
        for j, ref in enumerate(references):
            cout = max(abs(det["largeur_cm"] - ref["largeur_cm"]), abs(det["hauteur_cm"] - ref["hauteur_cm"]))
            paires.append((cout, i, j))
    paires.sort(key=lambda x: x[0])

    det_utilisees, ref_utilisees = set(), set()
    rapport = []
    for cout, i, j in paires:
        if i in det_utilisees or j in ref_utilisees:
            continue
        det_utilisees.add(i)
        ref_utilisees.add(j)
        det, ref = pieces_detectees[i], references[j]
        rapport.append({
            "piece_reference": ref["nom"],
            "largeur_attendue_cm": ref["largeur_cm"], "hauteur_attendue_cm": ref["hauteur_cm"],
            "largeur_mesuree_cm": det["largeur_cm"], "hauteur_mesuree_cm": det["hauteur_cm"],
            "erreur_cm": round(cout, 2),
            "verdict": "CONFORME" if cout <= tolerance_cm else "NON CONFORME",
            "bbox_px": det["bbox_px"],
        })

    for j, ref in enumerate(references):
        if j not in ref_utilisees:
            rapport.append({
                "piece_reference": ref["nom"],
                "largeur_attendue_cm": ref["largeur_cm"], "hauteur_attendue_cm": ref["hauteur_cm"],
                "largeur_mesuree_cm": None, "hauteur_mesuree_cm": None,
                "erreur_cm": None, "verdict": "MANQUANTE", "bbox_px": None,
            })

    for i, det in enumerate(pieces_detectees):
        if i not in det_utilisees:
            rapport.append({
                "piece_reference": None,
                "largeur_attendue_cm": None, "hauteur_attendue_cm": None,
                "largeur_mesuree_cm": det["largeur_cm"], "hauteur_mesuree_cm": det["hauteur_cm"],
                "erreur_cm": None, "verdict": "INATTENDUE", "bbox_px": det["bbox_px"],
            })

    return rapport


def verifier_conformite_tracee(
    tracee: str,
    *,
    checkpoints_dir: str,
    reference_table_path: str,
    trace_pdf_dir: str,
    annotations_dir: str,
    results_dir: str,
    tolerance_cm: float,
    min_area_cm2: float,
    device: str,
) -> Dict[str, Any]:
    """Full pipeline: PDF -> segmentation -> measurement -> verdict.
    Uses the leave-one-trace-out checkpoint for the known tracé (consistent
    with training: no data leakage)."""
    t_debut = time.time()

    pdf_path = find_pdf_for_tracee(tracee, trace_pdf_dir)
    if pdf_path is None:
        raise FileNotFoundError(f"PDF introuvable pour {tracee} dans {trace_pdf_dir}")

    checkpoint_path = Path(checkpoints_dir) / f"unet_fold_{tracee}_best.pt"
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint introuvable : {checkpoint_path}")

    with open(reference_table_path) as f:
        table_reference = json.load(f)
    if tracee not in table_reference:
        raise KeyError(f"{tracee} absent de la table de reference ({reference_table_path})")
    infos_ref = table_reference[tracee]
    code_modele = infos_ref.get("code_modele", "?")

    w_px, h_px, scale_cm_par_px = get_scale_and_target_size(tracee, pdf_path, annotations_dir, results_dir)
    image_rgb = render_page_matching_original(pdf_path, w_px, h_px)

    model = build_model(pretrained=False).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    mask_full = unet_predict_full_image(model, image_rgb, device)
    pieces_detectees = detect_pieces(mask_full, scale_cm_par_px, min_area_cm2)

    del model
    if device == "cuda":
        torch.cuda.empty_cache()

    rapport = apparier_et_verifier_conformite(pieces_detectees, infos_ref["pieces"], tolerance_cm)
    temps_total = time.time() - t_debut

    n_conformes = sum(1 for r in rapport if r["verdict"] == "CONFORME")
    n_non_conformes = sum(1 for r in rapport if r["verdict"] == "NON CONFORME")
    n_manquantes = sum(1 for r in rapport if r["verdict"] == "MANQUANTE")
    n_inattendues = sum(1 for r in rapport if r["verdict"] == "INATTENDUE")
    n_total_reference = n_conformes + n_non_conformes + n_manquantes

    logger.info(
        "Conformity check %s: %d/%d conforme, %.1f%% taux, %.2fs",
        tracee, n_conformes, n_total_reference,
        (n_conformes / n_total_reference * 100) if n_total_reference else 0.0,
        temps_total,
    )

    return {
        "tracee": tracee,
        "code_modele": code_modele,
        "checkpoint_utilise": str(checkpoint_path),
        "n_pieces_reference": n_total_reference,
        "n_conformes": n_conformes,
        "n_non_conformes": n_non_conformes,
        "n_manquantes": n_manquantes,
        "n_inattendues": n_inattendues,
        "taux_conformite_global": round(n_conformes / n_total_reference, 4) if n_total_reference else None,
        "temps_total_s": round(temps_total, 2),
        "rapport_detaille": rapport,
    }
