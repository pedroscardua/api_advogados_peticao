"""
Transforma texto grifado (highlight) em {{variaveis}} no .docx
e gera schema JSON para preenchimento por LLM.

Mantém toda a formatação original (negrito, itálico, fonte, tamanho).
Remove o destaque de cor após substituição.
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from lxml import etree
import json
from copy import deepcopy

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/2) (Petição) EXECUÇÃO - ASSINATURA ELETRÔNICA.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/2) (Petição) EXECUÇÃO - ASSINATURA ELETRÔNICA - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_peticao_execucao.json"

# ---------------------------------------------------------------------------
# MAPEAMENTO: (para_idx, run_idx) → (variavel, descricao, placeholder)
# Os "placeholders" são o texto que será inserido no documento.
# Quando um run grifado mistura boilerplate + dado variável,
# o placeholder preserva o boilerplate e usa {{ }} só no dado.
# ---------------------------------------------------------------------------
VARIABLE_MAP = {
    # Parágrafo 0 — cabeçalho com comarca
    (0, 1): {
        "var": "comarca",
        "desc": "Comarca/cidade onde o processo tramita (ex: VARGINHA/MG)",
        "placeholder": "{{comarca}}",
    },

    # Parágrafo 10 — qualificação dos executados
    (10, 10): {
        "var": "nome_empresa_executada",
        "desc": "Razão social completa da empresa executada",
        "placeholder": "{{nome_empresa_executada}},",
    },
    (10, 11): {
        "var": "qualificacao_empresa_executada",
        # Este run contém boilerplate + CNPJ + endereço — tudo é dado do cliente
        "desc": (
            "Qualificação completa da empresa executada: natureza jurídica, CNPJ, "
            "endereço completo. Formato: ' pessoa jurídica de direito privado "
            "regularmente inscrita no CNPJ/MF sob o nº XX.XXX.XXX/XXXX-XX, "
            "com sede na cidade de [CIDADE] à [ENDEREÇO COMPLETO] e '"
        ),
        "placeholder": " {{qualificacao_empresa_executada}} e ",
    },
    (10, 12): {
        "var": "nome_socio_executado",
        "desc": "Nome completo do sócio/avalista pessoa física executado",
        "placeholder": "{{nome_socio_executado}}",
    },
    (10, 13): {
        "var": "qualificacao_socio_executado",
        "desc": (
            "Qualificação completa do sócio executado: nacionalidade, estado civil, "
            "profissão, CPF e endereço completo. Formato: ', [NACIONALIDADE], "
            "[ESTADO CIVIL], [PROFISSÃO], inscrito(a) no CPF/MF sob o nº "
            "XXX.XXX.XXX-XX, residente e domiciliado(a) na cidade de [CIDADE], "
            "à [ENDEREÇO COMPLETO]'"
        ),
        "placeholder": "{{qualificacao_socio_executado}}",
    },

    # Parágrafo 30 — dados da cédula de crédito
    (30, 1): {
        "var": "numero_cedula_credito",
        "desc": "Número da Cédula de Crédito Bancário (título executivo extrajudicial)",
        "placeholder": "{{numero_cedula_credito}},",
    },
    (30, 3): {
        "var": "data_emissao_cedula",
        "desc": "Data de emissão da Cédula de Crédito Bancário no formato DD/MM/AAAA",
        "placeholder": "{{data_emissao_cedula}}",
    },
    (30, 5): {
        "var": "nome_empresa_executada_curto",
        "desc": "Nome da empresa executada (forma abreviada conforme consta na cédula)",
        "placeholder": "{{nome_empresa_executada_curto}}",
    },
    (30, 8): {
        # "pelo(s) também executado(s)" — trecho condicional sobre avalista
        "var": "texto_avalista",
        "desc": (
            "Trecho condicional sobre o avalista: 'pelo(s) também executado(s)' "
            "se houver avalista pessoa física, ou omitir se não houver."
        ),
        "placeholder": "{{texto_avalista}}",
    },
    (30, 9): {
        "var": "nome_socio_executado_avalista",
        "desc": "Nome completo do sócio/avalista conforme consta na cédula de crédito",
        "placeholder": " {{nome_socio_executado_avalista}},",
    },
    (30, 12): {
        "var": "valor_original_cedula",
        "desc": (
            "Valor original da cédula de crédito bancário em formato monetário brasileiro, "
            "incluindo o valor por extenso entre parênteses. "
            "Formato: '$ XX.XXX,XX (valor por extenso)'"
        ),
        "placeholder": "$ {{valor_original_cedula}}",
    },
    (30, 15): {
        "var": "numero_parcelas",
        "desc": (
            "Quantidade de parcelas mensais da cédula, incluindo o número por extenso. "
            "Formato: 'XX (valor por extenso)'"
        ),
        "placeholder": "{{numero_parcelas}}",
    },
    (30, 17): {
        "var": "valor_parcela",
        "desc": (
            "Valor de cada parcela mensal em formato monetário brasileiro, "
            "incluindo o valor por extenso entre parênteses. "
            "Formato: 'R$ XX.XXX,XX (valor por extenso).'"
        ),
        "placeholder": "R$ {{valor_parcela}}",
    },

    # Parágrafo 32 — amortização (run inteiro é dado variável do caso)
    (32, 0): {
        "var": "texto_amortizacao_cotas",
        "desc": (
            "Frase completa sobre amortização de cotas no estatuto da cooperativa, "
            "incluindo o valor amortizado. Formato: 'De acordo com o estatuto social "
            "da cooperativa, foi amortizado na operação o valor de R$ X.XXX,XX "
            "(valor por extenso) à título de devolução de cotas.' "
            "Omitir este parágrafo se não houver amortização de cotas."
        ),
        "placeholder": "{{texto_amortizacao_cotas}}",
    },

    # Parágrafo 34 — saldo devedor executado
    (34, 1): {
        "var": "valor_execucao",
        "desc": (
            "Valor total do saldo devedor objeto da execução, em formato monetário "
            "brasileiro com extenso. Formato: 'R$ XX.XXX,XX (valor por extenso),'"
        ),
        "placeholder": "{{valor_execucao}},",
    },

    # Parágrafo 44 — citação/pagamento
    (44, 1): {
        "var": "valor_citacao",
        "desc": (
            "Valor total a ser pago pelo devedor na citação (pode diferir ligeiramente "
            "do valor_execucao por arredondamento/atualização). "
            "Formato: 'R$ XX.XXX,XX (valor por extenso)'"
        ),
        "placeholder": "{{valor_citacao}}",
    },

    # Parágrafo 55 — interesse em audiência (cyan — trecho condicional)
    (55, 1): {
        "var": "texto_interesse_audiencia",
        "desc": (
            "Trecho condicional sobre interesse do exequente em audiência de conciliação. "
            "Se o exequente TIVER interesse: incluir o texto completo sobre interesse "
            "em audiência de conciliação/mediação. "
            "Se NÃO tiver interesse: substituir por texto informando que não há interesse."
        ),
        "placeholder": "{{texto_interesse_audiencia}}",
    },

    # Parágrafo 65 — valor da causa
    (65, 1): {
        "var": "valor_causa",
        "desc": (
            "Valor atribuído à causa para efeitos processuais, em formato monetário "
            "brasileiro com extenso. Formato: 'R$ XX.XXX,XX (valor por extenso).'"
        ),
        "placeholder": "{{valor_causa}}",
    },

    # Parágrafo 70 — data do documento
    (70, 1): {
        "var": "data_documento",
        "desc": (
            "Data de assinatura/emissão do documento no formato por extenso. "
            "Formato: 'D de [mês] de AAAA' (ex: '4 de dezembro de 2025')"
        ),
        "placeholder": "{{data_documento}}",
    },
}

# ---------------------------------------------------------------------------
# PROCESSAMENTO
# ---------------------------------------------------------------------------

def remove_highlight(rpr_el):
    """Remove w:highlight element from rPr, preserving all other formatting."""
    hl = rpr_el.find(qn("w:highlight"))
    if hl is not None:
        rpr_el.remove(hl)


def replace_run_text(run, new_text):
    """
    Replaces the text content of a run while preserving all XML formatting.
    Handles runs with multiple w:t elements (rare but possible).
    """
    # Find existing w:t
    t_elements = run._r.findall(qn("w:t"))
    if t_elements:
        # Clear all but first, set first to new_text
        for t in t_elements[1:]:
            run._r.remove(t)
        t_elements[0].text = new_text
        # Preserve xml:space="preserve" if text has leading/trailing spaces
        if new_text != new_text.strip():
            t_elements[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    else:
        # Create w:t element
        t = OxmlElement("w:t")
        t.text = new_text
        if new_text != new_text.strip():
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        run._r.append(t)


doc = Document(INPUT_FILE)

applied = []
skipped = []

for para_idx, para in enumerate(doc.paragraphs):
    for run_idx, run in enumerate(para.runs):
        key = (para_idx, run_idx)
        if key not in VARIABLE_MAP:
            continue

        mapping = VARIABLE_MAP[key]
        original_text = run.text

        # Apply substitution
        replace_run_text(run, mapping["placeholder"])

        # Remove highlight color (clean template look)
        rpr = run._r.find(qn("w:rPr"))
        if rpr is not None:
            remove_highlight(rpr)

        applied.append({
            "para": para_idx,
            "run": run_idx,
            "var": mapping["var"],
            "original": original_text,
            "replaced_with": mapping["placeholder"],
        })

doc.save(OUTPUT_FILE)

print(f"\n✅ Template gerado: {OUTPUT_FILE}")
print(f"\n📋 {len(applied)} substituição(ões) aplicada(s):\n")
for item in applied:
    print(f"  [P{item['para']:03d}/R{item['run']:02d}] {{{{{item['var']}}}}} ← \"{item['original'][:60]}\"")

# ---------------------------------------------------------------------------
# GERAR JSON SCHEMA
# ---------------------------------------------------------------------------

schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Petição de Execução - Dados Variáveis do Cliente",
    "description": (
        "Schema de variáveis para preenchimento automático do template de "
        "Ação de Execução de Título Extrajudicial. Cada campo representa uma "
        "informação específica do cliente/caso que deve ser preenchida pela LLM "
        "com base nos documentos e informações fornecidos."
    ),
    "type": "object",
    "required": [],
    "properties": {}
}

# Sort by variable name for clean output
for key in sorted(VARIABLE_MAP.keys()):
    mapping = VARIABLE_MAP[key]
    var = mapping["var"]
    desc = mapping["desc"]
    schema["required"].append(var)
    schema["properties"][var] = {
        "type": "string",
        "description": desc,
        "example_placeholder": mapping["placeholder"]
    }

with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print(f"\n📄 JSON Schema gerado: {SCHEMA_FILE}")
print(f"\nVariáveis definidas ({len(schema['properties'])}):")
for var in schema["required"]:
    print(f"  • {{{{{var}}}}}")
