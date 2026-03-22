# from langchain.document_loaders import DirectoryLoader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
# from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
import os
import shutil
import tiktoken
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Load environment variables. Assumes that project contains .env file with API keys
load_dotenv()
#---- Set OpenAI API key 
# Change environment variable name from "OPENAI_API_KEY" to the name given in 
# your .env file.


DATA_PATH = os.getenv("DATA_PATH")
CHROMA_DIR = os.getenv("CHROMA_PATH")
cur_path = os.path.dirname(__file__)
DATA_PATH = os.path.join(cur_path, '..', DATA_PATH, 'megaGymDataset.csv') 
CHROMA_PATH = os.path.join(cur_path, '..', CHROMA_DIR)
def get_embeddings_endpoint():
    """Get the Azure OpenAI endpoint, removing /openai/v1 suffix if present."""
    endpoint = os.getenv("AI_ENDPOINT", "")
    if endpoint.endswith("/openai/v1"):
        endpoint = endpoint.replace("/openai/v1", "")
    return endpoint

# ==========================================
# 1. INITIALISATION DES MODÈLES
# ==========================================
embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=get_embeddings_endpoint(),
    api_key=os.getenv("AI_API_KEY"),
    model=os.getenv("AI_EMBEDDING_MODEL", "text-embedding-ada-002"),
    api_version="2024-02-01",
)
def main():
    generate_data_store()


def generate_data_store():
    documents = load_documents()
    chunks = split_text()
    save_to_chroma(chunks)


def load_documents():
    loader = TextLoader(DATA_PATH)
    documents = loader.load()
    return documents

def len_line(text):
    return len(text.split('\n'))
def split_text():
    with open(DATA_PATH,'r') as f:
        lines = f.readlines()
    full_text = [Document(page_content="\n".join(lines))]
    text_splitter = CharacterTextSplitter(
    separator="\n",  # Split by lines first
    chunk_size=1,
    chunk_overlap=0,
    length_function=len_line,
)
    encoder = tiktoken.encoding_for_model(os.getenv("AI_EMBEDDING_MODEL", "text-embedding-ada-002"))

    logger.info(f"total tokens {len(encoder.encode(full_text[0].page_content))}")
    chunks = text_splitter.split_documents(full_text)


    return chunks


def save_to_chroma(chunks):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new DB from the documents.
    db = Chroma(
        embedding_function=embeddings, persist_directory=CHROMA_PATH
    )
    max_tokens_per_batch = 2000
    encoder = tiktoken.encoding_for_model(os.getenv("AI_EMBEDDING_MODEL", "text-embedding-ada-002"))
    # Add in token-aware batches
    current_batch = []
    current_tokens = 0
        
    for chunk in chunks:
        chunk_tokens = len(encoder.encode(chunk.page_content))
            
        if current_tokens + chunk_tokens > max_tokens_per_batch and current_batch:
            db.add_documents(current_batch)
            logger.info(f"Added batch: {len(current_batch)} chunks, {current_tokens} tokens")
            current_batch = [chunk]
            current_tokens = chunk_tokens
        else:
            current_batch.append(chunk)
            current_tokens += chunk_tokens
        
    if current_batch:
        db.add_documents(current_batch)
        logger.info(f"Added final batch: {len(current_batch)} chunks, {current_tokens} tokens")
        
    db.persist()


if __name__ == "__main__":
    main()
    