"""Smoke test de ambiente: confirma que o container sobe e mostra quais
integrações estão em modo real vs. modo mock, com base nas credenciais
presentes no ambiente.
"""
from traficcagent.config import load_settings


def main() -> None:
    settings = load_settings()
    print("TraficcAgent — status do ambiente")
    print(f"  Google Ads:        {'real' if settings.has_google_ads_credentials else 'mock'}")
    print(f"  Bot do Afiliado:   {'real' if settings.has_affiliate_bot_credentials else 'mock'}")
    print(f"  LLM (conteúdo):    {'real' if settings.has_llm_credentials else 'mock'}")


if __name__ == "__main__":
    main()
