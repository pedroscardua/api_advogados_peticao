"""
Transforma texto grifado em {{variaveis}} no .docx
8) (Petição) MONITÓRIA_ Confissão de Dívidas SEM ASSINATURA.docx

Refeito com índices precisos detectados no scan.
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/8) (Petição) MONITÓRIA_ Confissão de Dívidas SEM ASSINATURA.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/8) (Petição) Monitória - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_monitoria.json"

VARIABLE_MAP = {
    # P000: Comarca
    (0, 1): {"var": "comarca", "desc": "Comarca/Cidade", "placeholder": "{{comarca}}"},

    # P007: Qualificação
    (7, 9): {"var": "nome_reu_1", "desc": "Nome do primeiro réu", "placeholder": "{{nome_reu_1}}"},
    (7, 10): {"var": None, "placeholder": ", ", "desc": ""},
    (7, 11): {"var": "qualificacao_reu_1_e_intro_2", "desc": "Qualificação completa do réu 1 e introdução do réu 2", "placeholder": "{{qualificacao_reu_1_e_intro_2}} "},
    (7, 12): {"var": "nome_reu_2", "desc": "Nome do segundo réu", "placeholder": "{{nome_reu_2}}"},
    (7, 13): {"var": "qualificacao_reu_2", "desc": "Qualificação completa do réu 2", "placeholder": "{{qualificacao_reu_2}}"},

    # P011: Dados específicos de agência/réu
    (11, 0): {"var": "referencia_reu_unidade", "desc": "Referência ao réu ou unidade (ex: O 1ª Ré)", "placeholder": "{{referencia_reu_unidade}}"},
    (11, 2): {"var": "agencia_numero", "desc": "Número da agência", "placeholder": "{{agencia_numero}}"},
    (11, 4): {"var": "cidade_agencia", "desc": "Cidade da agência", "placeholder": "{{cidade_agencia}}"},

    # P013: Detalhes da Confissão de Dívida
    (13, 1): {"var": "data_pactuacao", "desc": "Data da pactuação", "placeholder": "{{data_pactuacao}}"},
    (13, 3): {"var": "nome_instrumento", "desc": "Nome do instrumento (Confissão de Dívida)", "placeholder": "{{nome_instrumento}}"},
    (13, 5): {"var": "numero_instrumento_e_valor_num", "desc": "Número do instrumento e valor numérico", "placeholder": "{{numero_instrumento_e_valor_num}}"},
    (13, 6): {"var": "valor_inicial_extenso", "desc": "Valor inicial por extenso", "placeholder": "{{valor_inicial_extenso}}"},
    (13, 7): {"var": None, "placeholder": ", para pagamento em ", "desc": ""},
    (13, 8): {"var": "quantidade_parcelas_extenso", "desc": "Quantidade de parcelas por extenso", "placeholder": "{{quantidade_parcelas_extenso}}"},
    (13, 9): {"var": "valor_parcela_e_vencimento_parte_1", "desc": "Valor da parcela e início da cláusula de vencimento", "placeholder": " parcelas mensais e consecutivas no valor de R$ {{valor_parcela_e_vencimento_parte_1}}"},
    (13, 10): {"var": "valor_parcela_extenso", "desc": "Valor da parcela por extenso", "placeholder": "{{valor_parcela_extenso}}"},
    (13, 11): {"var": "regra_vencimento_subsequentes", "desc": "Regra de vencimento das parcelas", "placeholder": "{{regra_vencimento_subsequentes}}"},

    # P015: Cláusula de Vencimento Antecipado
    (15, 1): {"var": "termo_devedor_fiduciante", "desc": "Termo para o devedor (ex: Ré)", "placeholder": "{{termo_devedor_fiduciante}}"},
    (15, 3): {"var": "texto_clausula_vencimento", "desc": "Texto da cláusula de vencimento antecipado", "placeholder": "{{texto_clausula_vencimento}}"},

    # P017: Valor Atualizado
    (17, 1): {"var": None, "placeholder": "R$ ", "desc": ""},
    (17, 3): {"var": None, "placeholder": " ", "desc": ""},
    (17, 4): {"var": "valor_atualizado_extenso", "desc": "Valor atualizado por extenso", "placeholder": "{{valor_atualizado_extenso}}"},
    (17, 5): {"var": None, "placeholder": ",", "desc": ""},

    # P020: Chamada de devedor
    (20, 1): {"var": "termo_chamada_devedor", "desc": "Chamada do devedor (ex: a Ré)", "placeholder": "{{termo_chamada_devedor}}"},

    # P025: Resumo do Contrato
    (25, 1): {"var": "resumo_contrato_completo", "desc": "Resumo integral do contrato (repetição)", "placeholder": "{{resumo_contrato_completo}}"},

    # P029, P044, P046, P050: Gênero de Ré/Réu
    (29, 1): {"var": "genero_devedor", "desc": "Gênero (Ré/Réu)", "placeholder": "{{genero_devedor}}"},
    (44, 1): {"var": "genero_devedor", "placeholder": "{{genero_devedor}}", "desc": "Gênero (Ré/Réu)"},
    (44, 3): {"var": "valor_atualizado_completo_pedidos", "desc": "Valor atualizado com extenso nos pedidos", "placeholder": "{{valor_atualizado_completo_pedidos}}"},
    (46, 1): {"var": "genero_devedor", "placeholder": "{{genero_devedor}}", "desc": "Gênero (Ré/Réu)"},
    (50, 1): {"var": "genero_devedor", "placeholder": "{{genero_devedor}}", "desc": "Gênero (Ré/Réu)"},

    # P052: Audiência Virtual
    (52, 1): {"var": "texto_audiencia_virtual", "desc": "Trecho sobre audiência virtual", "placeholder": "{{texto_audiencia_virtual}}"},

    # P054: Intimações
    (54, 1): {"var": None, "placeholder": "intimações/publicações", "desc": ""},
    (54, 3): {"var": None, "placeholder": "com endereço eletrônico ", "desc": ""},
    (54, 4): {"var": None, "placeholder": ",", "desc": ""},

    # P058: Custas
    (58, 0): {"var": "pedido_prazo_custas_inicial", "desc": "Parágrafo de pedido de prazo para custas", "placeholder": "{{pedido_prazo_custas_inicial}}"},

    # P062: Valor da Causa
    (62, 0): {"var": "valor_causa_completo", "desc": "Parágrafo completo do valor da causa", "placeholder": "{{valor_causa_completo}}"},

    # P066: Local/Data final
    (66, 0): {"var": "local_e_data_assinatura", "desc": "Cidade e data por extenso", "placeholder": "{{local_e_data_assinatura}}"},
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
schema = {"$schema": "http://json-schema.org/draft-07/schema#", "title": "Ação Monitória", "type": "object", "required": [], "properties": {}}
seen = set()
for key in sorted(VARIABLE_MAP.keys()):
    m = VARIABLE_MAP[key]
    if not m["var"] or m["var"] in seen: continue
    seen.add(m["var"])
    schema["required"].append(m["var"])
    schema["properties"][m["var"]] = {"type": "string", "description": m["desc"]}

with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print(f"DONE. Replaced {len(applied)} variables in File 8. Template: {OUTPUT_FILE}")
