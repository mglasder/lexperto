import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
import glob

from tqdm import tqdm

load_dotenv()  # Load environment variables from .env file

client = OpenAI()

AMTSHILFE_200_50tok = "vs_683985802fb48191ace2ae894aacc329"
AMTSHILFE_800_400tok = "vs_683988e8fafc8191b005deb06ffac7b0"


def count_tokens(text: str) -> int:
    """Count the number of tokens in a given text using the GPT-4o-mini tokenizer."""
    encoder = tiktoken.encoding_for_model("gpt-4o-mini")
    return len(encoder.encode(text))


def create_vector_store(name: str) -> str:
    """Create a vector store with the given name."""
    vector_store = client.vector_stores.create(name=name)
    return vector_store.id


def upload_files_to(vector_store_id: str, from_folder: str = "urteile") -> None:
    """Upload PDF files to the vector store."""
    pdfs = glob.glob(f"{from_folder}/*.pdf")

    for pdf in tqdm(pdfs):
        with open(pdf, "rb") as file:
            file_batch = client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id,
                files=[file],
                chunking_strategy={
                    "type": "static",
                    "static": {
                        "max_chunk_size_tokens": 800,
                        "chunk_overlap_tokens": 400,
                    },
                },
            )
        print(file_batch)


def try_retrieval(store_id: str) -> None:
    query = """
    Prüfung, welchen Zeitraum das vorliegende Amtshilfeersuchen betrifft und auf welches Recht es sich stützt.
    Das vorliegende Amtshilfeersuchen betrifft den Zeitraum vom 1. Juli 2020 bis 30. Juni 2022 und stützt sich auf Art. 27 DBA CH-IT und auf Bst. ebis des ebenfalls unter SR 0.672.945.41 aufgeführten dazugehörigen Zusatzprotokolls vom 9. März 1976 (nachfolgend: Zusatzprotokoll zum DBA CH-IT).
    """

    results = client.vector_stores.search(
        max_num_results=3,
        vector_store_id=store_id,
        query=query,
    )

    for res in results.data:
        print(res.score)
        print(res.content[0].text)
        print("")
        print("")
        print("____________________________________________")


if __name__ == "__main__":
    # vs_id = create_vector_store("Amtshilfeurteile-800-400tok")
    # upload_files_to(vs_id, "urteile")

    try_retrieval(AMTSHILFE_800_400tok)
