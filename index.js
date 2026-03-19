const express = require('express');
require('dotenv').config();
const axios = require('axios');
const { GoogleAIFileManager } = require("@google/generative-ai/server");
const path = require('path');
const fs = require('fs');
const app = express();
const port = 3000;

app.use(express.json());

app.get('/healthy', (req, res) => {
    res.status(200).json({ status: 'ok', message: 'Service is healthy' });
});

app.post('/llm/definir_tipo_de_peticao', async (req, res) => {
    try {
        const { data } = req.body;
        console.log("Reciving request /llm/definir_tipo_de_peticao")

        if (!data || !Array.isArray(data)) {
            return res.status(400).json({ error: 'Invalid input format. "data" array is required.' });
        }

        const start = Date.now();
        const geminiApiKey = process.env.GEMINI_API_KEY;
        if (!geminiApiKey) {
            return res.status(500).json({ error: 'GEMINI_API_KEY is not configured.' });
        }

        // Read the checklist markdown file as text
        const checklistPath = path.join(__dirname, 'arquivo_prompt', 'checklist', 'checklist_analise_contratual.md');
        const checklistContent = fs.readFileSync(checklistPath, 'utf-8');

        const parts = [];

        // 1. Add the checklist as text context
        parts.push({
            text: `<checklist_analise_contratual>\n${checklistContent}\n</checklist_analise_contratual>`
        });

        // 2. Add files from the request body
        data.forEach(item => {
            parts.push({
                fileData: {
                    mimeType: item.mimeType,
                    fileUri: item.fileUri
                }
            });
        });

        // 3. Add the text prompt
        parts.push({
            text: "O conteúdo dentro de <checklist_analise_contratual> é o manual de análise contratual com os tipos de contrato e seus critérios de identificação. Analise cuidadosamente os arquivos em anexo e classifique o tipo de contrato baseado nas definições do checklist. Atenção: existem tipos parecidos, diferencie com base nos critérios específicos de cada um (nomenclatura, cláusulas, garantias, documentação presente)."
        });

        const response = await axios.post(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key=${geminiApiKey}`,
            {
                contents: [
                    {
                        role: "user",
                        parts: parts
                    }
                ],
                generationConfig: {
                    responseMimeType: "application/json",
                    responseSchema: {
                        type: "object",
                        properties: {
                            type: {
                                type: "string",
                                description: "A classifcação do documento",
                                enum: [
                                    "CÉDULA DE CRÉDITO BANCÁRIO",
                                    "INSTRUMENTO PARTICULAR DE CONFISSÃO DE DÍVIDAS",
                                    "ALIENAÇÃO FIDUCIÁRIA DE VEÍCULOS E MAQUINÁRIOS",
                                    "CÉDULA RURAL",
                                    "CRÉDITO PRÉ-APROVADO",
                                    "CARTÃO DE CRÉDITO",
                                    "DESCONTO DE TÍTULOS",
                                    "DOCUMENTO NÃO VÁLIDO PARA AÇÃO JUDICIAL"
                                ]
                            }
                        },
                        required: ["type"]
                    }
                }
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );

        // Initial check for response structure
        if (response.data && response.data.candidates && response.data.candidates.length > 0) {
            const candidate = response.data.candidates[0];
            if (candidate.content && candidate.content.parts && candidate.content.parts.length > 0) {
                const textResponse = candidate.content.parts[0].text;
                try {
                    const jsonResponse = JSON.parse(textResponse);
                    return res.json(jsonResponse);
                } catch (e) {
                    console.error("Error parsing Gemini response:", textResponse);
                    return res.status(500).json({ error: 'Failed to parse JSON from Gemini response', raw: textResponse });
                }
            }
        }

        return res.status(500).json({ error: 'Unexpected response from Gemini API', raw: response.data });

    } catch (error) {
        console.error('Error processing /llm/definir_tipo_de_peticao:', error.response ? error.response.data : error.message);
        res.status(500).json({ error: 'Internal Server Error', details: error.response ? error.response.data : error.message });
    }
});

// Mapping: tipo_de_analise -> schema file + extracao_dados .md file
const TIPO_ANALISE_MAP = {
    celula_credito_bancario: {
        schema: 'schema_peticao_execucao.json',
        prompt_md: { dir: 'extracao_dados', file: '04_requisitos_modelos_peticao.md' }
    },
    confissao_divida: {
        schema: 'schema_monitoria.json',
        prompt_md: { dir: 'checklist', file: '02_instrumento_particular_confissao_dividas.md' }
    },
    alienacao_fidunciaria_veiculo: {
        schema: 'schema_busca_apreensao.json',
        prompt_md: { dir: 'extracao_dados', file: '02_ccb_busca_apreensao_veiculo.md' }
    },
    cedula_rural: {
        schema: 'schema_cedula_produto_rural.json',
        prompt_md: { dir: 'checklist', file: '04_cedula_rural.md' }
    },
    credito_pre_aprovado: {
        schema: 'schema_cobranca_app.json',
        prompt_md: { dir: 'extracao_dados', file: '03_contrato_pre_aprovado_app_cobranca.md' }
    },
    cartao_de_credito: {
        schema: 'schema_cobranca_cartao.json',
        prompt_md: { dir: 'checklist', file: '06_cartao_credito.md' }
    },
    desconto_titulos: {
        schema: 'schema_peticao_execucao.json',
        prompt_md: { dir: 'checklist', file: '07_desconto_titulos.md' }
    }
};

app.post('/llm/dados_extract', async (req, res) => {
    try {
        const { data, dados, add_doc, tipo_de_analise } = req.body;
        console.log("Reciving request /llm/dados_extract", tipo_de_analise ? `tipo_de_analise: ${tipo_de_analise}` : '');

        if (!data || !Array.isArray(data)) {
            return res.status(400).json({ error: 'Invalid input format. "data" array is required.' });
        }

        // Validate: either tipo_de_analise or dados must be provided
        if (!tipo_de_analise && (!dados || typeof dados !== 'object')) {
            return res.status(400).json({ error: 'Invalid input format. Either "tipo_de_analise" or "dados" object is required.' });
        }

        // Validate tipo_de_analise value if provided
        if (tipo_de_analise && !TIPO_ANALISE_MAP[tipo_de_analise]) {
            return res.status(400).json({
                error: `Invalid "tipo_de_analise": "${tipo_de_analise}". Valid values: ${Object.keys(TIPO_ANALISE_MAP).join(', ')}`
            });
        }

        const geminiApiKey = process.env.GEMINI_API_KEY;
        if (!geminiApiKey) {
            return res.status(500).json({ error: 'GEMINI_API_KEY is not configured.' });
        }

        const parts = [];
        let properties = {};
        let required = [];

        // Always include credivar_info_extraidas.md as reference context
        const credivarPath = path.join(__dirname, 'arquivo_prompt', 'extracao_dados', 'credivar_info_extraidas.md');
        const credivarContent = fs.readFileSync(credivarPath, 'utf-8');
        parts.push({
            text: `<referencia_geral_extracao>\n${credivarContent}\n</referencia_geral_extracao>`
        });

        if (tipo_de_analise) {
            // --- New flow: tipo_de_analise defined ---
            const config = TIPO_ANALISE_MAP[tipo_de_analise];

            // 2. Include the specific prompt .md for this tipo_de_analise
            const promptMdPath = path.join(__dirname, 'arquivo_prompt', config.prompt_md.dir, config.prompt_md.file);
            if (fs.existsSync(promptMdPath)) {
                const promptMdContent = fs.readFileSync(promptMdPath, 'utf-8');
                parts.push({
                    text: `<instrucoes_especificas_tipo>\n${promptMdContent}\n</instrucoes_especificas_tipo>`
                });
            }

            // 3. Add files from the request body
            data.forEach(item => {
                parts.push({
                    fileData: {
                        mimeType: item.mimeType,
                        fileUri: item.fileUri
                    }
                });
            });

            // 4. Add the text prompt
            parts.push({
                text: "O conteúdo em <referencia_geral_extracao> é o manual geral de referência para extração de dados de contratos. O conteúdo em <instrucoes_especificas_tipo> são as instruções específicas para este tipo de análise. Use ambos como guia para localizar e extrair as informações solicitadas dos documentos em anexo. Extraia todos os campos solicitados com precisão, seguindo os formatos e exemplos indicados no schema."
            });

            // 5. Build schema from JSON file
            const schemaPath = path.join(__dirname, 'novos_arquivos', 'schemas', config.schema);
            const schemaContent = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));

            // Convert schema properties to Gemini format (remove non-standard fields)
            for (const [key, prop] of Object.entries(schemaContent.properties)) {
                properties[key] = {
                    type: prop.type || "string",
                    description: prop.description || key
                };
            }
            required = schemaContent.required || Object.keys(schemaContent.properties);

        } else {
            // --- Legacy flow: dados provided ---

            // Add reference document if add_doc === 5
            if (add_doc === 5) {
                const fileManager = new GoogleAIFileManager(geminiApiKey);
                const filePath = path.join(__dirname, 'arquivo_prompt', '005_ALTERADO_INFORMAÇÕES EXTRAÍDAS PARA PETIÇÃO INICIAL - CREDIVAR.docx');

                const uploadResponse = await fileManager.uploadFile(filePath, {
                    mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    displayName: "005_ALTERADO_INFORMAÇÕES EXTRAÍDAS PARA PETIÇÃO INICIAL - CREDIVAR.docx",
                });

                console.log(`Uploaded reference file ${uploadResponse.file.displayName} as: ${uploadResponse.file.uri}`);

                parts.push({
                    fileData: {
                        mimeType: uploadResponse.file.mimeType,
                        fileUri: uploadResponse.file.uri
                    }
                });
            }

            // Add files from the request body
            data.forEach(item => {
                parts.push({
                    fileData: {
                        mimeType: item.mimeType,
                        fileUri: item.fileUri
                    }
                });
            });

            // Add text prompt with conditional instruction
            const textPrompt = add_doc === 5
                ? "O conteúdo em <referencia_geral_extracao> é o manual geral de referência para extração de dados. Use-o junto com o documento de referência em anexo como guia para localizar e extrair as informações solicitadas dos demais documentos anexos."
                : "O conteúdo em <referencia_geral_extracao> é o manual geral de referência para extração de dados de contratos. Use-o como guia para localizar e extrair as informações solicitadas dos documentos em anexo.";

            parts.push({
                text: textPrompt
            });

            // Dynamic schema generation from dados
            for (const [key, description] of Object.entries(dados)) {
                properties[key] = {
                    type: "string",
                    description: description
                };
                required.push(key);
            }
        }

        const response = await axios.post(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key=${geminiApiKey}`,
            {
                contents: [
                    {
                        role: "user",
                        parts: parts
                    }
                ],
                generationConfig: {
                    responseMimeType: "application/json",
                    responseSchema: {
                        type: "object",
                        properties: properties,
                        required: required
                    }
                }
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );

        // Initial check for response structure
        if (response.data && response.data.candidates && response.data.candidates.length > 0) {
            const candidate = response.data.candidates[0];
            if (candidate.content && candidate.content.parts && candidate.content.parts.length > 0) {
                const textResponse = candidate.content.parts[0].text;
                try {
                    const jsonResponse = JSON.parse(textResponse);
                    return res.json(jsonResponse);
                } catch (e) {
                    console.error("Error parsing Gemini response:", textResponse);
                    return res.status(500).json({ error: 'Failed to parse JSON from Gemini response', raw: textResponse });
                }
            }
        }

        return res.status(500).json({ error: 'Unexpected response from Gemini API', raw: response.data });

    } catch (error) {
        console.error('Error processing /llm/dados_extract:', error.response ? error.response.data : error.message);
        res.status(500).json({ error: 'Internal Server Error', details: error.response ? error.response.data : error.message });
    }
});

app.post('/llm/process_with_files', async (req, res) => {
    try {
        const { data, input, dados } = req.body;
        console.log("Receiving request /llm/process_with_files");

        if (!data || !Array.isArray(data)) {
            return res.status(400).json({ error: 'Invalid input format. "data" array is required.' });
        }

        if (!input || typeof input !== 'string') {
            return res.status(400).json({ error: 'Invalid input format. "input" string is required.' });
        }

        if (!dados || typeof dados !== 'object') {
            return res.status(400).json({ error: 'Invalid input format. "dados" object is required.' });
        }

        const geminiApiKey = process.env.GEMINI_API_KEY;
        if (!geminiApiKey) {
            return res.status(500).json({ error: 'GEMINI_API_KEY is not configured.' });
        }

        const parts = data.map(item => ({
            fileData: {
                mimeType: item.mimeType,
                fileUri: item.fileUri
            }
        }));

        parts.push({
            text: input
        });

        // Dynamic schema generation
        const properties = {};
        const required = [];

        for (const [key, description] of Object.entries(dados)) {
            properties[key] = {
                type: "string",
                description: description
            };
            required.push(key);
        }

        const response = await axios.post(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key=${geminiApiKey}`,
            {
                contents: [
                    {
                        role: "user",
                        parts: parts
                    }
                ],
                generationConfig: {
                    responseMimeType: "application/json",
                    responseSchema: {
                        type: "object",
                        properties: properties,
                        required: required
                    }
                }
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );

        // Initial check for response structure
        if (response.data && response.data.candidates && response.data.candidates.length > 0) {
            const candidate = response.data.candidates[0];
            if (candidate.content && candidate.content.parts && candidate.content.parts.length > 0) {
                const textResponse = candidate.content.parts[0].text;
                try {
                    const jsonResponse = JSON.parse(textResponse);
                    return res.json(jsonResponse);
                } catch (e) {
                    console.error("Error parsing Gemini response:", textResponse);
                    return res.status(500).json({ error: 'Failed to parse JSON from Gemini response', raw: textResponse });
                }
            }
        }

        return res.status(500).json({ error: 'Unexpected response from Gemini API', raw: response.data });

    } catch (error) {
        console.error('Error processing /llm/process_with_files:', error.response ? error.response.data : error.message);
        res.status(500).json({ error: 'Internal Server Error', details: error.response ? error.response.data : error.message });
    }
});

app.post('/llm/definir_nome', async (req, res) => {
    try {
        console.log("Reciving request /llm/definir_nome")
        const { data } = req.body;

        if (!data || !Array.isArray(data)) {
            return res.status(400).json({ error: 'Invalid input format. "data" array is required.' });
        }

        const parts = data.map(item => ({
            fileData: {
                mimeType: item.mimeType,
                fileUri: item.fileUri
            }
        }));

        parts.push({
            text: "Preciso que a partir dos documentos em anexo, determine o nome completo do cliente que aparece na maioria dos documentos. Retorne um Json com apenas uma variavel chamada name."
        });

        const geminiApiKey = process.env.GEMINI_API_KEY;
        if (!geminiApiKey) {
            return res.status(500).json({ error: 'GEMINI_API_KEY is not configured.' });
        }

        const response = await axios.post(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key=${geminiApiKey}`,
            {
                contents: [
                    {
                        role: "user",
                        parts: parts
                    }
                ],
                generationConfig: {
                    responseMimeType: "application/json",
                    responseSchema: {
                        type: "object",
                        properties: {
                            name: {
                                type: "string",
                                description: "O nome completo do cliente encontrado na maioria dos documentos"
                            }
                        },
                        required: ["name"]
                    }
                }
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );

        // Initial check for response structure
        if (response.data && response.data.candidates && response.data.candidates.length > 0) {
            const candidate = response.data.candidates[0];
            if (candidate.content && candidate.content.parts && candidate.content.parts.length > 0) {
                const textResponse = candidate.content.parts[0].text;
                try {
                    const jsonResponse = JSON.parse(textResponse);
                    return res.json(jsonResponse);
                } catch (e) {
                    console.error("Error parsing Gemini response:", textResponse);
                    return res.status(500).json({ error: 'Failed to parse JSON from Gemini response', raw: textResponse });
                }
            }
        }

        return res.status(500).json({ error: 'Unexpected response from Gemini API', raw: response.data });

    } catch (error) {
        console.error('Error processing /llm/definir_nome:', error.response ? error.response.data : error.message);
        res.status(500).json({ error: 'Internal Server Error', details: error.response ? error.response.data : error.message });
    }
});

app.post('/llm/alienacao/tem_veiculo', async (req, res) => {
    try {
        console.log("Reciving request /llm/alienacao/tem_veiculo")
        const { data } = req.body;

        if (!data || !Array.isArray(data)) {
            return res.status(400).json({ error: 'Invalid input format. "data" array is required.' });
        }

        const parts = data.map(item => ({
            fileData: {
                mimeType: item.mimeType,
                fileUri: item.fileUri
            }
        }));

        parts.push({
            text: "Preciso que a partir dos documentos em anexo, Analise os documentos em anexo e analise se a lista de bens alienados possui veículos."
        });

        const geminiApiKey = process.env.GEMINI_API_KEY;
        if (!geminiApiKey) {
            return res.status(500).json({ error: 'GEMINI_API_KEY is not configured.' });
        }

        const response = await axios.post(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key=${geminiApiKey}`,
            {
                contents: [
                    {
                        role: "user",
                        parts: parts
                    }
                ],
                generationConfig: {
                    responseMimeType: "application/json",
                    responseSchema: {
                        type: "object",
                        properties: {
                            have_vehicle: {
                                type: "boolean",
                                description: "Retorne true se o cliente tem veiculos como bens alienados"
                            }
                        },
                        required: ["have_vehicle"]
                    }
                }
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );

        // Initial check for response structure
        if (response.data && response.data.candidates && response.data.candidates.length > 0) {
            const candidate = response.data.candidates[0];
            if (candidate.content && candidate.content.parts && candidate.content.parts.length > 0) {
                const textResponse = candidate.content.parts[0].text;
                try {
                    const jsonResponse = JSON.parse(textResponse);
                    return res.json(jsonResponse);
                } catch (e) {
                    console.error("Error parsing Gemini response:", textResponse);
                    return res.status(500).json({ error: 'Failed to parse JSON from Gemini response', raw: textResponse });
                }
            }
        }

        return res.status(500).json({ error: 'Unexpected response from Gemini API', raw: response.data });

    } catch (error) {
        console.error('Error processing /llm/definir_nome:', error.response ? error.response.data : error.message);
        res.status(500).json({ error: 'Internal Server Error', details: error.response ? error.response.data : error.message });
    }
});

app.listen(port, () => {
    console.log(`API listening at http://localhost:${port}`);
});
