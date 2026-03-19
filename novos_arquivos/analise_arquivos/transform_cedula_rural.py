"""
Transforma texto grifado (highlight) em {{variaveis}} no .docx
3) (Petição) EXECUÇÃO DE CÉDULA DE PRODUTO RURAL - COM GARANTIDOR

Mantém toda a formatação original. Remove highlight após substituição.
"""
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import json

INPUT_FILE  = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/3) (Petição) EXECUÇÃO DE CÉDULA DE PRODUTO RURAL - COM GARANTIDOR.docx"
OUTPUT_FILE = "/Users/pedro/Desktop/harry_advogados/novos_arquivos/3) (Petição) EXECUÇÃO DE CÉDULA DE PRODUTO RURAL - COM GARANTIDOR - TEMPLATE.docx"
SCHEMA_FILE = "/Users/pedro/Desktop/harry_advogados/schema_cedula_produto_rural.json"

# ---------------------------------------------------------------------------
# MAPEAMENTO (para_idx, run_idx) → variável
#
# Legenda de cores:
#   yellow = dado variável simples do caso
#   cyan   = trecho condicional (dependente do tipo de garantia/garantidor)
# ---------------------------------------------------------------------------
VARIABLE_MAP = {
    # ── Parágrafo 3: cabeçalho — comarca ────────────────────────────────────
    (3, 1): {
        "var": "comarca",
        "desc": "Comarca/cidade onde o processo tramita (ex: MACHADO/MG)",
        "placeholder": "{{comarca}}",
    },

    # ── Parágrafo 19: qualificação dos executados ────────────────────────────
    (19, 6): {
        "var": "nome_devedor_principal",
        "desc": "Nome completo do devedor principal (1º executado — pessoa física que emitiu a cédula)",
        "placeholder": "{{nome_devedor_principal}}",
    },
    (19, 7): {
        # vírgula isolada no mesmo highlight — funde com o run anterior
        "var": None,  # será ignorado — vírgula já incluída no placeholder anterior
        "desc": "",
        "placeholder": ",",
    },
    (19, 8): {
        "var": "qualificacao_devedor_principal",
        "desc": (
            "Qualificação completa do devedor principal: nacionalidade, estado civil, profissão, "
            "CPF e endereço completo. "
            "Formato: ' [NACIONALIDADE], [ESTADO CIVIL], [PROFISSÃO], inscrito(a) no CPF/MF "
            "sob o n° XXX.XXX.XXX-XX, residente e domiciliado(a) na cidade de [CIDADE], "
            "à [ENDEREÇO], Bairro [BAIRRO], CEP: XXXXX-XXX e'"
        ),
        "placeholder": " {{qualificacao_devedor_principal}}",
    },
    (19, 10): {
        "var": "nome_garantidor",
        "desc": "Nome completo do garantidor hipotecante (2º executado — pessoa física que deu o imóvel em garantia)",
        "placeholder": "{{nome_garantidor}}",
    },
    (19, 11): {
        "var": "qualificacao_garantidor",
        "desc": (
            "Qualificação completa do garantidor: nacionalidade, estado civil, CPF e endereço completo. "
            "Formato: ', [NACIONALIDADE], [ESTADO CIVIL], inscrito(a) no CPF/MF "
            "sob o nº XXX.XXX.XXX-XX, residente e domiciliado(a) na cidade de [CIDADE], "
            "no lugar denominado [LOCAL], nº [Nº], Bairro [BAIRRO], CEP: XXXXX-XXX'"
        ),
        "placeholder": "{{qualificacao_garantidor}}",
    },
    (19, 13): {
        "var": "qualidade_garantidor",
        "desc": (
            "Qualidade jurídica do garantidor em maiúsculas. "
            "Exemplos: 'NA QUALIDADE DE GARANTIDORA HIPOTECANTE', "
            "'NA QUALIDADE DE GARANTIDOR HIPOTECANTE', "
            "'NA QUALIDADE DE AVALISTA'"
        ),
        "placeholder": "{{qualidade_garantidor}}",
    },

    # ── Parágrafo 25: fundamentação — tipo do título ─────────────────────────
    (25, 1): {
        "var": "tipo_titulo",
        "desc": (
            "Tipo do título executivo extrajudicial. "
            "Exemplos: 'Cédula de Produto Rural', 'Cédula de Crédito Bancário', "
            "'Cédula de Crédito Rural'"
        ),
        "placeholder": "{{tipo_titulo}}",
    },
    (25, 3): {
        "var": "texto_garantia_tipo",
        "desc": (
            "Trecho condicional que descreve o tipo de garantia do título. "
            "Se houver garantia hipotecária: 'garantida de forma hipotecária pelo(a) segundo(a) executado(a)'. "
            "Se for apenas avalista: omitir ou adaptar conforme o caso."
        ),
        "placeholder": "{{texto_garantia_tipo}}",
    },

    # ── Parágrafo 33: dados do título ────────────────────────────────────────
    (33, 1): {
        "var": "cabecalho_titulo_execucao",
        "desc": (
            "Identificação completa do título: tipo, número e data de emissão. "
            "Formato: '[TIPO DO TÍTULO] n° [NÚMERO], emitida em [DD/MM/AAAA], pelo(a) executado(a) '"
            "(ex: 'Cédula de Produto Rural n° 1578164, emitida em 01/03/2023, pelo(a) executado(a) ')"
        ),
        "placeholder": "{{cabecalho_titulo_execucao}}",
    },
    (33, 2): {
        "var": "nome_devedor_principal",  # reutiliza variável já definida
        "desc": "Nome completo do devedor principal (repetição no corpo do texto)",
        "placeholder": "{{nome_devedor_principal}}",
    },
    (33, 4): {
        "var": "texto_garantia_hipotecaria",
        "desc": (
            "Trecho condicional sobre garantia hipotecária. "
            "Se houver garantidor: 'com garantia hipotecária de '. "
            "Se não houver: deixar vazio."
        ),
        "placeholder": "{{texto_garantia_hipotecaria}}",
    },
    (33, 5): {
        "var": "nome_garantidor",  # reutiliza variável já definida
        "desc": "Nome do garantidor hipotecante (repetição no corpo do texto)",
        "placeholder": "{{nome_garantidor}}",
    },
    (33, 8): {
        "var": "data_vencimento_cedula",
        "desc": "Data de vencimento da cédula no formato DD/MM/AAAA",
        "placeholder": "{{data_vencimento_cedula}},",
    },
    (33, 10): {
        "var": "valor_original_cedula",
        "desc": (
            "Valor original da cédula em formato monetário brasileiro com extenso. "
            "Formato: 'R$ XX.XXX,XX (valor por extenso)'"
        ),
        "placeholder": "{{valor_original_cedula}}",
    },

    # ── Parágrafo 37: saldo devedor ──────────────────────────────────────────
    (37, 1): {
        "var": "valor_execucao",
        "desc": (
            "Valor total do saldo devedor executado, atualizado até a data da petição, "
            "em formato monetário com extenso. "
            "Formato: 'R$ XX.XXX,XX (valor por extenso)'"
        ),
        "placeholder": "{{valor_execucao}}",
    },

    # ── Parágrafo 47: citação ────────────────────────────────────────────────
    (47, 1): {
        "var": "valor_citacao",
        "desc": (
            "Valor a ser pago pelo devedor na citação (pode ser igual ao valor_execucao). "
            "Formato: 'R$ XX.XXX,XX (valor por extenso)'"
        ),
        "placeholder": "{{valor_citacao}}",
    },
    (47, 2): {
        # vírgula em run separado — fundida no placeholder anterior
        "var": None,
        "desc": "",
        "placeholder": ",",
    },
    (47, 4): {
        "var": "texto_limite_garantidor_citacao",
        "desc": (
            "Trecho condicional sobre responsabilidade limitada do garantidor na citação. "
            "Se houver garantidor hipotecante: 'sendo certo que o(a) executado(a) '. "
            "Se não houver, deixar vazio."
        ),
        "placeholder": "{{texto_limite_garantidor_citacao}}",
    },
    (47, 5): {
        "var": "nome_garantidor",  # reutiliza
        "desc": "Nome do garantidor (repetição no trecho de limitação de responsabilidade)",
        "placeholder": "{{nome_garantidor}}",
    },
    (47, 6): {
        "var": "texto_limite_valor_garantia",
        "desc": (
            "Trecho condicional que descreve o limite de responsabilidade do garantidor. "
            "Exemplo: ' responderá até o limite do valor da avaliação do bem dado em garantia'. "
            "Omitir se não houver garantidor real."
        ),
        "placeholder": "{{texto_limite_valor_garantia}}",
    },

    # ── Parágrafo 49: penhora ────────────────────────────────────────────────
    (49, 1): {
        "var": "texto_limite_garantidor_penhora",
        "desc": (
            "Trecho condicional que identifica o garantidor na cláusula de penhora. "
            "Exemplo: 'o(a) executado(a) '. Omitir se não houver garantidor real."
        ),
        "placeholder": "{{texto_limite_garantidor_penhora}}",
    },
    (49, 2): {
        "var": "nome_garantidor",  # reutiliza
        "desc": "Nome do garantidor (repetição na cláusula de penhora)",
        "placeholder": "{{nome_garantidor}}",
    },

    # ── Parágrafo 51: indicação de bem à penhora ────────────────────────────
    (51, 0): {
        "var": "texto_indicacao_penhora_tipo",
        "desc": (
            "Texto que descreve o tipo de garantia real indicada à penhora. "
            "Formato: 'O Exequente indica para penhora, neste ato, o seguinte bem dado em "
            "garantia contratual – [TIPO DE GARANTIA] EM '. "
            "Exemplo: '...– HIPOTECA EM ', '...– ALIENAÇÃO FIDUCIÁRIA EM '"
        ),
        "placeholder": "{{texto_indicacao_penhora_tipo}}",
    },
    (51, 1): {
        "var": "grau_garantia",
        "desc": (
            "Grau da garantia real. "
            "Exemplos: '1º GRAU:', '2º GRAU:', '1º GRAU E 2º GRAU:'"
        ),
        "placeholder": "{{grau_garantia}}",
    },

    # ── Parágrafo 53: descrição do bem ──────────────────────────────────────
    (53, 0): {
        "var": "descricao_bem_garantia",
        "desc": (
            "Descrição completa do imóvel dado em garantia: localização, área, matrícula, "
            "livro e cartório de registro. "
            "Formato: 'c.1 – [DESCRIÇÃO COMPLETA DO IMÓVEL COM MATRÍCULA E CARTÓRIO].'"
        ),
        "placeholder": "{{descricao_bem_garantia}}",
    },

    # ── Parágrafo 75: valor da causa ─────────────────────────────────────────
    (75, 1): {
        "var": "valor_causa",
        "desc": (
            "Valor atribuído à causa para efeitos processuais, em formato monetário "
            "com extenso. Formato: 'R$ XX.XXX,XX (valor por extenso).'"
        ),
        "placeholder": "{{valor_causa}}",
    },
}

# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES
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

        # Runs com var=None são vírgulas/pontuação absorvidas — só remove highlight
        replace_run_text(run, mapping["placeholder"])

        rpr = run._r.find(qn("w:rPr"))
        if rpr is not None:
            remove_highlight(rpr)

        if mapping["var"]:
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
    print(f"  [P{item['para']:03d}/R{item['run']:02d}] {{{{{item['var']}}}}} ← \"{item['original'][:70]}\"")

# ---------------------------------------------------------------------------
# GERAR JSON SCHEMA — com deduplicação de variáveis reutilizadas
# ---------------------------------------------------------------------------

seen_vars = set()
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Petição de Execução — Cédula de Produto Rural com Garantidor",
    "description": (
        "Schema de variáveis para preenchimento automático do template de "
        "Ação de Execução de Cédula de Produto Rural com garantidor hipotecante. "
        "Cada campo representa uma informação específica do caso a ser preenchida "
        "pela LLM com base nos documentos fornecidos pelo escritório."
    ),
    "type": "object",
    "required": [],
    "properties": {},
}

# Ordena chaves pelo índice de para+run para sequência lógica do documento
for key in sorted(VARIABLE_MAP.keys()):
    mapping = VARIABLE_MAP[key]
    var = mapping["var"]
    if not var or var in seen_vars:
        continue
    seen_vars.add(var)
    schema["required"].append(var)
    schema["properties"][var] = {
        "type": "string",
        "description": mapping["desc"],
        "example_placeholder": mapping["placeholder"],
    }

with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
    json.dump(schema, f, ensure_ascii=False, indent=2)

print(f"\n📄 JSON Schema gerado: {SCHEMA_FILE}")
print(f"\nVariáveis únicas ({len(schema['properties'])}):")
for var in schema["required"]:
    print(f"  • {{{{{var}}}}}")
