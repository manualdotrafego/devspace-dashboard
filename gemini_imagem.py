"""
Gerador de imagens usando Gemini 2.0 Flash (gratuito) via Google AI Studio.
Uso: python gemini_imagem.py
"""
import os
import base64
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def gerar_imagem(prompt: str, nome_arquivo: str = "imagem_gerada.png") -> str:
    """
    Gera uma imagem a partir de um prompt usando Gemini 2.0 Flash e salva em disco.
    Retorna o caminho do arquivo salvo.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_data = base64.b64decode(part.inline_data.data)
            with open(nome_arquivo, "wb") as f:
                f.write(image_data)
            print(f"Imagem salva em: {nome_arquivo}")
            return nome_arquivo

    raise ValueError("Nenhuma imagem foi gerada na resposta.")


if __name__ == "__main__":
    gerar_imagem(
        prompt="Um pôr do sol tropical com palmeiras e oceano azul, estilo fotorrealista",
        nome_arquivo="teste.png",
    )
