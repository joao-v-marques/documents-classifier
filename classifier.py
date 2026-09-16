import base64, anthropic, json
from pathlib import Path
from docx import Document

MODEL = "claude-sonet-5"

SYSTEM_PROMPT = (
    "Você analisa arquivos e decide se são documentos de identificação pessoal "
    "(RG, CPF, CNH, passaporte, certidão de nascimento/casamento, título de eleitor, "
    "carteira de trabalho, etc.) ou qualquer outro tipo de arquivo. "
    "Responda SEMPRE em JSON válido, sem nenhum texto fora do JSON, no formato exato: "
    '{"documento_pessoal": true ou false, "tipo": "<tipo identificado ou null>", '
    '"confianca": <número de 0 a 1>, "justificativa": "<explicação breve em português>"}'
)

IMAGE_MEDIA_TYPE = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

ANALYZE_INSTRUCTION = "Analise o arquivo fornecido e classifique-o conforme as instruções do sistema."

# funcao para extrair apenas o texto do docx, não tem como análisar o docx em si
def extract_docx_text(path: Path) -> str:
    document = Document(path)
    return "\n".join(p.text for p in document.paragraphs)

# funcao para montar os content blocks no formato que a API da anthropic pede
def build_content_blocks(path: Path) -> list[dict]:
    ext = path.suffix.lower()
    data = path.read_bytes()

    # caso a extensao do arquivo seja .pdf
    if ext == ".pdf":
        return [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": base64.standard_b64decode(data).decode(),
                },
            },
            {"type": "text", "text": ANALYZE_INSTRUCTION},
        ]

    # caso o arquivo seja imagem, extensões que contemplam está na IMAGE_MEDIA_TYPES
    if ext in IMAGE_MEDIA_TYPE:
        return [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": IMAGE_MEDIA_TYPE[ext],
                    "data": base64.standard_b64decode(data).decode(),
                },
            },
            {"type": "text", "text": ANALYZE_INSTRUCTION}
        ]

    # caso o arquivo seja word (.docx)
    if ext == ".docx":
        text = extract_docx_text(path)
        return [
            {
                "type": "text",
                "text": f"Conteúdo de um .txt:\n\n{text}\n\n{ANALYZE_INSTRUCTION}"
            }
        ]

    # caso o arquivo seja um txt
    if ext == ".txt":
        text = data.decode("utf-8", errors="replace")
        return [
            {
                "type": "text",
                "text": f"Conteúdo de um .txt:\n\n{text}\n\n{ANALYZE_INSTRUCTION}"
            }
        ]

    raise ValueError(f"Tipo de arquivo não suportado: {ext}")

# funcao que de fato analisa o arquivo e retorna um dicionario com as informações
def classify_file(path: Path) -> dict:
    client = anthropic.Anthropic() # lê automaticamente o ANTHROPIC_API_KEY do .env
    content = build_content_blocks(path)

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw_text = response.content[0].text
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {
            "erro": "Resposta da API não veio em JSON válido.", "resposta_bruta": raw_text
        }
    