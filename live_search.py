import os
import spacy
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize models and clients
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    ai_client = None

def extract_entities(claim_text):
    """Extracts key entities from the claim to form a search query."""
    if not nlp:
        # Fallback if spacy isn't loaded
        return claim_text[:50]
        
    doc = nlp(claim_text)
    entities = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT", "DATE", "LOC"]]
    
    # If no major entities found, use the first few words or the whole claim (up to 5 words)
    if not entities:
        words = claim_text.split()
        return " ".join(words[:5])
    
    return " ".join(entities)

def search_live_news(query):
    """Uses SerpAPI to fetch top news/web URLs based on the query."""
    if not SERPAPI_API_KEY or SERPAPI_API_KEY == "your_serpapi_api_key_here":
        # Mock response for testing if no key is provided
        return ["https://example.com/mock-news"]
        
    params = {
      "engine": "google",
      "q": query,
      "tbm": "nws", # News search
      "api_key": SERPAPI_API_KEY,
      "num": 3
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        news_results = results.get("news_results", [])
        urls = [result["link"] for result in news_results[:3] if "link" in result]
        if not urls:
            # Fallback to organic results if no news results
            organic_results = results.get("organic_results", [])
            urls = [result["link"] for result in organic_results[:3] if "link" in result]
        return urls
    except Exception as e:
        print(f"SerpAPI error: {e}")
        return []

def extract_page_content(url):
    """Scrapes paragraph text from a URL."""
    # Handle mock URL
    if url == "https://example.com/mock-news":
        return "This is a mock news article stating that the claim might be true or false depending on the context. Used for testing when API keys are missing."
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        # Limit text length to avoid token limits (1500 chars per article approx 300 words)
        return text[:1500] 
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def fact_check_claim(claim):
    """Main RAG pipeline: Extracts entities, searches web, scrapes content, and prompts LLM."""
    query = extract_entities(claim)
    if not query:
        query = claim

    urls = search_live_news(query)
    
    context_texts = []
    for url in urls:
        content = extract_page_content(url)
        if content:
            context_texts.append(f"Source ({url}):\n{content}")
            
    combined_context = "\n\n".join(context_texts)
    
    if not combined_context:
        return {
            "verification_status": "Unverified",
            "confidence_score": 0,
            "supporting_sources": [],
            "reasoning": "Could not retrieve live context to verify this claim."
        }
        
    prompt = f"""
    You are an expert fact-checker. You will be provided with a claim and some live web context retrieved from recent news articles.
    
    Claim to verify: "{claim}"
    
    Live Context:
    {combined_context}
    
    Compare the claim against the live context. Determine if it is True, Fake, or Unverified. Provide a confidence score and reasoning based ONLY on the provided context.
    """
    
    if not ai_client:
        # Mock LLM response if no API key
        return {
            "verification_status": "Unverified",
            "confidence_score": 50,
            "supporting_sources": urls,
            "reasoning": "GEMINI_API_KEY is not configured in .env. Returning mock verification."
        }
        
    try:
        class VerificationResult(BaseModel):
            verification_status: str
            confidence_score: int
            reasoning: str
            
        # We can use structured outputs natively with google-genai
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "verification_status": {"type": "STRING", "enum": ["True", "Fake", "Unverified"]},
                        "confidence_score": {"type": "INTEGER"},
                        "reasoning": {"type": "STRING"}
                    },
                    "required": ["verification_status", "confidence_score", "reasoning"]
                }
            )
        )
        import json
        result = json.loads(response.text)
        result["supporting_sources"] = urls
        return result
    except Exception as e:
        print(f"LLM Error: {e}")
        return {
            "verification_status": "Error",
            "confidence_score": 0,
            "supporting_sources": urls,
            "reasoning": f"An error occurred during LLM verification: {str(e)}"
        }
