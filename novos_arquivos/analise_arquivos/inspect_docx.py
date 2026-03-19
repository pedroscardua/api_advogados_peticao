"""
Inspects a .docx file for highlighted (grifado) text.
Checks both w:highlight and w:shd (shading) in run properties.
"""
from docx import Document
from docx.oxml.ns import qn
from lxml import etree
import sys

FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/2) (Petição) EXECUÇÃO - ASSINATURA ELETRÔNICA.docx"

doc = Document(FILE)

highlighted_runs = []

for para_idx, para in enumerate(doc.paragraphs):
    for run_idx, run in enumerate(para.runs):
        rpr = run._r.find(qn("w:rPr"))
        if rpr is None:
            continue

        highlight_el = rpr.find(qn("w:highlight"))
        shd_el = rpr.find(qn("w:shd"))

        highlight_color = None
        shd_color = None

        if highlight_el is not None:
            highlight_color = highlight_el.get(qn("w:val"))

        if shd_el is not None:
            fill = shd_el.get(qn("w:fill"))
            shd_val = shd_el.get(qn("w:val"))
            # Ignore "none" or "clear" fill with no actual color
            if fill and fill.upper() not in ("FFFFFF", "AUTO", ""):
                shd_color = fill

        if highlight_color or shd_color:
            text_snippet = run.text[:80].replace("\n", " ")
            highlighted_runs.append({
                "para": para_idx,
                "run": run_idx,
                "highlight": highlight_color,
                "shading_fill": shd_color,
                "text": text_snippet,
            })

if highlighted_runs:
    print(f"\n✅ Encontrados {len(highlighted_runs)} trecho(s) grifado(s):\n")
    for item in highlighted_runs:
        print(f"  [Parágrafo {item['para']:03d} | Run {item['run']:02d}]")
        print(f"    highlight  : {item['highlight']}")
        print(f"    shading    : {item['shading_fill']}")
        print(f"    texto      : \"{item['text']}\"")
        print()
else:
    print("\n⚠️  Nenhum texto grifado (highlight/shading) encontrado via python-docx.\n")
    print("Verificando XML bruto por w:highlight...")
    # Fallback: raw XML search
    body_xml = etree.tostring(doc.element.body, pretty_print=False).decode()
    if "w:highlight" in body_xml:
        print("  → w:highlight encontrado no XML! Pode estar em tabela/frame.")
    else:
        print("  → w:highlight NÃO encontrado no XML.")
    if "w:shd" in body_xml:
        print("  → w:shd encontrado no XML.")
    else:
        print("  → w:shd NÃO encontrado no XML.")
