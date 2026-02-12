const express = require('express');
require('dotenv').config();
const axios = require('axios');
const { GoogleAIFileManager } = require("@google/generative-ai/server");
const path = require('path');
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

        const fileManager = new GoogleAIFileManager(geminiApiKey);
        const filePath = path.join(__dirname, 'arquivo_prompt', 'checklist_analise_contratual.pdf');

        // Upload the local file
        const uploadResponse = await fileManager.uploadFile(filePath, {
            mimeType: "application/pdf",
            displayName: "checklist_analise_contratual.pdf",
        });

        console.log(`Uploaded file ${uploadResponse.file.displayName} as: ${uploadResponse.file.uri}`);

        const parts = [];

        // 1. Add the uploaded local file
        parts.push({
            fileData: {
                mimeType: uploadResponse.file.mimeType,
                fileUri: uploadResponse.file.uri
            }
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
            text: "O arquivo checklist_analise_contratual.pdf contem um manual e instruções leia. Em seguida analise os outros arquivos em anexo para responder corretamente qual a classificação dos arquivos. Podendo ser: CÉDULA DE CRÉDITO BANCÁRIO; INSTRUMENTO PARTICULAR DE CONFISSÃO DE DÍVIDAS; ALIENAÇÃO FIDUCIÁRIA DE VEÍCULOS E MAQUINÁRIOS; CÉDULA RURAL; CRÉDITO PRÉ-APROVADO; CARTÃO DE CRÉDITO; DESCONTO DE TÍTULOS; DOCUMENTO NÃO VÁLIDO PARA AÇÃO JUDICIAL, defina baseado no documento de checklist e analise cuidadosamente pois temos varias opçoes parecidas"
        });

        const response = await axios.post(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiApiKey}`,
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

app.post('/llm/dados_extract', async (req, res) => {
    try {
        const { data, dados, add_doc } = req.body;
        console.log("Reciving request /llm/dados_extract");

        if (!data || !Array.isArray(data)) {
            return res.status(400).json({ error: 'Invalid input format. "data" array is required.' });
        }

        if (!dados || typeof dados !== 'object') {
            return res.status(400).json({ error: 'Invalid input format. "dados" object is required.' });
        }

        const geminiApiKey = process.env.GEMINI_API_KEY;
        if (!geminiApiKey) {
            return res.status(500).json({ error: 'GEMINI_API_KEY is not configured.' });
        }

        const parts = [];

        // Add reference document if add_doc === 5
        if (add_doc === 5) {
            const fileManager = new GoogleAIFileManager(geminiApiKey);
            const filePath = path.join(__dirname, 'arquivo_prompt', '005_ALTERADO_INFORMAÇÕES EXTRAÍDAS PARA PETIÇÃO INICIAL - CREDIVAR.docx');

            const uploadResponse = await fileManager.uploadFile(filePath, {
                mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                displayName: "005_ALTERADO_INFORMAÇÕES EXTRAÍDAS PARA PETIÇÃO INICIAL - CREDIVAR.docx",
            });

            console.log(`Uploaded reference file ${uploadResponse.file.displayName} as: ${uploadResponse.file.uri}`);

            // Add the reference document first
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
            ? "O primeiro arquivo em anexo é um mapa de referência que indica onde encontrar as informações nos outros documentos. Use-o como guia para localizar e extrair as informações solicitadas dos demais documentos anexos."
            : "Analise os documentos em anexo e extraia as informações solicitadas.";

        parts.push({
            text: textPrompt
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
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiApiKey}`,
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
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiApiKey}`,
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
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiApiKey}`,
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
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiApiKey}`,
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
