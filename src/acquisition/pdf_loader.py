"""
pdf_loader.py

Chargement des tracés depuis les fichiers PDF vectoriels natifs generes par
Gerber AccuMark (AccuMark Marker PDF Print File Generator). Contrairement a
un scan/photo, ces PDF contiennent :
  - un calque vectoriel (les contours des pieces, traits pleins et pointilles)
  - un calque TEXTE reel et positionne (nom de piece, taille, code modele)

Ce module fournit deux choses :
  1. rasterize_pdf(path, dpi) -> image numpy (pour la segmentation / baseline classique)
  2. extract_text_layer(path) -> liste de mots avec leur position (x, y)
     Ceci remplace l'OCR pour le nommage des pieces : le texte est deja
     numerique et positionne dans le fichier source, donc plus fiable qu'une
     lecture optique sur image rasterisee.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import cv2
import fitz  # PyMuPDF


@dataclass
class TextWord:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float


def rasterize_pdf(pdf_path: str, dpi: int = 100, max_dim_px: int = 4000) -> np.ndarray:
    """Convertit la 1ere page d'un PDF en image numpy (BGR, pour usage OpenCV).

    Utilise PyMuPDF (fitz) plutot que pdftoppm/Poppler : c'est une dependance
    Python pure (pip install pymupdf), donc rien a installer separement sous
    Windows.

    Les plans de coupe SARTEX sont tres grands physiquement (parfois >2m de
    long), donc on plafonne le zoom automatiquement si l'image resultante
    depasserait max_dim_px, pour rester gerable en memoire.
    """
    doc = fitz.open(pdf_path)
    page = doc[0]

    zoom = dpi / 72.0  # 72 dpi = echelle 1:1 native du PDF
    page_w_px = page.rect.width * zoom
    page_h_px = page.rect.height * zoom
    if max(page_w_px, page_h_px) > max_dim_px:
        zoom = max_dim_px / max(page.rect.width, page.rect.height)

    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

    if pix.n == 4:  # RGBA -> BGR
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:  # RGB -> BGR
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:  # grayscale
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    doc.close()
    return img


def extract_text_layer(pdf_path: str) -> list[TextWord]:
    """Extrait les mots du calque texte reel du PDF, avec leurs coordonnees.

    Utilise PyMuPDF (fitz) plutot que pdfplumber : sur les plans de coupe
    AccuMark, une partie des libelles de pieces est imprimee en texte pivote
    (pour suivre l'orientation de la piece sur le plan). pdfplumber (base sur
    pdfminer) perd une partie de ce texte pivote, alors que PyMuPDF le lit
    correctement. Verifie sur Tracee1 : PyMuPDF retrouve les 25 occurrences
    attendues du code piece, contre seulement 14 avec pdfplumber.
    """
    words: list[TextWord] = []
    doc = fitz.open(pdf_path)
    page = doc[0]
    for x0, y0, x1, y1, text, *_ in page.get_text("words"):
        words.append(TextWord(text=text, x0=x0, y0=y0, x1=x1, y1=y1))
    doc.close()
    return words


def get_pdf_page_size_cm(pdf_path: str) -> tuple[float, float]:
    """Taille physique reelle de la page en cm (utile pour la calibration
    d'echelle : ces PDF sont a l'echelle 1:1 du plan de coupe reel).
    """
    doc = fitz.open(pdf_path)
    page = doc[0]
    width_cm = page.rect.width / 72 * 2.54
    height_cm = page.rect.height / 72 * 2.54
    doc.close()
    return width_cm, height_cm
