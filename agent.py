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
        # Using Gemini 2.0 Flash which is fast, but we must prompt it strictly.
        self.gen_model = "gemini-2.0-flash-exp" 
        self.embedding_model = "text-embedding-004"
        
        self.qdrant_client = self._init_qdrant()

    def _init_qdrant(self):
        try:
            client = QdrantClient(
                url=self.qdrant_host, 
                api_key=self.qdrant_key,
                prefer_grpc=False
            )
            # Quick check
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
            docs = [f"[Role: {hit.payload.get('role', 'Unknown')}] {hit.payload.get('text', '')[:1000]}" for hit in results]
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
        You are a Data Analyst. Analyze this CV against the knowledge base context and output specific scores.
        Context: {context_text}
        CV: {cv_text}
        """
        skill_report = self._call_gemini(json_prompt, schema=json_schema)

        # 3. Strategy (Markdown with STRICT Search Command)
        # We use a very aggressive prompt to stop the "I will search" behavior.
        md_prompt = f"""
        You are a High-End Career Management AI. 
        
        CONTEXT FROM SIMILAR PROFILES:
        {context_text}
        
        CANDIDATE CV:
        {cv_text}
        
        ---
        
        MISSION:
        Perform a deep Google Search to find REAL, ACTIVE job market data and compile a final strategy report.
        
        MANDATORY OUTPUT FORMAT (Do not describe the plan. EXECUTE IT and OUTPUT the results):

        ### 1. 🏠 Top Domestic Employers (High Match)
        (Search for 5 top companies in the candidate's local region matching their skills)
        * **[Company Name]** - [Rationale]
            * 🔗 **Apply Here:** [Insert Direct Career Page URL found via Google Search]
        * ...(Repeat for 5 companies)

        ### 2. 🌍 International Sponsorship Targets
        (Search for 5 global companies known for visa sponsorship in this domain)
        * **[Company Name]** ([Country]) - [Visa Tier/Category]
            * 🔗 **Apply Here:** [Insert Direct Career Page URL found via Google Search]
        * ...(Repeat for 5 companies)

        ### 3. 🛂 Visa & Immigration Pathway
        * **Target Visa Class:** [Specific Visa Name, e.g., H-1B, Skilled Worker]
        * **Critical Requirement:** [Key barrier to entry]
        * **Strategy:** [One specific action to improve eligibility]

        IMPORTANT:
        - DO NOT write "I will search for...".
        - DO NOT write "Here is a plan".
        - GENERATE THE ACTUAL LISTS WITH LINKS NOW.
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
            # Explicitly configuring the tool for Gemini 2.0
            payload["tools"] = [{"google_search": {}}] 

        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            if 'candidates' not in data:
                return ("Error: API blocked response.", []) if not schema else {"error": "Blocked"}

            candidate = data['candidates'][0]
            
            # Text extraction
            text = candidate.get('content', {}).get('parts', [{}])[0].get('text', "")
            
            # Source extraction (Gemini 2.0 Logic)
            sources = []
            if use_search:
                # Check both new and old fields just in case
                meta = candidate.get('groundingMetadata', {})
                chunks = meta.get('groundingChunks', []) or meta.get('groundingAttributions', [])
                
                for chunk in chunks:
                    web = chunk.get('web', {})
                    if web.get('uri'):
                        sources.append({
                            "title": web.get('title', 'Source'), 
                            "uri": web['uri']
                        })

            if schema:
                # Clean up json markdown wrappers if present
                clean_text = text.replace("```json", "").replace("```", "").strip()
                try:
                    return json.loads(clean_text)
                except:
                    return {"error": "JSON Parse Error", "raw": text}
            
            return text, sources

        except Exception as e:
            return ({"error": str(e)} if schema else (f"Error: {e}", []))
