import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import uuid

# --- CONFIGURATION ---
# Use the same Qdrant settings as your setup_rag.py
QDRANT_URL = "http://localhost:6333" # Or your Cloud URL
QDRANT_API_KEY = None # Add your key if using Cloud
COLLECTION_NAME = "resumes_54k" # A new collection for this large dataset
CSV_PATH = "data/resumes.csv" # Path to your downloaded CSV

# --- INITIALIZATION ---
print("Initializing Qdrant and Model...")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
model = SentenceTransformer('all-MiniLM-L6-v2') # 384 dimensions, fast and effective

# Create collection if it doesn't exist
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    print(f"Collection '{COLLECTION_NAME}' created.")

# --- LOAD DATA ---
print(f"Loading dataset from {CSV_PATH}...")
# The 54k dataset usually has 'Resume_str' and 'Category' columns
df = pd.read_csv(CSV_PATH)
df = df.dropna(subset=['Resume_str']) # Remove empty rows
print(f"Loaded {len(df)} resumes.")

# --- INGESTION LOOP ---
batch_size = 100 # Upload in batches to prevent timeouts
points = []

print("Starting ingestion...")
for index, row in tqdm(df.iterrows(), total=len(df)):
    text = row['Resume_str']
    category = row.get('Category', 'Uncategorized')
    
    # 1. Embed the text
    embedding = model.encode(text).tolist()
    
    # 2. Create the Point (Vector + Metadata)
    point = PointStruct(
        id=str(uuid.uuid4()), # Generate a unique ID
        vector=embedding,
        payload={
            "text": text,
            "category": category,
            "source": "54k_dataset",
            "original_id": row.get('ID', index)
        }
    )
    points.append(point)
    
    # 3. Upload Batch
    if len(points) >= batch_size:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        points = [] # Clear batch

# Upload remaining points
if points:
    client.upsert(collection_name=COLLECTION_NAME, points=points)

print("Ingestion Complete! All resumes are now in Qdrant.")
