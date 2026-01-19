import os
import requests
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

class JobSearchAgent:
    def __init__(self, gemini_api_key, qdrant_host, qdrant_api_key, collection_name="resume_knowledge_base"):
        self.gemini_key = gemini_api_key
        self.qdrant_host = qdrant_host
        self.qdrant_key = qdrant_api_key
        self.collection_name = collection_name
        self.gen_model = "gemini-2.0-flash" # Use stable flash model or 'gemini-2.0-flash-exp'
        self.embedding_model = "text-embedding-004"
        
        self.qdrant_client = self._init_qdrant()

    def _init_qdrant(self):
        try:
            client = QdrantClient(
                url=self.qdrant_host, 
                api_key=self.qdrant_key,
                prefer_grpc=False
            )
            client.get_collection(self.collection_name)
            return client
        except Exception as e:
            print(f"Agent Warning: Qdrant connection failed: {e}")
            return None

    def get_embedding(self, text):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:embedContent?key={self.gemini_key}"
        payload = {"model": f"models/{self.embedding_model}", "content": {"parts": [{"text": text}]}}
        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()['embedding']['values']
        except Exception as e:
            print(f"Embedding Error: {e}")
            return None

    def search_knowledge_base(self, query_vector, role_filter="All", k=5):
        if not self.qdrant_client: return "Knowledge Base unavailable."
        
        search_filter = None
        if role_filter != "All":
            search_filter = Filter(
                must=[FieldCondition(key="role", match=MatchValue(value=role_filter))]
            )

        try:
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=k,
                with_payload=True
            )
            docs = [f"[Role: {hit.payload.get('role', 'Unknown')}] {hit.payload.get('text', '')[:1500]}" for hit in results]
            return "\n---\n".join(docs) if docs else "No relevant resumes found."
        except Exception as e:
            return "Search failed."

    def generate_strategy(self, cv_text, role_filter="All"):
        # 1. Retrieve Context
        query_vec = self.get_embedding(cv_text)
        context_text = self.search_knowledge_base(query_vec, role_filter) if query_vec else "No context."

        # 2. Skill Report (JSON)
        json_schema = {
            "type": "OBJECT",
            "properties": {
                "predictive_score": {"type": "INTEGER"},
                "weakest_link_skill": {"type": "STRING"},
                "tech_score": {"type": "INTEGER"},
                "leader_score": {"type": "INTEGER"},
                "domain_score": {"type": "INTEGER"},
            },
            "required": ["predictive_score", "weakest_link_skill", "tech_score", "leader_score"]
        }
        
        json_prompt = f"""
        Analyze this CV against the knowledge base context.
        Context: {context_text}
        CV: {cv_text}
        """
        skill_report = self._call_gemini(json_prompt, schema=json_schema)

        # 3. Strategy (Markdown with Search)
        # CRITICAL: Prompt explicit search instructions for URLs
        md_prompt = f"""
        Role: Expert Job Consultant.
        Context: {context_text}
        User CV: {cv_text}
        
        Task: Provide a strategic job search plan.
        
        ACTION REQUIRED:
        1. SEARCH for "Top employers for [User's Role] in [User's Location]".
        2. LIST 5 Domestic Employers. For EACH, you MUST provide the specific **Careers Page URL** found in your search.
        3. SEARCH for "Top international companies sponsoring visas for [User's Role]".
        4. LIST 5 International Employers. For EACH, provide the **Careers Page URL**.
        5. Detailed Visa/Immigration strategy.
        """
        markdown_text, sources = self._call_gemini(md_prompt, use_search=True)
        
        return markdown_text, skill_report, sources

    def _call_gemini(self, prompt, schema=None, use_search=False):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gen_model}:generateContent?key={self.gemini_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {}
        }
        
        if schema:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            payload["generationConfig"]["responseSchema"] = schema
        
        # --- FIXED FOR GEMINI 2.0 ---
        if use_search:
            # Gemini 2.0 uses 'google_search', not 'google_search_retrieval'
            payload["tools"] = [{"google_search": {}}] 

        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            candidate = data.get('candidates', [{}])[0]
            
            # Text extraction
            text = candidate.get('content', {}).get('parts', [{}])[0].get('text', "")
            
            # --- FIXED PARSING FOR GEMINI 2.0 ---
            sources = []
            if use_search:
                meta = candidate.get('groundingMetadata', {})
                # Gemini 2.0 uses 'groundingChunks', NOT 'groundingAttributions'
                chunks = meta.get('groundingChunks', [])
                for chunk in chunks:
                    web = chunk.get('web', {})
                    if web.get('uri'):
                        sources.append({
                            "title": web.get('title', 'Source'), 
                            "uri": web['uri']
                        })

            if schema:
                # Sanitize JSON string (sometimes models add ```json ... ``` wrappers)
                text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            
            return text, sources

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return ({"error": str(e)} if schema else (f"Error: {e}", []))
