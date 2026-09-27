import os
import json
import requests
import datetime
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Third-party SDKs
from pygooglenews import GoogleNews
from newsapi import NewsApiClient
from google import genai
from google.genai import types

# Load environment variables securely
load_dotenv()

# Initialize API Keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Clients
try:
    newsapi_client = NewsApiClient(api_key=NEWSAPI_KEY) if NEWSAPI_KEY else None
except Exception as e:
    print(f"Failed to initialize NewsAPI: {e}")
    newsapi_client = None

try:
    # Use modern google-genai SDK
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        ai_client = None
except Exception as e:
    print(f"Failed to initialize Gemini AI: {e}")
    ai_client = None

# ---------------------------------------------------------
# FETCHERS FOR MICROSERVICES & REPOSITORIES
# ---------------------------------------------------------

def fetch_pygooglenews(query, timeframe_24h=False):
    """Fetches articles using PyGoogleNews."""
    results = []
    try:
        gn = GoogleNews(lang='en', country='US')
        search_kwargs = {}
        if timeframe_24h:
            search_kwargs['when'] = '24h'
            
        search = gn.search(query, **search_kwargs)
        for entry in search.get('entries', [])[:5]:
            results.append({
                'title': entry.get('title', ''),
                'summary': entry.get('summary', ''),
                'url': entry.get('link', ''),
                'source': entry.get('source', {}).get('title', 'Google News'),
                'published_time': entry.get('published', '')
            })
    except Exception as e:
        print(f"[PyGoogleNews] Error fetching for '{query}': {e}")
    return results

def fetch_newsapi(query, timeframe_24h=False):
    """Fetches articles using official NewsAPI Python wrapper."""
    results = []
    if not newsapi_client:
        return results
    try:
        kwargs = {'q': query, 'language': 'en', 'sort_by': 'relevancy', 'page_size': 5}
        if timeframe_24h:
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            kwargs['from_param'] = yesterday
            
        response = newsapi_client.get_everything(**kwargs)
        for article in response.get('articles', []):
            results.append({
                'title': article.get('title', ''),
                'summary': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', 'NewsAPI'),
                'published_time': article.get('publishedAt', '')
            })
    except Exception as e:
        print(f"[NewsAPI] Error fetching for '{query}': {e}")
    return results

def fetch_inshorts_cyberboysumanjay(query):
    """Fetches from Cyberboysumanjay's Inshorts API (unofficial)."""
    results = []
    # Note: Search by query isn't natively supported in most Inshorts APIs (usually category based),
    # but we simulate the typical REST request for search if the fork supports it.
    try:
        # Example common public deployment
        url = f"https://inshorts.deta.dev/news?category=all" 
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            # Filter manually by query since endpoint might not support ?q=
            query_lower = query.lower()
            for article in data:
                if query_lower in article.get('title', '').lower() or query_lower in article.get('content', '').lower():
                    results.append({
                        'title': article.get('title', ''),
                        'summary': article.get('content', ''),
                        'url': article.get('read_more_url') or article.get('url', ''),
                        'source': 'Inshorts (Cyberboysumanjay)',
                        'published_time': article.get('date', '')
                    })
    except Exception as e:
        print(f"[Inshorts-Cyberboysumanjay] Endpoint offline or error: {e}")
    return results[:3]

def fetch_inshorts_kehsihba19(query):
    """Fetches from Kehsihba19's Inshorts API fork."""
    results = []
    try:
        url = "https://inshorts-news.vercel.app/all" 
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            query_lower = query.lower()
            for article in data:
                if query_lower in article.get('title', '').lower():
                    results.append({
                        'title': article.get('title', ''),
                        'summary': article.get('content', ''),
                        'url': article.get('url', ''),
                        'source': 'Inshorts (Kehsihba19)',
                        'published_time': article.get('time', '')
                    })
    except Exception as e:
        print(f"[Inshorts-Kehsihba19] Endpoint offline or error: {e}")
    return results[:3]

def fetch_open_news(query):
    """Fetches from Open-News microservice."""
    results = []
    try:
        # Placeholder for open-news standard REST endpoint
        url = f"https://open-news-api.vercel.app/search?q={quote_plus(query)}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get('articles', [])
            for article in data[:3]:
                results.append({
                    'title': article.get('title', ''),
                    'summary': article.get('description', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', 'Open-News'),
                    'published_time': article.get('publishedAt', '')
                })
    except Exception as e:
        print(f"[Open-News] Endpoint offline or error: {e}")
    return results

# ---------------------------------------------------------
# AGGREGATION & CORE CAPABILITIES
# ---------------------------------------------------------

def deduplicate_articles(articles):
    """Removes duplicate articles based on URL and Title similarity."""
    seen_urls = set()
    seen_titles = set()
    deduped = []
    
    for article in articles:
        url = article.get('url', '').strip()
        title = article.get('title', '').strip().lower()
        
        if not url or not title:
            continue
            
        if url not in seen_urls and title not in seen_titles:
            seen_urls.add(url)
            seen_titles.add(title)
            deduped.append(article)
            
    return deduped

def get_recent_context(topic_name):
    """
    Capability 2: 24-Hour Live Context Retrieval.
    Queries all five sources for the topic, restricted to 24h where possible.
    Returns the top 5 deduplicated news items.
    """
    all_articles = []
    
    # Run fetchers concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(fetch_pygooglenews, topic_name, timeframe_24h=True),
            executor.submit(fetch_newsapi, topic_name, timeframe_24h=True),
            executor.submit(fetch_inshorts_cyberboysumanjay, topic_name),
            executor.submit(fetch_inshorts_kehsihba19, topic_name),
            executor.submit(fetch_open_news, topic_name)
        ]
        
        for future in as_completed(futures):
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
            except Exception as e:
                print(f"Executor thread raised an exception: {e}")

    # Deduplicate and sort/limit to top 5
    deduped = deduplicate_articles(all_articles)
    
    # Sort could be by date if normalized, but here we just take the first 5 highly relevant ones
    return deduped[:5]
