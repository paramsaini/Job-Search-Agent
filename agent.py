import os
import requests
import json
import time
from qdrant_client import QdrantClient, models
from qdrant_client.models import Filter, FieldCondition, MatchValue

class JobSearchAgent:
    def __init__(self, gemini_api_key, qdrant_host, qdrant_api_key, collection_name="resume_knowledge_base"):
        self.gemini_key = gemini_api_key
        self.qdrant_host = qdrant_host
        self.qdrant_key = qdrant_api_key
        self.collection_name = collection_name
        self.embedding_model = "text-embedding-004"
        self.gen_model = "gemini-2.0-flash-exp" # Using latest fast model
        
        # Initialize Qdrant Client
        self.qdrant_client = self._init_qdrant()

    def _init_qdrant(self):
        try:
            client = QdrantClient(
                url=self.qdrant_host,
                api_key=self.qdrant_key,
                prefer_grpc=False
            )
            # Quick connection check
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

    def search_knowledge_base(self, query_vector, role_filter="All", k=10):
        if not self.qdrant_client:
            return "Knowledge Base unavailable."

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
            
            docs = [
                f"[Role: {hit.payload.get('role', 'Unknown')}] {hit.payload.get('text', '')[:2000]}" 
                for hit in results
            ]
            return "\n---\n".join(docs) if docs else "No relevant resumes found."
        except Exception as e:
            print(f"Search Error: {e}")
            return "Search failed."

    def generate_strategy(self, cv_text, role_filter="All"):
        # 1. Retrieve Context
        query_vec = self.get_embedding(cv_text)
        context_text = "No context available."
        if query_vec:
            context_text = self.search_knowledge_base(query_vec, role_filter)

        # 2. Prepare Prompts
        json_schema = {
            "type": "OBJECT",
            "properties": {
                "predictive_score": {"type": "INTEGER"},
                "weakest_link_skill": {"type": "STRING"},
                "learning_resource_1": {"type": "STRING"},
                "learning_resource_2": {"type": "STRING"},
                "tech_score": {"type": "INTEGER"},
                "leader_score": {"type": "INTEGER"},
                "domain_score": {"type": "INTEGER"},
            },
            "required": ["predictive_score", "weakest_link_skill", "tech_score"]
        }

        # Call for JSON Report
        json_prompt = f"""
        Analyze this CV against the knowledge base context.
        Context: {context_text}
        CV: {cv_text}
        """
        skill_report = self._call_gemini(json_prompt, schema=json_schema)

        # Call for Markdown Strategy
        md_prompt = f"""
        Role: Expert Job Consultant.
        Context: {context_text}
        User CV: {cv_text}
        
        Task: Provide a strategic job search plan.
        1. List 5 Domestic Employers with URLs.
        2. List 5 International Employers with URLs.
        3. Detailed Visa/Immigration strategy for the target role.
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
        
        if use_search:
            payload["tools"] = [{"google_search": {}}]

        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            candidate = data.get('candidates', [{}])[0]
            text = candidate.get('content', {}).get('parts', [{}])[0].get('text', "")
            
            # Parse sources if available
            sources = []
            if use_search:
                meta = candidate.get('groundingMetadata', {})
                for chunk in meta.get('groundingAttributions', []):
                    web = chunk.get('web', {})
                    if web.get('uri'):
                        sources.append({"title": web.get('title', 'Source'), "uri": web['uri']})

            if schema:
                return json.loads(text)
            return text, sources

        except Exception as e:
            return ({"error": str(e)} if schema else (f"Error: {e}", []))
