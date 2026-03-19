"""
Transforma texto grifado em {{variaveis}} no .docx
7) (Petição) Cobrança - Contrato APP ou CAIXA ELETRÔNICO.docx
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/7) (Petição) Cobrança - Contrato APP ou CAIXA ELETRÔNICO.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/7) (Petição) Cobrança App-Caixa - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_cobranca_app.json"

VARIABLE_MAP = {
    (0, 1): {"var": "comarca", "desc": "Comarca onde tramita o processo", "placeholder": "DE {{comarca}}"},
    (13, 8): {"var": "nome_reu", "desc": "Nome completo do réu", "placeholder": "{{nome_reu}},"},
    (13, 9): {"var": "qualificacao_reu", "desc": "Qualificação completa do réu (nacionalidade, estado civil, profissão, CPF, endereço)", "placeholder": "{{qualificacao_reu}}"},
    (20, 1): {"var": "data_contrato", "desc": "Data de contratação do empréstimo", "placeholder": "{{data_contrato}}"},
    (20, 3): {"var": "plataforma_contratacao", "desc": "Plataforma de contratação (ex: SICOOBNET WAP EMPRESARIAL / CELULAR)", "placeholder": "{{plataforma_contratacao}},"},
    (20, 5): {"var": "detalhes_contrato_valor", "desc": "Número do contrato e valor contratado com extenso", "placeholder": "{{detalhes_contrato_valor}},"},
    (20, 7): {"var": "valor_total_emprestimo", "desc": "Valor total do empréstimo com extenso", "placeholder": "R$ {{valor_total_emprestimo}}."},
    (22, 1): {"var": "quantidade_parcelas", "desc": "Quantidade de parcelas com extenso", "placeholder": "{{quantidade_parcelas}}"},
    (22, 3): {"var": "valor_parcela", "desc": "Valor da parcela com extenso", "placeholder": "R$ {{valor_parcela}},"},
    (22, 5): {"var": "datas_pagamento_inicio_fim", "desc": "Datas de início e término dos pagamentos", "placeholder": "{{datas_pagamento_inicio_fim}}."},
    (26, 1): {"var": "tipo_contrato_eletronico", "desc": "Tipo de contrato (ex: contrato eletrônico de empréstimo)", "placeholder": "{{tipo_contrato_eletronico}}"},
    (42, 2): {"var": "valor_debito_total", "desc": "Valor total do débito atualizado com extenso", "placeholder": "R$ {{valor_debito_total}}"},
    (52, 3): {"var": None, "placeholder": "R$ ", "desc": ""},
    (52, 5): {"var": "valor_condenacao", "desc": "Valor da condenação pleiteada com extenso", "placeholder": "{{valor_condenacao}}"},
    (52, 6): {"var": None, "placeholder": ",", "desc": ""},
    (68, 0): {"var": "pedido_prazo_custas", "desc": "Pedido de prazo para custas (condicional)", "placeholder": "{{pedido_prazo_custas}}"},
    (72, 1): {"var": None, "placeholder": "de ", "desc": ""},
    (72, 2): {"var": "valor_causa", "desc": "Valor da causa com extenso", "placeholder": "R$ {{valor_causa}}"},
    (72, 3): {"var": None, "placeholder": ".", "desc": ""},
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
    "title": "Ação de Cobrança - App ou Caixa Eletrônico",
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