def live_search_by_keywords(query: str) -> list:
    """
    Query live sources using *raw* query string (keywords or entities).
    Returns a flat list of article dicts.
    """
    all_articles = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(fetch_pygooglenews, query, timeframe_24h=False), # We will handle 48h inside if needed
            executor.submit(fetch_newsapi, query, timeframe_24h=False),
            executor.submit(fetch_inshorts_cyberboysumanjay, query),
            executor.submit(fetch_inshorts_kehsihba19, query),
            executor.submit(fetch_open_news, query)
        ]
        
        for future in as_completed(futures):
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
            except Exception as e:
                pass

    return deduplicate_articles(all_articles)

def verify_claim(user_claim_text):
    """
    Capability 1: Live News Verification (True/False Detection).
    Aggregates news across 5 repos, feeds to Gemini via google-genai, returns structured JSON.
    """
    # 1. Extract context using the 24-hour fetcher or general fetcher
    # Using general fetcher for claims (no 24h restriction to allow historical fact-checking)
    all_articles = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(fetch_pygooglenews, user_claim_text, timeframe_24h=False),
            executor.submit(fetch_newsapi, user_claim_text, timeframe_24h=False),
            executor.submit(fetch_inshorts_cyberboysumanjay, user_claim_text),
            executor.submit(fetch_inshorts_kehsihba19, user_claim_text),
            executor.submit(fetch_open_news, user_claim_text)
        ]
        
        for future in as_completed(futures):
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
            except Exception as e:
                pass

    deduped_articles = deduplicate_articles(all_articles)[:8] # Cap at 8 for context limit
    
    if not deduped_articles:
        return {
            "verification_status": "Unverified",
            "confidence_score": 0,
            "supporting_sources": [],
            "reasoning": "No relevant news sources could be found across any of the 5 live repositories to verify this claim."
        }

    # 2. Build the LLM Context
    context_blocks = []
    source_urls = []
    for idx, article in enumerate(deduped_articles, 1):
        context_blocks.append(f"Source {idx} ({article['source']}): {article['title']}\nSummary: {article['summary']}")
        source_urls.append(article['url'])
        
    combined_context = "\n\n".join(context_blocks)
    
    # 3. LLM Fact-Checking via google-genai
    prompt = f"""
    You are a highly analytical Senior Fact-Checking Engine. 
    Compare the following user claim against the aggregated live news context from various sources.
    
    USER CLAIM: "{user_claim_text}"
    
    LIVE NEWS CONTEXT:
    {combined_context}
    
    Analyze the evidence. Output your response strictly in the following JSON format. Do not use markdown wrappers.
    """
    
    if not ai_client:
        return {
            "verification_status": "Unverified",
            "confidence_score": 50,
            "supporting_sources": source_urls,
            "reasoning": "GEMINI_API_KEY is missing or invalid. Aggregation succeeded, but AI verification is unavailable."
        }

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "verification_status": {"type": "STRING", "enum": ["True", "False", "Unverified"]},
                        "confidence_score": {"type": "INTEGER"},
                        "reasoning": {"type": "STRING"}
                    },
                    "required": ["verification_status", "confidence_score", "reasoning"]
                }
            )
        )
        
        result = json.loads(response.text)
        result["supporting_sources"] = source_urls
        return result
        
    except Exception as e:
        print(f"LLM Verification Error: {e}")
        return {
            "verification_status": "Error",
            "confidence_score": 0,
            "supporting_sources": source_urls,
            "reasoning": f"Aggregation succeeded, but an error occurred during LLM processing: {str(e)}"
        }

# For standalone testing
if __name__ == "__main__":
    print("Testing 24h Context Fetch for 'OpenAI'...")
    context = get_recent_context("OpenAI")
    print(json.dumps(context, indent=2))
    
    print("\nTesting Verification Pipeline for 'Apple announced new iPhone 16'...")
    verification = verify_claim("Apple announced new iPhone 16")
    print(json.dumps(verification, indent=2))
