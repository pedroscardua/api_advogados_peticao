const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const rootDir = path.resolve(__dirname, '..');

test('cedula de credito bancario usa roteiro especifico de extracao', () => {
  const indexSource = fs.readFileSync(path.join(rootDir, 'index.js'), 'utf8');

  assert.match(
    indexSource,
    /celula_credito_bancario:\s*{[\s\S]*schema:\s*'schema_peticao_execucao\.json'/,
  );
  assert.match(
    indexSource,
    /celula_credito_bancario:\s*{[\s\S]*file:\s*'01_ccb_execucao_titulo_extrajudicial\.md'/,
  );
});

test('schema de CCB diferencia emitente principal de avalista', () => {
  const schema = JSON.parse(
    fs.readFileSync(
      path.join(rootDir, 'novos_arquivos', 'schemas', 'schema_peticao_execucao.json'),
      'utf8',
    ),
  );

  const nomeEmpresa = schema.properties.nome_empresa_executada.description;
  const qualificacaoEmpresa = schema.properties.qualificacao_empresa_executada.description;
  const nomeCurto = schema.properties.nome_empresa_executada_curto.description;
  const nomeAvalista = schema.properties.nome_socio_executado_avalista.description;

  assert.match(nomeEmpresa, /II - DADOS DO\(S\) EMITENTE\(S\)/);
  assert.match(nomeEmpresa, /nunca/i);
  assert.match(nomeEmpresa, /avalista/i);
  assert.match(qualificacaoEmpresa, /emitente\/devedor principal/i);
  assert.match(nomeCurto, /somente o nome/i);
  assert.match(nomeCurto, /sem qualifica/i);
  assert.match(nomeAvalista, /somente o nome/i);
  assert.match(nomeAvalista, /sem qualifica/i);
});

test('template de CCB deixa nomes e qualificacoes dos executados em negrito', () => {
  const templatePath = path.join(
    rootDir,
    'novos_arquivos',
    'templates',
    '2) (Petição) EXECUÇÃO - ASSINATURA ELETRÔNICA - TEMPLATE.docx',
  );
  const xml = execFileSync('unzip', ['-p', templatePath, 'word/document.xml'], {
    encoding: 'utf8',
  });

  for (const placeholder of [
    '{{nome_empresa_executada}},',
    '{{qualificacao_empresa_executada}} e ',
    '{{nome_socio_executado}}',
    '{{qualificacao_socio_executado}}',
  ]) {
    const escaped = placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const run = xml.match(new RegExp(`<w:r\\b(?:(?!</w:r>).)*${escaped}(?:(?!</w:r>).)*</w:r>`))?.[0];

    assert.ok(run, `${placeholder} deve existir no template`);
    assert.match(run, /<w:b(?:\s+w:val="1")?\s*\/>/, `${placeholder} deve estar em run com negrito`);
  }
});
