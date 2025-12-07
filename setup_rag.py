import os
import glob
import requests
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from langchain_text_splitters import RecursiveCharacterTextSplitter
from docx import Document
import pypdf
import time
import uuid

# --- Setup and Configuration ---
load_dotenv()

# --- Gemini API Config ---
API_KEY = os.environ.get("GEMINI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent?key={API_KEY}"

# --- Qdrant Config ---
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "") 
COLLECTION_NAME = 'resume_knowledge_base'
EMBEDDING_DIM = 768
BATCH_SIZE = 500 # NEW: Define batch size for upsert operations

RESUMES_DIR = './resumes_data'

# Ensure the resume directory exists
if not os.path.exists(RESUMES_DIR):
    os.makedirs(RESUMES_DIR)
    print(f"Created directory: {RESUMES_DIR}. Please place your 1000 resumes inside.")
    exit()

# --- Utility Functions (extract_text_... and get_embedding remain the same) ---

def extract_text_from_pdf(filepath):
    """Uses pypdf to extract text from a PDF file stream."""
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
    except Exception as e:
        print(f"Error processing PDF {filepath}: {e}")
        return ""

def extract_text_from_docx(filepath):
    """Extracts text from a DOCX file."""
    try:
        doc = Document(filepath)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        print(f"Error processing DOCX {filepath}: {e}")
        return ""
        
def get_embedding(text):
    """Calls Gemini API to get a single embedding vector."""
    if not API_KEY:
        raise ValueError("API Key is missing for embedding generation.")
        
    payload = { "model": EMBEDDING_MODEL, "content": { "parts": [{ "text": text }] } }
    
    # Simple retry logic for stability during large dataset processing
    for attempt in range(3):
        try:
            response = requests.post(
                EMBEDDING_API_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )
            response.raise_for_status()
            return response.json()['embedding']['values']
        except requests.exceptions.RequestException as e:
            time.sleep(2 ** attempt)
            continue
    raise ConnectionError(f"Failed to get embedding after 3 attempts.")


# --- Main RAG Setup Pipeline ---
def setup_rag_pipeline():
    print("--- Starting RAG Vector Database Setup (Qdrant) ---")
    
    # 1. Initialize Qdrant Client
    try:
        qdrant = QdrantClient(
            url=QDRANT_HOST, 
            api_key=QDRANT_API_KEY,
            prefer_grpc=True
        )
        qdrant.get_collections() 
        
    except Exception as e:
        print(f"\n--- ERROR: Could not connect to Qdrant at {QDRANT_HOST}. ---")
        print(f"Check 1: Verify QDRANT_HOST in your .env file is a valid cloud URL.")
        print(f"Check 2: Ensure your network is active and the API key is correct.")
        print(f"Original error: {e}")
        return

    # Check/Create Collection (Recreates the collection to start fresh)
    try:
        qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE)
        )
        print(f"Recreated Qdrant collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"Error creating Qdrant collection. Check connection/host: {e}")
        return

    # 2. Document Processing and Chunking 
    all_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    
    files = glob.glob(os.path.join(RESUMES_DIR, '*'))
    if not files:
        print(f"ERROR: No resume files found in {RESUMES_DIR}. Cannot build database.")
        return

    print(f"Found {len(files)} files to process.")
    
    # Note: We must re-process the files since the previous run failed before the final success step.
    for i, filepath in enumerate(files):
        resume_id = os.path.basename(filepath)
        if filepath.endswith('.pdf'):
            raw_text = extract_text_from_pdf(filepath)
        elif filepath.endswith('.docx'):
            raw_text = extract_text_from_docx(filepath)
        else:
            continue
        
        if not raw_text.strip(): continue

        chunks = text_splitter.split_text(raw_text)
        
        for j, chunk in enumerate(chunks):
            try:
                vector = get_embedding(chunk)
                all_chunks.append(
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={'text': chunk, 'source_file': resume_id}
                    )
                )
            except Exception as e:
                print(f"Skipping chunk for {resume_id} due to embedding error: {e}")
                
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(files)} files.")


    # 3. Upsert (Index) Data to Qdrant (WITH BATCHING FIX)
    if all_chunks:
        total_chunks = len(all_chunks)
        print(f"\nStarting upsert (indexing) for {total_chunks} chunks in batches of {BATCH_SIZE}...")
        
        for i in range(0, total_chunks, BATCH_SIZE):
            batch = all_chunks[i:i + BATCH_SIZE]
            
            try:
                qdrant.upsert(
                    collection_name=COLLECTION_NAME,
                    points=batch,
                    wait=True
                )
                print(f"-> Successfully indexed {min(i + BATCH_SIZE, total_chunks)} / {total_chunks} chunks.")
            except Exception as e:
                print(f"\n--- FATAL ERROR: Indexing failed for batch starting at index {i}. ---")
                print(f"Original error: {e}")
                # We stop the process here if one batch fails due to a deadline issue.
                return
            
        print(f"\n--- SUCCESS! Indexed {total_chunks} total chunks in Qdrant collection: {COLLECTION_NAME}. ---")
    else:
        print("\n--- FAILURE: No chunks were successfully embedded and indexed. ---")


if __name__ == '__main__':
    setup_rag_pipeline()