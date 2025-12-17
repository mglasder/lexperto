import os
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

"""
LangChain Chat example for Azure OpenAI private endpoint.

Required env vars:
  - AZURE_OPENAI_ENDPOINT
  - AZURE_OPENAI_API_KEY
  - AZURE_OPENAI_API_VERSION (default: 2024-12-01-preview)
  - AZURE_OPENAI_CHAT_DEPLOYMENT (your chat model deployment name)

Usage:
  export AZURE_OPENAI_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com/"
  export AZURE_OPENAI_API_KEY="<key>"
  export AZURE_OPENAI_API_VERSION="2024-12-01-preview"
  export AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o-mini"
  python -m experiments.langchain_azure_openai_chat
"""


def make_llm(
    *,
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment_name: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = 512,
) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=api_key,
        openai_api_version=api_version,
        azure_endpoint=endpoint,
        model=deployment_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def main() -> None:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")

    if not endpoint or not api_key:
        raise RuntimeError(
            "Missing Azure OpenAI configuration: set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY"
        )

    llm = make_llm(
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        deployment_name=deployment,
    )

    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="I am going to Paris, what should I see?"),
    ]

    response = llm.invoke(messages)
    print(response.content)


if __name__ == "__main__":
    main()



