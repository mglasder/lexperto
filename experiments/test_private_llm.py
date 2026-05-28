import os
from openai import AzureOpenAI

endpoint = "https://foundry-lexperto-resource.cognitiveservices.azure.com/"
model_name = "gpt-4.1-mini"
deployment = "gpt-4.1-mini"

subscription_key = "CYBVPEzSazBYEvom7i1hrqBpBN7Co7uSfJzZkq3nsVADvmkrBJcQJQQJ99BIACPV0roXJ3w3AAAAACOG8mlg"
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

def main():
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "I am going to Paris, what should I see?",
            }
        ],
        max_completion_tokens=512,
        temperature=0.7,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        model=deployment,
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()