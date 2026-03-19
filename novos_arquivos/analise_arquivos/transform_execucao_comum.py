"""
Transforma texto grifado em {{variaveis}} no .docx
5) (Petição) Execução Comum_.docx

Mantém toda a formatação original. Remove highlight após substituição.
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/5) (Petição) Execução Comum_.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/5) (Petição) Execução Comum - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_execucao_comum.json"

# ---------------------------------------------------------------------------
# MAPEAMENTO (para_idx, run_idx) → variável
# Note que alguns parágrafos têm muitos runs picados (ex: P10 e P31)
# ---------------------------------------------------------------------------
VARIABLE_MAP = {
    # ── P10: qualificação do réu (muito picado) ──────────────────────────────
    (10, 5): {"var": None, "placeholder": " em face de ", "desc": ""}, # white highlight placeholder
    (10, 6): {"var": None, "placeholder": "", "desc": ""},
    (10, 7): {"var": None, "placeholder": "", "desc": ""},
    (10, 8): {
        "var": "nome_empresa_executada",
        "desc": "Razão social completa da empresa executada",
        "placeholder": "{{nome_empresa_executada}}",
    },
    (10, 9): {"var": None, "placeholder": ", ", "desc": ""},
    (10, 10): {
        "var": "qualificacao_empresa_executada_parte_1",
        "desc": "Texto de qualificação jurídica inicial (ex: 'pessoa jurídica de direito privado, inscrita no CNPJ')",
        "placeholder": "{{qualificacao_empresa_executada_parte_1}}",
    },
    (10, 11): {
        "var": "qualificacao_empresa_executada_parte_2",
        "desc": "Restante da qualificação da empresa (CNPJ, cidade, sede)",
        "placeholder": "{{qualificacao_empresa_executada_parte_2}}",
    },
    (10, 12): {"var": None, "placeholder": ", à Rua ", "desc": ""},
    (10, 13): {
        "var": "logradouro_empresa",
        "desc": "Nome do logradouro da sede da empresa",
        "placeholder": "{{logradouro_empresa}}",
    },
    (10, 14): {"var": None, "placeholder": ", nº ", "desc": ""},
    (10, 15): {
        "var": "numero_endereco_empresa",
        "desc": "Número do endereço da sede da empresa",
        "placeholder": "{{numero_endereco_empresa}}",
    },
    (10, 16): {"var": None, "placeholder": ", Bairro ", "desc": ""},
    (10, 17): {
        "var": "bairro_empresa",
        "desc": "Bairro da sede da empresa",
        "placeholder": "{{bairro_empresa}}",
    },
    (10, 18): {"var": None, "placeholder": ", CEP: ", "desc": ""},
    (10, 19): {
        "var": "cep_empresa",
        "desc": "CEP da sede da empresa",
        "placeholder": "{{cep_empresa}}",
    },
    (10, 20): {"var": None, "placeholder": " e ", "desc": ""},
    (10, 21): {
        "var": "nome_socio_executado",
        "desc": "Nome completo do sócio/avalista executado",
        "placeholder": "{{nome_socio_executado}}",
    },
    (10, 22): {"var": None, "placeholder": ", ", "desc": ""},
    (10, 23): {"var": "nacionalidade_socio", "desc": "Nacionalidade do sócio (brasileiro/a)", "placeholder": "{{nacionalidade_socio}}"},
    (10, 24): {"var": None, "placeholder": "(a)", "desc": ""},
    (10, 25): {"var": "estado_civil_socio", "desc": "Estado civil do sócio (casado/a)", "placeholder": "{{estado_civil_socio}}"},
    (10, 26): {"var": None, "placeholder": "(a)", "desc": ""},
    (10, 27): {"var": None, "placeholder": ", ", "desc": ""},
    (10, 28): {
        "var": "profissao_socio",
        "desc": "Profissão do sócio",
        "placeholder": "{{profissao_socio}}",
    },
    (10, 29): {"var": None, "placeholder": ", inscrito(", "desc": ""},
    (10, 30): {"var": None, "placeholder": "a)", "desc": ""},
    (10, 31): {"var": None, "placeholder": " no CPF/MF sob o nº ", "desc": ""},
    (10, 32): {
        "var": "cpf_socio",
        "desc": "CPF do sócio",
        "placeholder": "{{cpf_socio}}",
    },
    (10, 33): {"var": None, "placeholder": ", residente e domiciliado(a) na cidade de ", "desc": ""},
    (10, 34): {
        "var": "endereco_completo_socio",
        "desc": "Endereço residencial completo do sócio",
        "placeholder": "{{endereco_completo_socio}}",
    },

    # ── P31: dados do título (também muito picado) ──────────────────────────
    (31, 0): {"var": None, "placeholder": "O título executivo que embasa a presente demanda é uma Cédula de Crédito Bancário n° ", "desc": ""},
    (31, 1): {"var": "numero_cedula", "desc": "Número da Cédula de Crédito", "placeholder": "{{numero_cedula}}"},
    (31, 2): {"var": None, "placeholder": ", emitida em ", "desc": ""},
    (31, 3): {"var": "data_emissao_cedula", "desc": "Data de emissão da cédula", "placeholder": "{{data_emissao_cedula}}"},
    (31, 4): {"var": None, "placeholder": ",", "desc": ""},
    (31, 5): {"var": None, "placeholder": "", "desc": ""},
    (31, 6): {"var": None, "placeholder": " sendo o crédito contratado no valor de ", "desc": ""},
    (31, 7): {"var": None, "placeholder": "R$ ", "desc": ""},
    (31, 8): {"var": "valor_contratado_num", "desc": "Valor contratado numérico", "placeholder": "{{valor_contratado_num}}"},
    (31, 9): {"var": None, "placeholder": " (", "desc": ""},
    (31, 10): {"var": "valor_contratado_extenso", "desc": "Valor contratado por extenso", "placeholder": "{{valor_contratado_extenso}}"},
    (31, 11): {"var": None, "placeholder": "centavos)", "desc": ""},
    (31, 12): {"var": None, "placeholder": ", para ser pago em ", "desc": ""},
    (31, 13): {"var": None, "placeholder": "", "desc": ""},
    (31, 14): {"var": "quantidade_parcelas_num", "desc": "Quantidade de parcelas numérico", "placeholder": "{{quantidade_parcelas_num}}"},
    (31, 15): {"var": None, "placeholder": " (", "desc": ""},
    (31, 16): {"var": "quantidade_parcelas_extenso", "desc": "Quantidade de parcelas por extenso", "placeholder": "{{quantidade_parcelas_extenso}}"},
    (31, 17): {"var": None, "placeholder": ")", "desc": ""},
    (31, 18): {"var": None, "placeholder": " parcelas mensais, iniciando-se os pagamentos em ", "desc": ""},
    (31, 19): {"var": "data_inicio_pagamentos", "desc": "Data de início dos pagamentos", "placeholder": "{{data_inicio_pagamentos}}"},
    (31, 20): {"var": None, "placeholder": " com término previsto para ", "desc": ""},
    (31, 21): {"var": "data_termino_pagamentos", "desc": "Data de término dos pagamentos", "placeholder": "{{data_termino_pagamentos}}."},
    (31, 22): {"var": None, "placeholder": "", "desc": ""},

    # ── P33: amortização ───────────────────────────────────────────────────
    (33, 0): {
        "var": "texto_amortizacao_cotas",
        "desc": "Parágrafo completo sobre amortização de cotas (condicional)",
        "placeholder": "{{texto_amortizacao_cotas}}",
    },

    # ── P35: saldo devedor ──────────────────────────────────────────────────
    (35, 0): {"var": None, "placeholder": "Conforme planilha anexa, que preenche todos os requisitos do art. 28, § 2º da Lei 10.931/2004, o saldo devedor executado, é de ", "desc": ""},
    (35, 1): {"var": None, "placeholder": "", "desc": ""},
    (35, 2): {"var": None, "placeholder": "R$ ", "desc": ""},
    (35, 3): {"var": "valor_execucao_num", "desc": "Valor total da execução numérico", "placeholder": "{{valor_execucao_num}}"},
    (35, 4): {"var": None, "placeholder": " (", "desc": ""},
    (35, 5): {"var": "valor_execucao_extenso_parte_1", "desc": "Parte 1 do valor da execução por extenso", "placeholder": "{{valor_execucao_extenso_parte_1}}"},
    (35, 6): {"var": "valor_execucao_extenso_parte_2", "desc": "Parte 2 do valor da execução por extenso", "placeholder": "{{valor_execucao_extenso_parte_2}}"},
    (35, 7): {"var": "valor_execucao_extenso_parte_3", "desc": "Parte 3 do valor da execução por extenso", "placeholder": "{{valor_execucao_extenso_parte_3}}"},
    (35, 8): {"var": None, "placeholder": "entavos), ", "desc": ""},

    # ── P45: citação ────────────────────────────────────────────────────────
    (45, 1): {"var": None, "placeholder": " ", "desc": ""},
    (45, 2): {
        "var": "valor_citacao_completo",
        "desc": "Valor de citação completo (R$ numérico + extenso)",
        "placeholder": "{{valor_citacao_completo}}",
    },

    # ── P65: valor da causa ──────────────────────────────────────────────────
    (65, 1): {"var": None, "placeholder": " ", "desc": ""},
    (65, 2): {
        "var": "valor_causa_completo",
        "desc": "Valor da causa completo (R$ numérico + extenso)",
        "placeholder": "{{valor_causa_completo}}",
    },

    # ── P70: data ────────────────────────────────────────────────────────────
    (70, 2): {
        "var": "data_assinatura_por_extenso",
        "desc": "Data de assinatura por extenso (ex: 4 de dezembro de 2025)",
        "placeholder": "{{data_assinatura_por_extenso}}",
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
    "title": "Petição de Execução Comum",
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
