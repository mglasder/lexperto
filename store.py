import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()


def create_store_and_upload():
    vector_store = client.vector_stores.create(        # Create vector store
        name="BGB",
    )

    #append id to file
    with open("data/vector_store_ids.txt", "a") as f:
        f.write(f"\n{vector_store.id}")

    print(vector_store.id)


    file_batch = client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, 
        files=[open("data/BGB.pdf", "rb")]
    )

    print(file_batch.status)
    print(file_batch.file_counts)

def retrieve():
    bgb_store_id = "vs_6831657e75048191b74cd994e2232105"
    user_query = "Welche Paragraphen sind relevant für den Kaufvertrag?"

    results = client.vector_stores.search(
        vector_store_id=bgb_store_id,
        query=user_query,
    )
    for result in results:
        print(print(result.content))

def ask_assistant_with_store():
    bgb_store_id = "vs_6831657e75048191b74cd994e2232105"
    assistant_id = "asst_CeRT4S3egnpB2oTuJmxcP4UK"

    # assistant = client.beta.assistants.create(
    #     name="Rechtsrecherche Assistent",
    #     instructions="Du Bist ein Assistent, der bei der Rechtsrecherche hilft. Die bist Experte für das deutsche BGB.",
    #     model="gpt-4.1",
    #     tools=[{"type": "file_search"}],
    #     tool_resources={"file_search": {"vector_store_ids": [bgb_store_id]}}
    # )

    # assistant = client.beta.assistants.retrieve(assistant_id)
    #
    # assistant = client.beta.assistants.update(
    #     assistant_id=assistant.id,
    #     tools=[{"type": "file_search"}],
    #     tool_resources={"file_search": {"vector_store_ids": [bgb_store_id]}},
    # )

    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "Zitiere $ 453 wortwörtlich aus dem BGB.",
            }
        ]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant_id
    )

    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(f"[{index}] {cited_file.filename}")

    print(message_content.value)
    print("\ncitations:\n")
    print("\n".join(citations))


def delete_stores(ids: [str] = []):
    for id_ in ids:
        # Delete the vector store
        client.vector_stores.delete(id_)

if __name__ == "__main__":
    # create_store_and_upload()
    # retrieve()
    ask_assistant_with_store()