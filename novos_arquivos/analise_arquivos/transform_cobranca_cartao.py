"""
Transforma texto grifado em {{variaveis}} no .docx
6) (Petição) Cobrança - CARTÃO DE CRÉDITO.docx

Remove highlight e garante padrão {{variavel}} para dados do cliente.
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/6) (Petição) Cobrança - CARTÃO DE CRÉDITO.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/6) (Petição) Cobrança Cartão Crédito - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_cobranca_cartao.json"

# ---------------------------------------------------------------------------
# MAPEAMENTO (para_idx, run_idx) → variáveis
# ---------------------------------------------------------------------------
VARIABLE_MAP = {
    (0, 1): {
        "var": "comarca",
        "desc": "Comarca/cidade onde o processo tramita",
        "placeholder": "{{comarca}}",
    },
    (10, 9): {
        "var": "qualificacao_completa_reu",
        "desc": "Qualificação completa do réu: nome, nacionalidade, estado civil, profissão, CPF/CNPJ e endereço",
        "placeholder": "{{qualificacao_completa_reu}}",
    },
    (14, 1): {
        "var": "segmento_cartao",
        "desc": "Segmento do cartão de crédito (ex: SICOOBCARD MASTERCARD EMPRESARIAL PRO)",
        "placeholder": "{{segmento_cartao}}",
    },
    (14, 3): {
        "var": None, "placeholder": "", "desc": "", # remove instrução "(retirar esta informação...)"
    },
    (16, 1): {
        "var": "data_inicio_mora",
        "desc": "Data de início da inadimplência",
        "placeholder": "{{data_inicio_mora}}.",
    },
    (18, 1): {
        "var": "valor_debito_extenso",
        "desc": "Valor total do débito com extenso",
        "placeholder": "{{valor_debito_extenso}}",
    },
    (18, 2): {"var": None, "placeholder": ",", "desc": ""},
    (26, 1): {
        "var": "documentos_comprobatorios_1",
        "desc": "Texto descrevendo documentos anexos (ex: 'carreada juntamente com as faturas do cartão de crédito')",
        "placeholder": "{{documentos_comprobatorios_1}}",
    },
    (26, 3): {
        "var": "documentos_comprobatorios_2",
        "desc": "Texto complementar de documentos (ex: 'e extratos')",
        "placeholder": "{{documentos_comprobatorios_2}}",
    },
    (36, 1): {
        "var": "valor_debito_extenso", # reutiliza
        "placeholder": "{{valor_debito_extenso}}",
        "desc": "Valor total do débito com extenso",
    },
    (52, 1): {
        "var": "valor_causa_extenso",
        "desc": "Valor da causa com extenso",
        "placeholder": "{{valor_causa_extenso}}",
    },
    (57, 1): {
        "var": "data_assinatura",
        "desc": "Data de assinatura da petição",
        "placeholder": "{{data_assinatura}}",
    },
}

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def remove_highlight(rpr_el):
    hl = rpr_el.find(qn("w:highlight"))
    if hl is not None:
        rpr_el.remove(hl)

def replace_run_text(run, new_text):
    t_elements = run._r.findall(qn("w:t"))
    if t_elements:
        for t in t_elements[1:]:
            run._r.remove(t)
        t_elements[0].text = new_text
        if new_text != new_text.strip():
            t_elements[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    else:
        t = OxmlElement("w:t")
        t.text = new_text
        if new_text != new_text.strip():
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        run._r.append(t)

# ---------------------------------------------------------------------------
# PROCESSAMENTO
# ---------------------------------------------------------------------------

doc = Document(INPUT_FILE)
applied = []

for para_idx, para in enumerate(doc.paragraphs):
    for run_idx, run in enumerate(para.runs):
        key = (para_idx, run_idx)
        if key not in VARIABLE_MAP:
            continue
        mapping = VARIABLE_MAP[key]
        original_text = run.text
        replace_run_text(run, mapping["placeholder"])
        rpr = run._r.find(qn("w:rPr"))
        if rpr is not None:
            remove_highlight(rpr)
        if mapping["var"]:
            applied.append({
                "para": para_idx, "run": run_idx,
                "var": mapping["var"],
                "original": original_text,
                "replaced_with": mapping["placeholder"],
            })

doc.save(OUTPUT_FILE)
print(f"\n✅ Template gerado: {OUTPUT_FILE}")

schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Ação de Cobrança - Cartão de Crédito",
    "type": "object",
    "required": [],
    "properties": {},
}

seen = set()
for key in sorted(VARIABLE_MAP.keys()):
    m = VARIABLE_MAP[key]
    var = m["var"]
    if not var or var in seen: continue
    seen.add(var)
    schema["required"].append(var)
    schema["properties"][var] = {
        "type": "string",
        "description": m["desc"],
        "example_placeholder": m["placeholder"],
    }

with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print(f"📄 JSON Schema gerado: {SCHEMA_FILE}")
print(f"Variáveis únicas: {len(schema['properties'])}")
