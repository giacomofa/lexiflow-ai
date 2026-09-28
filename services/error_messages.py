"""
Traduz exceções técnicas (principalmente da API da OpenAI) em mensagens
amigáveis para o usuário final, em vez de expor a exceção crua na tela.
"""
from __future__ import annotations

import json
import logging

import openai

logger = logging.getLogger("lexiflow.errors")


def describe_error(exc: Exception) -> str:
    if isinstance(exc, openai.RateLimitError):
        return (
            "O serviço de IA está temporariamente sobrecarregado (limite de requisições "
            "atingido). Aguarde alguns instantes e tente novamente."
        )

    if isinstance(exc, openai.AuthenticationError):
        return (
            "Falha de autenticação com o serviço de IA (chave de API ausente ou inválida). "
            "Contate o administrador do sistema."
        )

    if isinstance(exc, openai.APITimeoutError):
        return (
            "A análise demorou mais do que o esperado e não foi concluída. Tente novamente — "
            "se o problema persistir, o documento pode ser muito longo."
        )

    if isinstance(exc, openai.APIConnectionError):
        return (
            "Não foi possível conectar ao serviço de IA. Verifique sua conexão com a internet "
            "e tente novamente."
        )

    if isinstance(exc, openai.InternalServerError):
        return "O serviço de IA está temporariamente indisponível. Tente novamente em alguns instantes."

    if isinstance(exc, openai.APIStatusError):
        return (
            f"O serviço de IA retornou um erro (código {exc.status_code}). "
            "Tente novamente; se persistir, contate o suporte."
        )

    if isinstance(exc, openai.OpenAIError):
        return "Não foi possível concluir a análise com o serviço de IA. Tente novamente."

    if isinstance(exc, json.JSONDecodeError):
        return (
            "O modelo de IA retornou uma resposta em formato inesperado. "
            "Tente processar o documento novamente."
        )

    if isinstance(exc, ValueError):
        return str(exc)

    # Qualquer outro tipo de exceção não foi previsto acima — em vez de
    # devolver a exceção crua ao usuário (que pode ser um perfil "basic" sem
    # privilégio nenhum, e a mensagem pode conter caminho de arquivo, nome de
    # tabela/coluna ou outro detalhe interno), registra o detalhe técnico no
    # log do servidor e devolve uma mensagem genérica e segura para a tela.
    logger.error("Erro não tratado ao processar documento/pergunta: %r", exc)
    return "Ocorreu um erro inesperado ao processar o documento. Tente novamente ou contate o suporte."
