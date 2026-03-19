"""
Transforma texto grifado em {{variaveis}} no .docx
5) (Petição) Execução Comum_.docx

Refeito com índices precisos detectados no scan.
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/5) (Petição) Execução Comum_.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/5) (Petição) Execução Comum - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_execucao_comum.json"

# Mapeamento baseado no scan rigoroso (hl: color ou shd: fill)
VARIABLE_MAP = {
    # P000: Comarca
    (0, 2): {"var": "comarca", "desc": "Comarca/Cidade do processo", "placeholder": "{{comarca}}"},

    # P013: Qualificação (em face de...)
    (13, 5): {"var": None, "placeholder": "em face de", "desc": ""},
    (13, 6): {"var": None, "placeholder": " ", "desc": ""},
    (13, 7): {"var": None, "placeholder": "", "desc": ""},
    (13, 8): {"var": "nome_empresa_executada", "desc": "Nome da empresa executada", "placeholder": "{{nome_empresa_executada}}"},
    (13, 9): {"var": None, "placeholder": ", ", "desc": ""},
    (13, 10): {"var": "qualificacao_empresa_parte_1", "desc": "Parte 1 da qualificação da empresa", "placeholder": "{{qualificacao_empresa_parte_1}}"},
    (13, 11): {"var": "qualificacao_empresa_parte_2", "desc": "Parte 2 da qualificação da empresa (CNPJ, Sede)", "placeholder": "{{qualificacao_empresa_parte_2}}"},
    (13, 12): {"var": None, "placeholder": ", à Rua ", "desc": ""},
    (13, 13): {"var": "logradouro_empresa", "desc": "Rua da empresa", "placeholder": "{{logradouro_empresa}}"},
    (13, 14): {"var": None, "placeholder": ", nº ", "desc": ""},
    (13, 15): {"var": "numero_endereco_empresa", "desc": "Número do endereço da empresa", "placeholder": "{{numero_endereco_empresa}}"},
    (13, 16): {"var": None, "placeholder": ", Bairro ", "desc": ""},
    (13, 17): {"var": "bairro_empresa", "desc": "Bairro da empresa", "placeholder": "{{bairro_empresa}}"},
    (13, 18): {"var": None, "placeholder": ", CEP: ", "desc": ""},
    (13, 19): {"var": "cep_empresa", "desc": "CEP da empresa", "placeholder": "{{cep_empresa}}"},
    (13, 20): {"var": None, "placeholder": " e ", "desc": ""},
    (13, 21): {"var": "nome_socio_executado", "desc": "Nome do sócio executado", "placeholder": "{{nome_socio_executado}}"},
    (13, 22): {"var": None, "placeholder": ", ", "desc": ""},
    (13, 23): {"var": "nacionalidade_socio", "desc": "Nacionalidade do sócio", "placeholder": "{{nacionalidade_socio}}"},
    (13, 24): {"var": None, "placeholder": "(a)", "desc": ""},
    (13, 25): {"var": "estado_civil_socio", "desc": "Estado civil do sócio", "placeholder": "{{estado_civil_socio}}"},
    (13, 26): {"var": None, "placeholder": "(a)", "desc": ""},
    (13, 27): {"var": None, "placeholder": ", ", "desc": ""},
    (13, 28): {"var": "profissao_socio", "desc": "Profissão do sócio", "placeholder": "{{profissao_socio}}"},
    (13, 29): {"var": None, "placeholder": ", inscrito(", "desc": ""},
    (13, 30): {"var": None, "placeholder": "a)", "desc": ""},
    (13, 31): {"var": None, "placeholder": " no CPF/MF sob o nº ", "desc": ""},
    (13, 32): {"var": "cpf_socio", "desc": "CPF do sócio", "placeholder": "{{cpf_socio}}"},
    (13, 33): {"var": None, "placeholder": ", residente e domiciliado(a) na cidade de ", "desc": ""},
    (13, 34): {"var": "endereco_completo_socio", "desc": "Endereço completo do sócio", "placeholder": "{{endereco_completo_socio}}"},

    # P031: Título Executivo
    (31, 0): {"var": None, "placeholder": "O título executivo que embasa a presente demanda é uma Cédula de Crédito Bancário n° ", "desc": ""},
    (31, 1): {"var": "numero_cedula", "desc": "Número da Cédula de Crédito", "placeholder": "{{numero_cedula}}"},
    (31, 2): {"var": None, "placeholder": ", emitida em ", "desc": ""},
    (31, 3): {"var": "data_emissao_cedula", "desc": "Data de emissão da cédula", "placeholder": "{{data_emissao_cedula}}"},
    (31, 4): {"var": None, "placeholder": ",", "desc": ""},
    (31, 5): {"var": None, "placeholder": " ", "desc": ""},
    (31, 6): {"var": None, "placeholder": "sendo o crédito contratado no valor de ", "desc": ""},
    (31, 7): {"var": None, "placeholder": "R$ ", "desc": ""},
    (31, 8): {"var": "valor_contratado_num", "desc": "Valor contratado numérico", "placeholder": "{{valor_contratado_num}}"},
    (31, 9): {"var": None, "placeholder": " (", "desc": ""},
    (31, 10): {"var": "valor_contratado_extenso", "desc": "Valor contratado por extenso", "placeholder": "{{valor_contratado_extenso}}"},
    (31, 11): {"var": None, "placeholder": "centavos)", "desc": ""},
    (31, 12): {"var": None, "placeholder": ", para ser pago em ", "desc": ""},
    (31, 13): {"var": None, "placeholder": " ", "desc": ""},
    (31, 14): {"var": "quantidade_parcelas_num", "desc": "Quantidade de parcelas numérico", "placeholder": "{{quantidade_parcelas_num}}"},
    (31, 15): {"var": None, "placeholder": " (", "desc": ""},
    (31, 16): {"var": "quantidade_parcelas_extenso", "desc": "Quantidade de parcelas por extenso", "placeholder": "{{quantidade_parcelas_extenso}}"},
    (31, 17): {"var": None, "placeholder": ")", "desc": ""},
    (31, 18): {"var": None, "placeholder": " parcelas mensais, iniciando-se os pagamentos em ", "desc": ""},
    (31, 19): {"var": "data_inicio_pagamentos", "desc": "Data de início dos pagamentos", "placeholder": "{{data_inicio_pagamentos}}"},
    (31, 20): {"var": None, "placeholder": " com término previsto para ", "desc": ""},
    (31, 21): {"var": "data_termino_pagamentos", "desc": "Data de término dos pagamentos", "placeholder": "{{data_termino_pagamentos}}"},
    (31, 22): {"var": None, "placeholder": ".", "desc": ""},

    # P033: Amortização
    (33, 0): {"var": "texto_amortizacao_cotas", "desc": "Parágrafo completo sobre amortização de cotas (condicional)", "placeholder": "{{texto_amortizacao_cotas}}"},

    # P035: Saldo Devedor
    (35, 0): {"var": None, "placeholder": "Conforme planilha anexa, que preenche todos os requisitos do art. 28, § 2º da Lei 10.931/2004, o saldo devedor executado, é de ", "desc": ""},
    (35, 1): {"var": None, "placeholder": " ", "desc": ""},
    (35, 2): {"var": None, "placeholder": "R$ ", "desc": ""},
    (35, 3): {"var": "valor_execucao_num", "desc": "Valor total da execução numérico", "placeholder": "{{valor_execucao_num}}"},
    (35, 4): {"var": None, "placeholder": " (", "desc": ""},
    (35, 5): {"var": "valor_execucao_extenso_parte_1", "desc": "Parte 1 do valor por extenso", "placeholder": "{{valor_execucao_extenso_parte_1}}"},
    (35, 6): {"var": "valor_execucao_extenso_parte_2", "desc": "Parte 2 do valor por extenso", "placeholder": "{{valor_execucao_extenso_parte_2}}"},
    (35, 7): {"var": "valor_execucao_extenso_parte_3", "desc": "Parte 3 do valor por extenso", "placeholder": "{{valor_execucao_extenso_parte_3}}"},
    (35, 8): {"var": None, "placeholder": "entavos), ", "desc": ""},

    # P045: Citação
    (45, 1): {"var": None, "placeholder": " ", "desc": ""},
    (45, 2): {"var": "valor_citacao_completo", "desc": "Valor de citação completo (R$ num + ext)", "placeholder": "{{valor_citacao_completo}}"},

    # P065: Valor da Causa
    (65, 1): {"var": None, "placeholder": " ", "desc": ""},
    (65, 2): {"var": "valor_causa_completo", "desc": "Valor da causa completo (R$ num + ext)", "placeholder": "{{valor_causa_completo}}"},

    # P070: Data
    (70, 2): {"var": "data_assinatura_por_extenso", "desc": "Data da petição por extenso", "placeholder": "{{data_assinatura_por_extenso}}"},
}

def remove_hl_and_shd(run):
    rPr = run._r.find(qn("w:rPr"))
    if rPr is not None:
        hl = rPr.find(qn("w:highlight"))
        if hl is not None: rPr.remove(hl)
        shd = rPr.find(qn("w:shd"))
        if shd is not None: rPr.remove(shd)

def replace_run_text(run, new_text):
    t_elements = run._r.findall(qn("w:t"))
    if t_elements:
        for t in t_elements[1:]: run._r.remove(t)
        t_elements[0].text = new_text
        if new_text != new_text.strip():
            t_elements[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    else:
        t = OxmlElement("w:t")
        t.text = new_text
        if new_text != new_text.strip():
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        run._r.append(t)

doc = Document(INPUT_FILE)
applied = []

for para_idx, para in enumerate(doc.paragraphs):
    for run_idx, run in enumerate(para.runs):
        key = (para_idx, run_idx)
        if key not in VARIABLE_MAP: continue
        mapping = VARIABLE_MAP[key]
        original_text = run.text
        replace_run_text(run, mapping["placeholder"])
        remove_hl_and_shd(run)
        if mapping["var"]:
            applied.append({"para": para_idx, "run": run_idx, "var": mapping["var"], "orig": original_text})

doc.save(OUTPUT_FILE)
schema = {"$schema": "http://json-schema.org/draft-07/schema#", "title": "Execução Comum", "type": "object", "required": [], "properties": {}}
seen = set()
for key in sorted(VARIABLE_MAP.keys()):
    m = VARIABLE_MAP[key]
    if not m["var"] or m["var"] in seen: continue
    seen.add(m["var"])
    schema["required"].append(m["var"])
    schema["properties"][m["var"]] = {"type": "string", "description": m["desc"]}

with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print(f"DONE. Replaced {len(applied)} variables. Template: {OUTPUT_FILE}")
