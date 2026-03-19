"""
Transforma texto grifado em {{variaveis}} no .docx
8) (Petição) MONITÓRIA_ Confissão de Dívidas SEM ASSINATURA.docx
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/8) (Petição) MONITÓRIA_ Confissão de Dívidas SEM ASSINATURA.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/8) (Petição) Monitória - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_monitoria.json"

VARIABLE_MAP = {
    (0, 1): {"var": "comarca", "desc": "Comarca onde tramita o processo", "placeholder": "DE {{comarca}}"},
    (11, 8): {"var": "nome_reu", "desc": "Nome completo do réu", "placeholder": "{{nome_reu}},"},
    (11, 9): {"var": "qualificacao_reu", "desc": "Qualificação completa do réu", "placeholder": "{{qualificacao_reu}}"},
    (13, 1): {"var": "data_pactuacao", "desc": "Data em que foi pactuada a operação", "placeholder": "{{data_pactuacao}}"},
    (13, 3): {"var": "nome_instrumento", "desc": "Nome do instrumento jurídico (ex: Instrumento Particular de Confissão de Dívida e Outras Avenças)", "placeholder": "{{nome_instrumento}}"},
    (13, 5): {"var": "numero_instrumento_e_valor", "desc": "Número do instrumento e valor inicial numérico", "placeholder": "nº {{numero_instrumento_e_valor}}"},
    (13, 6): {"var": "valor_inicial_extenso", "desc": "Valor inicial por extenso", "placeholder": "({{valor_inicial_extenso}})"},
    (13, 7): {"var": None, "placeholder": ", para pagamento em ", "desc": ""},
    (13, 8): {"var": "quantidade_parcelas_extenso", "desc": "Quantidade de parcelas por extenso", "placeholder": "{{quantidade_parcelas_extenso}}"},
    (13, 9): {"var": "detalhes_parcelas_vencimento", "desc": "Valor da parcela (num + ext) e datas de vencimento", "placeholder": " parcelas mensais e consecutivas no valor de R$ {{detalhes_parcelas_vencimento}}"},
    (13, 10): {"var": None, "placeholder": "", "desc": ""},
    (13, 11): {"var": None, "placeholder": "", "desc": ""},
    # Menções a "Ré" / "Réu" / "Réus" - serão mantidas como texto mas removido highlight. 
    # Para automação real, talvez fosse bom ter {{termo_reu}}, mas como é picado, só limparei o grifo se não for dado mutável.
    (15, 1): {"var": "termo_devedor_singular", "desc": "Termo para o devedor (ex: Ré / Réu)", "placeholder": "{{termo_devedor_singular}}"},
    (15, 3): {"var": "clausula_vencimento_antecipado", "desc": "Texto sobre vencimento antecipado ou cláusula específica", "placeholder": "{{clausula_vencimento_antecipado}}"},
    (17, 1): {"var": None, "placeholder": "R$ ", "desc": ""},
    (17, 2): {"var": "valor_atualizado_num", "desc": "Valor atualizado numérico", "placeholder": "{{valor_atualizado_num}}"},
    (17, 3): {"var": None, "placeholder": " ", "desc": ""},
    (17, 4): {"var": "valor_atualizado_extenso", "desc": "Valor atualizado por extenso", "placeholder": "({{valor_atualizado_extenso}})"},
    (17, 5): {"var": None, "placeholder": ",", "desc": ""},
    (20, 1): {"var": "termo_devedor_articulado", "desc": "Termo referenciando o devedor (ex: a Ré / o Réu)", "placeholder": "{{termo_devedor_articulado}}"},
    (25, 1): {"var": "resumo_contrato_completo", "desc": "Resumo completo dos termos do contrato (repetição)", "placeholder": "{{resumo_contrato_completo}}"},
    (29, 1): {"var": "termo_genero_devedor", "desc": "Gênero do devedor (ex: Ré / Réu)", "placeholder": "{{termo_genero_devedor}}"},
    (44, 1): {"var": "termo_genero_devedor_plural", "desc": "Termo plural para devedores (ex: Ré / Réu)", "placeholder": "{{termo_genero_devedor_plural}}"},
    (44, 3): {"var": "valor_atualizado_completo_pedidos", "desc": "Valor atualizado com extenso nos pedidos", "placeholder": "R$ {{valor_atualizado_completo_pedidos}},"},
    (46, 1): {"var": "termo_devedor_singular", "placeholder": "{{termo_devedor_singular}}", "desc": "Termo para o devedor"},
    (50, 1): {"var": "termo_genero_devedor_plural", "placeholder": "{{termo_genero_devedor_plural}}", "desc": "Termo plural para devedores"},
    (52, 1): {"var": "opcao_audiencia_virtual", "desc": "Texto sobre opção de audiência virtual (condicional)", "placeholder": "{{opcao_audiencia_virtual}}"},
    (54, 1): {"var": None, "placeholder": "intimações/publicações", "desc": ""}, # limpa grifo
    (54, 3): {"var": None, "placeholder": "com endereço eletrônico ", "desc": ""}, # limpa grifo
    (54, 4): {"var": None, "placeholder": ",", "desc": ""},
    (58, 0): {"var": "pedido_prazo_custas", "desc": "Pedido de prazo para custas (condicional)", "placeholder": "{{pedido_prazo_custas}}"},
    (62, 0): {"var": "valor_causa_completo", "desc": "Valor da causa com descrição", "placeholder": "Dá-se à causa o valor de R$ {{valor_causa_completo}}."},
    (66, 0): {"var": "local_e_data", "desc": "Cidade e data por extenso", "placeholder": "{{local_e_data}}."},
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
    "title": "Ação Monitória - Confissão de Dívida",
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
