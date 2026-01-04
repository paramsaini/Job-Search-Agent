import pandas as pd
import time
import uuid
import os
import requests
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from tqdm import tqdm

# --- 1. CONFIGURATION (Same as setup_rag.py) ---
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")
QDRANT_HOST = os.environ.get("QDRANT_HOST", "YOUR_CLOUD_URL_HERE") # Ensure this is your Cloud URL
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
COLLECTION_NAME = 'resume_knowledge_base'
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent?key={API_KEY}"

# --- 2. DEFINE THE EMBEDDING FUNCTION (Reused) ---
def get_embedding(text):
    """Calls Gemini API to get a single embedding vector (Identical to setup_rag.py)."""
    if not API_KEY:
        raise ValueError("API Key is missing.")
        
    payload = { "model": EMBEDDING_MODEL, "content": { "parts": [{ "text": text }] } }
    
    # Retry logic for rate limits (Important for 54k items)
    for attempt in range(5):
        try:
            response = requests.post(
                EMBEDDING_API_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )
            if response.status_code == 429: # Rate limit hit
                time.sleep(5 * (attempt + 1)) # Backoff
                continue
                
            response.raise_for_status()
            return response.json()['embedding']['values']
        except Exception as e:
            time.sleep(2)
            continue
    print(f"Failed to embed text: {text[:50]}...")
    return None

# --- 3. MERGE DATA (Relational -> Single Text) ---
def load_and_merge_data():
    print("Reading CSV files...")
    # Load People
    df_people = pd.read_csv("data/01_people.csv")
    df_people = df_people[['person_id', 'name']] # Minimal columns

    # Load Skills
    print("Processing Skills...")
    df_skills = pd.read_csv("data/02_abilities.csv")
    skills_grouped = df_skills.groupby('person_id')['ability'].apply(
        lambda x: ', '.join(x.astype(str))
    ).reset_index(name='skills')

    # Load Experience
    print("Processing Experience...")
    df_exp = pd.read_csv("data/04_experience.csv")
    df_exp['role_str'] = df_exp['position_name'] + " at " + df_exp['organization_name']
    exp_grouped = df_exp.groupby('person_id')['role_str'].apply(
        lambda x: '; '.join(x.astype(str))
    ).reset_index(name='experience')

    # Merge All
    print("Merging datasets...")
    df_final = df_people.merge(skills_grouped, on='person_id', how='left')
    df_final = df_final.merge(exp_grouped, on='person_id', how='left')
    df_final.fillna("", inplace=True)
    
    return df_final

# --- 4. MAIN EXECUTION ---
if __name__ == "__main__":
    # Initialize Qdrant
    qdrant = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)
    
    # Load Data
    df = load_and_merge_data()
    print(f"Total resumes to process: {len(df)}")

    batch_size = 50 
    points = []

    # Iterate and Upload
    for index, row in tqdm(df.iterrows(), total=len(df)):
        
        # Construct the text representation
        # We simulate a document structure so the search finds it easily
        text_content = (
            f"Candidate Name: {row['name']}\n"
            f"Skills: {row['skills']}\n"
            f"Experience: {row['experience']}"
        )
        
        # Skip empty data
        if len(text_content) < 50: continue

        # Get Embedding (Gemini)
        vector = get_embedding(text_content)
        
        if vector:
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": text_content,
                    "source_file": "kaggle_54k_dataset",
                    "person_id": str(row['person_id']),
                    "role": row['name']
                }
            ))

        # Upload Batch
        if len(points) >= batch_size:
            try:
                qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
                points = [] # Clear batch
                time.sleep(0.5) # Small pause to be nice to Gemini API
            except Exception as e:
                print(f"Error uploading batch: {e}")

    # Final Batch
    if points:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        
    print("Done! All resumes added to Qdrant.")
