"""
conformity.py

Coeur du controle qualite : compare les dimensions mesurees d'un tracé A TESTER
aux dimensions nominales de la table de reference (construite a partir des 4
tracés valides), et rend un verdict piece par piece + un verdict global.

Logique de comparaison :
- Chaque piece du tracé teste est recherchee dans la reference du MEME MODELE
  (identifie par le code interne du tracé).
- Si la piece existe dans la reference : ses dimensions (largeur, hauteur) sont
  comparees a la reference, avec une tolerance en cm (+/- tolerance_cm).
- Si une piece du test n'a pas d'equivalent dans la reference (nom inconnu) :
  signalee comme anomalie separee (pas une simple non-conformite dimensionnelle).
- Si une piece de la reference est absente du test : signalee comme piece
  manquante (le tracé teste n'a pas toutes les pieces attendues).

Le verdict global est "conforme" seulement si : toutes les pieces attendues sont
presentes, aucune piece inconnue, et toutes les dimensions sont dans la tolerance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from measurement.dimensions import measure_piece
from acquisition.pdf_loader import get_pdf_page_size_cm
from database.reference_table import get_model_code


@dataclass
class DimensionCheck:
    dimension: str          # 'largeur' ou 'hauteur'
    valeur_mesuree_cm: float
    valeur_reference_cm: float
    ecart_cm: float
    tolerance_cm: float
    conforme: bool


@dataclass
class PieceVerdict:
    nom: str
    trouve_dans_reference: bool
    checks: list = field(default_factory=list)  # list[DimensionCheck]
    conforme: bool = True


@dataclass
class TraceeVerdict:
    tracee_teste: str
    code_modele: str
    tolerance_cm: float
    pieces: list = field(default_factory=list)      # list[PieceVerdict]
    pieces_manquantes: list = field(default_factory=list)  # attendues, absentes du test
    pieces_inconnues: list = field(default_factory=list)   # presentes, non reconnues
    conforme_global: bool = True
    taux_conformite_pct: float = 100.0


def evaluate_tracee(
    test_annotations_path: str,
    test_pdf_path: str,
    reference_table_path: str,
    tolerance_cm: float = 3.0,
) -> TraceeVerdict:
    """Evalue la conformite d'un tracé teste par rapport a la table de reference.

    Args:
        test_annotations_path: JSON d'annotations du tracé a tester (meme format
            que ceux exportes par l'outil d'annotation).
        test_pdf_path: PDF du tracé a tester (pour l'echelle et le code modele).
        reference_table_path: JSON de la table de reference (genere par
            reference_table.save_reference_table).
        tolerance_cm: tolerance admise en cm sur chaque dimension.
    """
    with open(test_annotations_path, encoding='utf-8') as f:
        test_data = json.load(f)
    with open(reference_table_path, encoding='utf-8') as f:
        ref_table = json.load(f)

    w_px, h_px = test_data['image_original_size_px']
    w_cm, h_cm = get_pdf_page_size_cm(test_pdf_path)
    scale_cm_per_px = ((w_cm / w_px) + (h_cm / h_px)) / 2

    code_modele = get_model_code(test_pdf_path)

    # trouver la reference correspondant a ce modele (par code, pas par nom de tracé)
    matching_model = None
    for tracee_name, model_data in ref_table.items():
        if model_data['code_modele'] == code_modele:
            matching_model = model_data
            break

    if matching_model is None:
        raise ValueError(
            f"Aucune reference trouvee pour le modele '{code_modele}'. "
            f"Modeles disponibles: {[m['code_modele'] for m in ref_table.values()]}"
        )

    reference_pieces = matching_model['pieces']

    # mesurer chaque piece du tracé teste
    verdict = TraceeVerdict(
        tracee_teste=Path(test_pdf_path).stem,
        code_modele=code_modele,
        tolerance_cm=tolerance_cm,
    )

    noms_testes = set()
    for piece in test_data['pieces']:
        nom = piece['nom'].strip().upper()
        noms_testes.add(nom)
        m = measure_piece(piece['points_original_px'], scale_cm_per_px)

        if nom not in reference_pieces:
            verdict.pieces_inconnues.append(nom)
            continue

        ref = reference_pieces[nom]
        checks = []
        for dim, val_mesuree, val_ref in [
            ('largeur', m.largeur_cm, ref['largeur_cm']),
            ('hauteur', m.hauteur_cm, ref['hauteur_cm']),
        ]:
            ecart = round(abs(val_mesuree - val_ref), 2)
            checks.append(DimensionCheck(
                dimension=dim,
                valeur_mesuree_cm=val_mesuree,
                valeur_reference_cm=val_ref,
                ecart_cm=ecart,
                tolerance_cm=tolerance_cm,
                conforme=ecart <= tolerance_cm,
            ))

        piece_conforme = all(c.conforme for c in checks)
        verdict.pieces.append(PieceVerdict(nom=nom, trouve_dans_reference=True, checks=checks, conforme=piece_conforme))

    # pieces attendues (reference) mais absentes du test
    verdict.pieces_manquantes = [nom for nom in reference_pieces if nom not in noms_testes]

    # verdict global
    n_pieces_ok = sum(1 for p in verdict.pieces if p.conforme)
    n_pieces_total = len(verdict.pieces)
    verdict.taux_conformite_pct = round(100 * n_pieces_ok / n_pieces_total, 1) if n_pieces_total else 0.0
    verdict.conforme_global = (
        n_pieces_ok == n_pieces_total
        and len(verdict.pieces_manquantes) == 0
        and len(verdict.pieces_inconnues) == 0
    )

    return verdict


def print_report(verdict: TraceeVerdict) -> None:
    """Affiche un rapport de conformite lisible dans la console."""
    print(f"{'='*70}")
    print(f"RAPPORT DE CONFORMITE - {verdict.tracee_teste}")
    print(f"Modele identifie : {verdict.code_modele}")
    print(f"Tolerance appliquee : +/- {verdict.tolerance_cm} cm")
    print(f"{'='*70}\n")

    for p in verdict.pieces:
        statut = "OK  " if p.conforme else "!!! "
        print(f"{statut}{p.nom}")
        if not p.conforme:
            for c in p.checks:
                if not c.conforme:
                    print(f"       -> {c.dimension}: mesure {c.valeur_mesuree_cm}cm vs "
                          f"reference {c.valeur_reference_cm}cm (ecart {c.ecart_cm}cm > "
                          f"tolerance {c.tolerance_cm}cm)")

    if verdict.pieces_manquantes:
        print(f"\nPieces manquantes (attendues, absentes du tracé teste) :")
        for nom in verdict.pieces_manquantes:
            print(f"   - {nom}")

    if verdict.pieces_inconnues:
        print(f"\nPieces inconnues (presentes, non reconnues dans la reference) :")
        for nom in verdict.pieces_inconnues:
            print(f"   - {nom}")

    print(f"\n{'='*70}")
    print(f"Taux de conformite : {verdict.taux_conformite_pct}%")
    print(f"VERDICT GLOBAL : {'CONFORME' if verdict.conforme_global else 'NON CONFORME'}")
    print(f"{'='*70}")
