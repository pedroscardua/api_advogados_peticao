"""
Transforma texto grifado em {{variaveis}} no .docx
4) (Petição) Inicial - BUSCA E APREENSÃO

Mantém toda a formatação original. Remove highlight após substituição.
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/4) (Petição) Inicial - BUSCA E APREENSÃO.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/4) (Petição) Inicial - BUSCA E APREENSÃO - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_busca_apreensao.json"

# ---------------------------------------------------------------------------
# MAPEAMENTO (para_idx, run_idx) → variável
#
# Parágrafo 10: qualificação do réu (empresa)
# Parágrafo 18: data e nº do contrato
# Parágrafos 23-26: dados do veículo (ficha técnica)
# Parágrafo 28: valores e parcelas
# Parágrafo 32: meio de constituição em mora
# Parágrafo 34: saldo devedor atualizado
# Parágrafo 44: avalistas
# Parágrafo 70: trecho condicional sobre custas
# Parágrafo 72: valor da causa
# ---------------------------------------------------------------------------
VARIABLE_MAP = {
    # ── P10: qualificação do réu ─────────────────────────────────────────────
    (10, 10): {
        "var": "nome_reu",
        "desc": "Nome/razão social completa do réu (devedor fiduciante)",
        "placeholder": "{{nome_reu}}",
    },
    (10, 11): {
        "var": "qualificacao_reu",
        "desc": (
            "Qualificação completa do réu: natureza jurídica (PJ) ou dados pessoais (PF), "
            "CNPJ/CPF e endereço completo. "
            "Para PJ: ', pessoa jurídica de direito privado, inscrita no CNPJ/MF sob o n° "
            "XX.XXX.XXX/XXXX-XX, com endereço comercial na [ENDEREÇO COMPLETO]'. "
            "Para PF: ', [NACIONALIDADE], [ESTADO CIVIL], [PROFISSÃO], inscrito(a) no "
            "CPF/MF sob o n° XXX.XXX.XXX-XX, residente e domiciliado(a) na [ENDEREÇO]'."
        ),
        "placeholder": "{{qualificacao_reu}}",
    },

    # ── P18: dados do contrato ───────────────────────────────────────────────
    (18, 1): {
        "var": "data_assinatura_contrato",
        "desc": "Data de assinatura do contrato/cédula no formato DD/MM/AAAA",
        "placeholder": "{{data_assinatura_contrato}}",
    },
    (18, 3): {
        "var": "tipo_e_numero_contrato",
        "desc": (
            "Tipo e número do título contratual em maiúsculas. "
            "Formato: '[TIPO DO TÍTULO] nº [NÚMERO]'. "
            "Exemplo: 'CÉDULA DE CRÉDITO BANCÁRIO nº 1236858'"
        ),
        "placeholder": "{{tipo_e_numero_contrato}}",
    },

    # ── P23-26: ficha técnica do veículo (bem alienado fiduciariamente) ──────
    # Estes runs são pares rótulo+valor; substituímos apenas os VALORES.
    # Os rótulos (MARCA:, TIPO:, etc.) permanecem como texto normal no placeholder.
    (23, 0): {
        "var": None,  # rótulo "MARCA:" — mantém literal
        "placeholder": "MARCA:",
        "desc": "",
    },
    (23, 1): {
        "var": "veiculo_marca",
        "desc": "Marca do veículo dado em alienação fiduciária (ex: RENAULT, VOLKSWAGEN, FIAT)",
        "placeholder": "    {{veiculo_marca}}                         ",
    },
    (23, 2): {
        "var": None,  # rótulo "TIPO:" — mantém literal
        "placeholder": "TIPO:",
        "desc": "",
    },
    (23, 3): {
        "var": "veiculo_tipo",
        "desc": "Tipo/categoria do veículo (ex: AUTOMÓVEL, CAMINHONETE, MOTOCICLETA)",
        "placeholder": "            {{veiculo_tipo}}",
    },
    (24, 0): {
        "var": None,
        "placeholder": "MODELO:",
        "desc": "",
    },
    (24, 1): {
        "var": "veiculo_modelo",
        "desc": "Modelo completo do veículo (ex: SANDERO STW 16 HP, GOL 1.0, ONIX PLUS)",
        "placeholder": "    {{veiculo_modelo}}               ",
    },
    (24, 2): {
        "var": None,
        "placeholder": "CHASSI:     ",
        "desc": "",
    },
    (24, 3): {
        "var": "veiculo_chassi",
        "desc": "Número do chassi do veículo (17 caracteres alfanuméricos)",
        "placeholder": "{{veiculo_chassi}}",
    },
    (25, 0): {
        "var": None,
        "placeholder": "COR:        ",
        "desc": "",
    },
    (25, 1): {
        "var": "veiculo_cor",
        "desc": "Cor do veículo (ex: VERMELHA, PRATA, BRANCA, PRETA)",
        "placeholder": "    {{veiculo_cor}}                                ",
    },
    (25, 2): {
        "var": None,
        "placeholder": "ANO:",
        "desc": "",
    },
    (25, 3): {
        "var": "veiculo_ano",
        "desc": "Ano de fabricação/modelo do veículo no formato AAAA/AAAA (ex: 2013/2014)",
        "placeholder": "            {{veiculo_ano}}",
    },
    (26, 0): {
        "var": None,
        "placeholder": "PLACA:              ",
        "desc": "",
    },
    (26, 1): {
        "var": "veiculo_placa",
        "desc": "Placa do veículo no formato AAA9999 ou AAA9A99 (Mercosul)",
        "placeholder": "{{veiculo_placa}}                             ",
    },
    (26, 2): {
        "var": None,
        "placeholder": "RENAVAM:    ",
        "desc": "",
    },
    (26, 3): {
        "var": "veiculo_renavam",
        "desc": "Número do RENAVAM do veículo (11 dígitos)",
        "placeholder": "{{veiculo_renavam}}",
    },

    # ── P28: valores do contrato ─────────────────────────────────────────────
    (28, 1): {
        "var": "valor_financiado",
        "desc": (
            "Valor total financiado/contraído no contrato, com extenso. "
            "Formato: 'R$ XX.XXX,XX (valor por extenso)'"
        ),
        "placeholder": "{{valor_financiado}}",
    },
    (28, 3): {
        "var": "descricao_parcelas",
        "desc": (
            "Descrição do número e periodicidade das parcelas. "
            "Formato: 'XX (valor por extenso) prestações fixas, mensais e consecutivas'"
        ),
        "placeholder": "{{descricao_parcelas}}",
    },
    (28, 5): {
        "var": "valor_parcela",
        "desc": (
            "Valor de cada parcela com extenso. "
            "Formato: 'R$ XXX,XX (valor por extenso)'"
        ),
        "placeholder": "{{valor_parcela}}",
    },
    (28, 7): {
        "var": "data_vencimento_primeira_parcela",
        "desc": "Data de vencimento da primeira parcela no formato DD/MM/AAAA",
        "placeholder": "{{data_vencimento_primeira_parcela}}",
    },
    (28, 9): {
        "var": "data_vencimento_ultima_parcela",
        "desc": "Data de vencimento da última parcela no formato DD/MM/AAAA",
        "placeholder": "{{data_vencimento_ultima_parcela}}",
    },

    # ── P32: constituição em mora ────────────────────────────────────────────
    (32, 1): {
        "var": "meio_constituicao_mora",
        "desc": (
            "Meio pelo qual o devedor foi constituído em mora. "
            "Exemplos: 'Notificação Extrajudicial (doc. anexo),', "
            "'carta com aviso de recebimento (doc. anexo),' "
            "(incluir vírgula ao final)"
        ),
        "placeholder": "{{meio_constituicao_mora}}",
    },

    # ── P34: saldo devedor atualizado ────────────────────────────────────────
    (34, 1): {
        "var": "valor_debito_atualizado",
        "desc": (
            "Saldo devedor total atualizado na data da petição (vencido + vincendo + encargos), "
            "com extenso. Formato: 'R$ XX.XXX,XX (valor por extenso)'"
        ),
        "placeholder": "{{valor_debito_atualizado}}",
    },
    (34, 2): {
        # vírgula em run separado — mantém sintaticamente
        "var": None,
        "placeholder": ",",
        "desc": "",
    },

    # ── P44: avalistas ───────────────────────────────────────────────────────
    (44, 0): {
        "var": "texto_intro_avalistas",
        "desc": (
            "Trecho introdutório do pedido de intimação dos avalistas. "
            "Se houver avalista(s): 'Requer ainda a intimação dos avalistas do contrato, '. "
            "Se não houver avalistas: deixar vazio (string vazia)."
        ),
        "placeholder": "{{texto_intro_avalistas}}",
    },
    (44, 1): {
        "var": "nome_avalista_1",
        "desc": "Nome completo do primeiro avalista",
        "placeholder": "{{nome_avalista_1}}",
    },
    (44, 2): {
        "var": "qualificacao_avalista_1",
        "desc": (
            "Qualificação completa do primeiro avalista: nacionalidade, estado civil, profissão, "
            "CPF e endereço, seguida de ' e ' (conjunção para ligar ao 2º avalista, se houver). "
            "Formato: ', [NACIONAL.], [EST. CIVIL], [PROFISSÃO], inscrito(a) no CPF/MF sob o "
            "nº XXX.XXX.XXX-XX, residente e domiciliado(a) na [ENDEREÇO] e '"
        ),
        "placeholder": "{{qualificacao_avalista_1}}",
    },
    (44, 3): {
        "var": "nome_avalista_2",
        "desc": (
            "Nome completo do segundo avalista (se houver). "
            "Deixar vazio se houver apenas um avalista."
        ),
        "placeholder": "{{nome_avalista_2}}",
    },
    (44, 4): {
        "var": "qualificacao_avalista_2",
        "desc": (
            "Qualificação completa do segundo avalista: nacionalidade, estado civil, profissão, "
            "CPF, seguida da finalidade do pedido. "
            "Formato: ', [NACIONAL.], [EST. CIVIL], [PROFISSÃO], inscrito(a) no CPF/MF "
            "[XXX.XXX.XXX-XX], para que tenha conhecimento da presente ação.' "
            "Deixar vazio se não houver segundo avalista."
        ),
        "placeholder": "{{qualificacao_avalista_2}}",
    },

    # ── P70: trecho condicional sobre custas ─────────────────────────────────
    (70, 0): {
        "var": "texto_prazo_custas",
        "desc": (
            "Trecho condicional sobre pedido de prazo para recolhimento de custas iniciais. "
            "Se aplicável: manter o texto completo sobre prazo de 15 dias e art. 290 CPC. "
            "Se não aplicável (custas já recolhidas): deixar vazio."
        ),
        "placeholder": "{{texto_prazo_custas}}",
    },

    # ── P72: valor da causa ──────────────────────────────────────────────────
    (72, 0): {
        "var": None,
        "placeholder": "Dá-se à presente causa o valor de ",
        "desc": "",
    },
    (72, 1): {
        "var": "valor_causa",
        "desc": (
            "Valor atribuído à causa para efeitos processuais, com extenso. "
            "Formato: 'R$ XX.XXX,XX (valor por extenso)'"
        ),
        "placeholder": "{{valor_causa}}",
    },
    (72, 2): {
        "var": None,
        "placeholder": ".",
        "desc": "",
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
print(f"\n📋 {len(applied)} substituição(ões) com variáveis:\n")
for item in applied:
    print(f"  [P{item['para']:03d}/R{item['run']:02d}] {{{{{item['var']}}}}} ← \"{item['original'][:70]}\"")

# ---------------------------------------------------------------------------
# JSON SCHEMA
# ---------------------------------------------------------------------------

seen = set()
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Petição Inicial — Busca e Apreensão (Alienação Fiduciária)",
    "description": (
        "Schema de variáveis para preenchimento automático do template de Ação de "
        "Busca e Apreensão com base em Cédula de Crédito Bancário / Alienação Fiduciária. "
        "Cada campo representa uma informação específica do caso a ser preenchida "
        "pela LLM com base nos documentos fornecidos."
    ),
    "type": "object",
    "required": [],
    "properties": {},
}

for key in sorted(VARIABLE_MAP.keys()):
    m = VARIABLE_MAP[key]
    var = m["var"]
    if not var or var in seen:
        continue
    seen.add(var)
    schema["required"].append(var)
    schema["properties"][var] = {
        "type": "string",
        "description": m["desc"],
        "example_placeholder": m["placeholder"],
    }

with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print(f"\n📄 JSON Schema gerado: {SCHEMA_FILE}")
print(f"\nVariáveis únicas ({len(schema['properties'])}):")
for var in schema["required"]:
    print(f"  • {{{{{var}}}}}")
