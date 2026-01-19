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
        # Using Flash 1.5 as it often follows strict formatting better than the experimental 2.0
        self.gen_model = "gemini-1.5-flash" 
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
            return None

    def search_knowledge_base(self, query_vector, role_filter="All", k=5):
        if not self.qdrant_client: return "Knowledge Base unavailable."
        
        search_filter = None
        if role_filter != "All":
            search_filter = Filter(must=[FieldCondition(key="role", match=MatchValue(value=role_filter))])

        try:
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=k,
                with_payload=True
            )
            docs = [f"[Role: {hit.payload.get('role', 'Unknown')}] {hit.payload.get('text', '')[:500]}" for hit in results]
            return "\n".join(docs) if docs else "No relevant resumes found."
        except Exception:
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
            },
            "required": ["predictive_score", "weakest_link_skill", "tech_score"]
        }
        
        json_prompt = f"Analyze this CV against the context. Context: {context_text}. CV: {cv_text}"
        skill_report = self._call_gemini(json_prompt, schema=json_schema)

        # 3. Strategy (Strict Table Enforcement)
        # We explicitly forbid "chatting" and force Markdown Tables.
        md_prompt = f"""
        SYSTEM_INSTRUCTION: You are a DATA FORMATTER. You are NOT a chat assistant. 
        You DO NOT speak. You DO NOT say "Here is the plan". You ONLY output Markdown Tables.

        INPUT DATA:
        Context: {context_text}
        CV: {cv_text}
        
        TASK:
        1. Search Google for 10 LIVE domestic job openings matching this CV.
        2. Search Google for 10 LIVE international visa-sponsoring companies matching this CV.
        3. Format the data into the EXACT tables below.
        
        REQUIRED OUTPUT FORMAT (Markdown Only):

        ### 🏠 Top Domestic Employers (High Match)
        | Company Name | Job Role & Match Reason | Direct Career Page Link |
        | :--- | :--- | :--- |
        | [Insert Company] | [Insert Role] - [Why it matches] | [Insert EXACT URL found via Google Search] |
        (Repeat for 5 rows)

        ### 🌍 International Sponsorship Targets
        | Company | Country | Visa Strategy | Direct Career Page Link |
        | :--- | :--- | :--- | :--- |
        | [Insert Company] | [Country] | [Visa Tier/Type] | [Insert EXACT URL found via Google Search] |
        (Repeat for 5 rows)

        ### 🚀 Execution Strategy
        * **Action 1:** [Specific Action]
        * **Action 2:** [Specific Action]
        
        CONSTRAINT: DO NOT output any text before or after the tables. Start directly with "### 🏠".
        """
        markdown_text, sources = self._call_gemini(md_prompt, use_search=True)
        
        return markdown_text, skill_report, sources

    def _call_gemini(self, prompt, schema=None, use_search=False):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gen_model}:generateContent?key={self.gemini_key}"
        
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {}}
        
        if schema:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            payload["generationConfig"]["responseSchema"] = schema
        
        if use_search:
            # Force Google Search Tool
            payload["tools"] = [{"google_search": {}}] 

        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            candidate = data.get('candidates', [{}])[0]
            text = candidate.get('content', {}).get('parts', [{}])[0].get('text', "")
            
            # Extract Sources if available
            sources = []
            if use_search:
                meta = candidate.get('groundingMetadata', {})
                chunks = meta.get('groundingChunks', []) or meta.get('groundingAttributions', [])
                for chunk in chunks:
                    web = chunk.get('web', {})
                    if web.get('uri'):
                        sources.append({"title": web.get('title', 'Source'), "uri": web['uri']})

            if schema:
                clean_text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
            
            return text, sources

        except Exception as e:
            return ({"error": str(e)} if schema else (f"Error: {e}", []))
