"""
Transforma texto grifado em {{variaveis}} no .docx
4) (Petição) Inicial - BUSCA E APREENSÃO.docx

Refeito com índices precisos detectados no scan.
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/4) (Petição) Inicial - BUSCA E APREENSÃO.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/4) (Petição) Inicial - Busca e Apreensão - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_busca_apreensao.json"

VARIABLE_MAP = {
    # P002: Comarca
    (2, 1): {"var": "comarca", "desc": "Comarca/Cidade", "placeholder": "{{comarca}}"},

    # P016: Réu
    (16, 10): {"var": "nome_reu", "desc": "Nome do réu", "placeholder": "{{nome_reu}}"},
    (16, 11): {"var": "qualificacao_reu", "desc": "Qualificação completa do réu", "placeholder": "{{qualificacao_reu}}"},

    # P018: Contrato
    (18, 1): {"var": "data_assinatura_contrato", "desc": "Data da assinatura do contrato", "placeholder": "{{data_assinatura_contrato}}"},
    (18, 3): {"var": "tipo_e_numero_titulo", "desc": "Tipo e número do título (Cédula nº X)", "placeholder": "{{tipo_e_numero_titulo}}"},

    # P023: Veículo (Marca/Tipo)
    (23, 1): {"var": "veiculo_marca", "desc": "Marca do veículo", "placeholder": "{{veiculo_marca}}"},
    (23, 3): {"var": "veiculo_tipo", "desc": "Tipo do veículo", "placeholder": "{{veiculo_tipo}}"},

    # P024: Veículo (Modelo/Chassi)
    (24, 1): {"var": "veiculo_modelo", "desc": "Modelo do veículo", "placeholder": "{{veiculo_modelo}}"},
    (24, 3): {"var": "veiculo_chassi", "desc": "Chassi do veículo", "placeholder": "{{veiculo_chassi}}"},

    # P025: Veículo (Cor/Ano)
    (25, 1): {"var": "veiculo_cor", "desc": "Cor do veículo", "placeholder": "{{veiculo_cor}}"},
    (25, 3): {"var": "veiculo_ano", "desc": "Ano do veículo", "placeholder": "{{veiculo_ano}}"},

    # P026: Veículo (Placa/Renavam)
    (26, 1): {"var": "veiculo_placa", "desc": "Placa do veículo", "placeholder": "{{veiculo_placa}}"},
    (26, 3): {"var": "veiculo_renavam", "desc": "Renavam do veículo", "placeholder": "{{veiculo_renavam}}"},

    # P028: Valores
    (28, 1): {"var": "valor_total_financiado", "desc": "Valor total financiado com extenso", "placeholder": "{{valor_total_financiado}}"},
    (28, 3): {"var": "regra_pagamento_parcelas", "desc": "Descrição das parcelas (ex: 48 parcelas fixas...)", "placeholder": "{{regra_pagamento_parcelas}}"},
    (28, 5): {"var": "valor_parcela_com_extenso", "desc": "Valor da parcela com extenso", "placeholder": "{{valor_parcela_com_extenso}}"},
    (28, 7): {"var": "data_primeira_parcela", "desc": "Vencimento da primeira parcela", "placeholder": "{{data_primeira_parcela}}"},
    (28, 9): {"var": "data_ultima_parcela", "desc": "Vencimento da última parcela", "placeholder": "{{data_ultima_parcela}}"},

    # P032: Mora
    (32, 1): {"var": "meio_constituicao_mora", "desc": "Meio de constituição em mora (ex: Notificação Extrajudicial)", "placeholder": "{{meio_constituicao_mora}}"},

    # P034: Saldo Devedor
    (34, 1): {"var": "valor_saldo_devedor_com_extenso", "desc": "Saldo devedor total com extenso", "placeholder": "{{valor_saldo_devedor_com_extenso}}"},
    (34, 2): {"var": None, "placeholder": ",", "desc": ""},

    # P044: Avalistas
    (44, 0): {"var": "intro_avalistas", "desc": "Trecho de introdução dos avalistas", "placeholder": "{{intro_avalistas}}"},
    (44, 1): {"var": "nome_avalista_1", "desc": "Nome do primeiro avalista", "placeholder": "{{nome_avalista_1}}"},
    (44, 2): {"var": "qualificacao_avalista_1_e_intro_2", "desc": "Qualificação do avalista 1 e ligação para o segundo", "placeholder": "{{qualificacao_avalista_1_e_intro_2}}"},
    (44, 3): {"var": "nome_avalista_2", "desc": "Nome do segundo avalista", "placeholder": "{{nome_avalista_2}}"},
    (44, 4): {"var": "qualificacao_avalista_2", "desc": "Qualificação do segundo avalista", "placeholder": "{{qualificacao_avalista_2}}"},

    # P070: Custas
    (70, 0): {"var": "pedido_prazo_custas_inicial", "desc": "Pedido de prazo para custas", "placeholder": "{{pedido_prazo_custas_inicial}}"},

    # P072: Valor da Causa
    (72, 0): {"var": None, "placeholder": "Dá-se à presente causa o valor de ", "desc": ""},
    (72, 1): {"var": "valor_causa", "desc": "Valor da causa com extenso", "placeholder": "{{valor_causa}}"},
    (72, 2): {"var": None, "placeholder": ".", "desc": ""},
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
print(f"DONE. Replaced {len(applied)} variables in File 4. Template: {OUTPUT_FILE}")
