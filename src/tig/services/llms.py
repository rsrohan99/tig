import os

from dotenv import load_dotenv

from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.llms import LLM


SUPPORTED_PROVIDERS = [
    "openai",
    "anthropic",
    "google",
    "deepseek",
    "ollama",
    "groq",
    "openrouter",
    "chatsbp",
]

DEFAULT_PROVIDER = "google"
DEFAULT_MODEL = "gemini-2.0-flash"


def get_llm() -> tuple[LLM, str, str]:
    """Load the LLM from the environment variables or use default values. Returns a tuple of (LLM, provider, model_name)."""

    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
    provider = os.getenv("TIG_PROVIDER")
    if provider not in SUPPORTED_PROVIDERS:
        print(
            f"\n❌ Unsupported provider: {provider}. Supported providers are: {SUPPORTED_PROVIDERS}"
        )
        print(
            f"\n⚠️ Defaulting to provider: '{DEFAULT_PROVIDER}' and model: '{os.getenv('TIG_MODEL', DEFAULT_MODEL)}'\n"
        )
        return (
            GoogleGenAI(model=os.getenv("TIG_MODEL", DEFAULT_MODEL)),
            DEFAULT_PROVIDER,
            os.getenv("TIG_MODEL", DEFAULT_MODEL),
        )
    model_name = os.getenv("TIG_MODEL")
    if not model_name:
        print("\n⚠️ No model name provided. Using default for the provider.\n")

    if provider == "google":
        llm = (
            GoogleGenAI(model=model_name)
            if model_name
            else GoogleGenAI(model=DEFAULT_MODEL)
        )
        return llm, provider, llm.model

    if provider == "openai":
        from llama_index.llms.openai import OpenAI

        llm = OpenAI(model=model_name) if model_name else OpenAI(model="o4-mini")
        return llm, provider, llm.model

    if provider == "anthropic":
        from llama_index.llms.anthropic import Anthropic

        llm = (
            Anthropic(model=model_name)
            if model_name
            else Anthropic(model="claude-3-5-haiku-20241022")
        )
        return llm, provider, llm.model

    if provider == "deepseek":
        from llama_index.llms.deepseek import DeepSeek

        llm = (
            DeepSeek(model=model_name)
            if model_name
            else DeepSeek(model="deepseek-chat")
        )
        return llm, provider, llm.model

    if provider == "ollama":
        from llama_index.llms.ollama import Ollama

        llm = Ollama(model=model_name) if model_name else Ollama(model="gemma3")
        return llm, provider, llm.model

    if provider == "groq":
        from llama_index.llms.groq import Groq

        llm = (
            Groq(model=model_name)
            if model_name
            else Groq(model="meta-llama/llama-4-scout-17b-16e-instruct")
        )
        return llm, provider, llm.model

    if provider == "openrouter":
        from llama_index.llms.openrouter import OpenRouter

        llm = (
            OpenRouter(model=model_name)
            if model_name
            else OpenRouter(model="google/gemini-2.0-flash-001")
        )
        return llm, provider, llm.model

    if provider == "chatsbp":
        from llama_index.llms.openai import OpenAI
        api_key =   os.getenv("CHATSBP_API_KEY", "")
        api_base =   os.getenv("CHATSBP_API_BASE", "https://litellm.sbp.ai")

        # # Get the model name from environment variable or use default
        if not model_name:
            model_name =  "azure/gpt-4o"

        llm = OpenAI(model=model_name.split("/")[-1],
                    api_key=api_key,
                    api_base=api_base,
                    additional_kwargs={"model": "azure/gpt-4o"})
        return llm, provider, llm.model

    else:
        llm = (
            GoogleGenAI(model=model_name)
            if model_name
            else GoogleGenAI(model=DEFAULT_MODEL)
        )
        return llm, provider, llm.model
