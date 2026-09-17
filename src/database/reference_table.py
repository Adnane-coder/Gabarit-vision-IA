"""
reference_table.py

Construit la table de reference des dimensions nominales, a partir des tracés
valides annotes a la main. C'est LA source de verite du projet : en l'absence
de fiche technique fournie par SARTEX, les dimensions mesurees sur ces tracés
de reference font foi (cf. decision validee avec les encadrants).

IMPORTANT - portee de la reference :
Les 4 tracés (Tracee1 a Tracee4) correspondent chacun a un MODELE DE VETEMENT
DIFFERENT (codes internes distincts : 157380CD-PDF, 02110170811CD-A,
01461170745CD-A1, 01110170919CD-A). Ce ne sont PAS 4 exemplaires du meme
vetement. La table de reference est donc structuree par modele : chaque
modele a ses propres dimensions nominales par piece, et un nouveau tracé a
tester doit etre compare a la reference du MEME modele (identifie par son
code interne), pas a une reference globale toutes pieces confondues.

Quand un nom de piece apparait plusieurs fois dans un meme modele (ex. pieces
symetriques gauche/droite), les mesures sont moyennees et un controle de
coherence (ecart-type) est calcule pour detecter d'eventuelles erreurs
d'annotation.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field, asdict
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from measurement.dimensions import measure_piece, PieceMeasurements
from acquisition.pdf_loader import get_pdf_page_size_cm, rasterize_pdf


@dataclass
class PieceReference:
    """Reference nominale d'une piece pour un modele donne."""
    nom: str
    n_instances: int
    largeur_cm: float
    hauteur_cm: float
    perimetre_cm: float
    aire_cm2: float
    diagonale_cm: float
    # ecart-type observe entre instances (0 si une seule instance) - sert a detecter
    # les incoherences d'annotation ou les vraies asymetries de la piece
    ecart_type_largeur_cm: float = 0.0
    ecart_type_hauteur_cm: float = 0.0


@dataclass
class ModelReference:
    """Table de reference complete pour un modele de vetement (un tracé)."""
    tracee: str
    code_modele: str
    pieces: dict = field(default_factory=dict)  # nom_piece -> PieceReference


def get_model_code(pdf_path: str) -> str:
    """Extrait le code interne du modele depuis le calque texte du PDF
    (le code le plus frequent contenant 'CD', hors variantes tronquees).
    """
    import fitz
    from collections import Counter
    doc = fitz.open(pdf_path)
    words = doc[0].get_text('words')
    codes = Counter(w[4] for w in words if 'CD' in w[4].upper() and 'PLCT' not in w[4].upper())
    if not codes:
        return "INCONNU"
    return codes.most_common(1)[0][0]


def build_model_reference(tracee_name: str, pdf_path: str, annotations_path: str) -> ModelReference:
    """Construit la reference pour UN modele (un tracé), a partir de son fichier
    d'annotations JSON exporte par l'outil d'annotation.
    """
    with open(annotations_path, encoding='utf-8') as f:
        data = json.load(f)

    w_px, h_px = data['image_original_size_px']
    w_cm, h_cm = get_pdf_page_size_cm(pdf_path)
    scale_cm_per_px = ((w_cm / w_px) + (h_cm / h_px)) / 2

    code_modele = get_model_code(pdf_path)

    # regrouper les mesures par nom de piece
    measurements_by_name: dict[str, list[PieceMeasurements]] = {}
    for piece in data['pieces']:
        nom = piece['nom'].strip().upper()  # normalisation : casse uniforme
        m = measure_piece(piece['points_original_px'], scale_cm_per_px)
        measurements_by_name.setdefault(nom, []).append(m)

    pieces_ref = {}
    for nom, mlist in measurements_by_name.items():
        largeurs = [m.largeur_cm for m in mlist]
        hauteurs = [m.hauteur_cm for m in mlist]
        pieces_ref[nom] = PieceReference(
            nom=nom,
            n_instances=len(mlist),
            largeur_cm=round(statistics.mean(largeurs), 2),
            hauteur_cm=round(statistics.mean(hauteurs), 2),
            perimetre_cm=round(statistics.mean(m.perimetre_cm for m in mlist), 2),
            aire_cm2=round(statistics.mean(m.aire_cm2 for m in mlist), 2),
            diagonale_cm=round(statistics.mean(m.diagonale_cm for m in mlist), 2),
            ecart_type_largeur_cm=round(statistics.stdev(largeurs), 2) if len(largeurs) > 1 else 0.0,
            ecart_type_hauteur_cm=round(statistics.stdev(hauteurs), 2) if len(hauteurs) > 1 else 0.0,
        )

    return ModelReference(tracee=tracee_name, code_modele=code_modele, pieces=pieces_ref)


def build_full_reference_table(tracees: dict[str, tuple[str, str]]) -> dict[str, ModelReference]:
    """Construit la table complete pour plusieurs modeles.
    tracees: { nom_tracee: (pdf_path, annotations_path) }
    """
    table = {}
    for tracee_name, (pdf_path, ann_path) in tracees.items():
        table[tracee_name] = build_model_reference(tracee_name, pdf_path, ann_path)
    return table


def qa_check(model_ref: ModelReference, tolerance_pct: float = 5.0) -> list[str]:
    """Controle qualite : signale les pieces dont les instances multiples varient
    de plus de tolerance_pct % l'une par rapport a l'autre (indice possible d'une
    erreur d'annotation plutot qu'une vraie asymetrie de la piece).
    """
    warnings = []
    for nom, ref in model_ref.pieces.items():
        if ref.n_instances < 2:
            continue
        if ref.largeur_cm > 0 and (ref.ecart_type_largeur_cm / ref.largeur_cm * 100) > tolerance_pct:
            warnings.append(
                f"[{model_ref.tracee}] '{nom}' : largeur incoherente entre ses "
                f"{ref.n_instances} instances (moyenne {ref.largeur_cm}cm, "
                f"ecart-type {ref.ecart_type_largeur_cm}cm) - a verifier"
            )
        if ref.hauteur_cm > 0 and (ref.ecart_type_hauteur_cm / ref.hauteur_cm * 100) > tolerance_pct:
            warnings.append(
                f"[{model_ref.tracee}] '{nom}' : hauteur incoherente entre ses "
                f"{ref.n_instances} instances (moyenne {ref.hauteur_cm}cm, "
                f"ecart-type {ref.ecart_type_hauteur_cm}cm) - a verifier"
            )
    return warnings


def save_reference_table(table: dict[str, ModelReference], out_path: str) -> None:
    """Sauvegarde la table complete en JSON, lisible et versionnable."""
    serializable = {}
    for tracee_name, model_ref in table.items():
        serializable[tracee_name] = {
            "code_modele": model_ref.code_modele,
            "pieces": {nom: asdict(ref) for nom, ref in model_ref.pieces.items()},
        }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
