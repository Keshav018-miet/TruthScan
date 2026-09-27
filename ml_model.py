from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import json
import re

class ChannelVerifier:
    def __init__(self):
        # Database of verified channels and trusted domains
        self.verified_channels = [
            {
                "id": "defence_squad",
                "name": "Defence Squad Official",
                "category": "Defense & Military News",
                "patterns": [
                    r"youtube\.com/c/defencesquad",
                    r"youtube\.com/@defencesquad",
                    r"instagram\.com/defencesquad",
                    r"twitter\.com/defence_squad_",
                    r"t\.me/dsquadofficial",
                    r"bit\.ly/defencesquadapp"
                ],
                "trust_score": 95,
                "status": "Verified Official Channel",
                "badge": "VERIFIED_OFFICIAL"
            }
        ]

        self.trusted_domains = {
            "reuters.com": ("Reuters Official", 98),
            "bbc.com": ("BBC News", 95),
            "pib.gov.in": ("Press Information Bureau (Govt of India)", 99),
            "defense.gov": ("US Dept of Defense", 98),
            "isro.gov.in": ("ISRO Official", 99),
            "drdo.gov.in": ("DRDO Official", 99)
        }

    def verify_source(self, channel_input):
        if not channel_input or not channel_input.strip():
            return {
                "provided": False,
                "channel_name": "Not Provided",
                "status": "No Channel Specified",
                "trust_score": 50,
                "badge": "UNSPECIFIED",
                "details": "No specific source link or handle was provided with this article."
            }

        cleaned_input = channel_input.strip().lower()

        # Check pre-registered verified channels
        for ch in self.verified_channels:
            for pattern in ch["patterns"]:
                if re.search(pattern, cleaned_input):
                    return {
                        "provided": True,
                        "channel_name": ch["name"],
                        "category": ch["category"],
                        "status": ch["status"],
                        "trust_score": ch["trust_score"],
                        "badge": ch["badge"],
                        "details": f"Authenticated match with official registry for {ch['name']}."
                    }

        # Check domain based trust
        for domain, (name, score) in self.trusted_domains.items():
            if domain in cleaned_input:
                return {
                    "provided": True,
                    "channel_name": name,
                    "status": "Trusted News Domain",
                    "trust_score": score,
                    "badge": "TRUSTED_DOMAIN",
                    "details": f"Source matched known trusted domain: {domain}."
                }

        # General / Unverified Channel
        return {
            "provided": True,
            "channel_name": channel_input.strip(),
            "status": "Unverified / Unknown Channel",
            "trust_score": 45,
            "badge": "UNVERIFIED",
            "details": "Channel link provided, but not found in the pre-verified official database."
        }


class FakeNewsModel:
    def __init__(self):
        self.dataset = [
            ("The earth is flat and scientists have been lying to us.", 1),
            ("New study shows that eating apples cures all forms of cancer instantly.", 1),
            ("Aliens landed in New York yesterday and nobody noticed.", 1),
            ("The government is secretly controlled by lizard people.", 1),
            ("Breaking: Water found to be wet.", 1),
            ("NASA launches new rover to Mars to study geological history.", 0),
            ("The stock market closed higher today after tech earnings were reported.", 0),
            ("A new species of frog was discovered in the Amazon rainforest.", 0),
            ("The president signed a new bill into law regarding infrastructure.", 0),
            ("Local team wins the championship game after a stunning comeback.", 0),
            ("Consuming excessive amounts of sugar is linked to health issues.", 0),
            ("Eating garlic cures COVID-19 in 24 hours.", 1),
            ("5G networks are causing the spread of viruses.", 1),
            ("Global temperatures reached record highs this summer.", 0),
            ("Drinking bleach will clean your body of all toxins.", 1)
        ]
        self.model = None
        self.verifier = ChannelVerifier()
        self.train_model()
        
        # Load spaCy for NER extraction
        import spacy
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None

    def train_model(self):
        print("Training demo Fake News ML model...")
        texts = [item[0] for item in self.dataset]
        labels = [item[1] for item in self.dataset] # 1 = Fake, 0 = Real

        self.model = make_pipeline(TfidfVectorizer(), LogisticRegression())
        self.model.fit(texts, labels)
        print("Model training complete.")
        
    def extract_keywords(self, text):
        import string
        from spacy.lang.en.stop_words import STOP_WORDS
        text_clean = text.translate(str.maketrans("", "", string.punctuation))
        tokens = [t.lower() for t in text_clean.split() if t.lower() not in STOP_WORDS]
        fallback = " ".join(tokens)
        return fallback if fallback else text[:100]

    def predict(self, text, channel_url=None):
        if not self.model:
            return {"prediction": "Error", "confidence": 0.0, "fact_check_info": "Model not loaded", "source_verification": {}}
            
        # --- ROBUST CLAIM & ENTITY EXTRACTION ---
        query = ""
        if self.nlp:
            doc = self.nlp(text)
            ents = [ent.text for ent in doc.ents if ent.label_ in {"ORG", "GPE", "PERSON", "EVENT"}]
            if len(ents) >= 2:
                query = " ".join(ents)
        
        if not query:
            query = self.extract_keywords(text)
            
        # --- MULTI-SOURCE REAL-TIME VERIFICATION PRIORITY ---
        from multi_source_verifier import live_search_by_keywords
        try:
            live_results = live_search_by_keywords(query)
        except Exception as e:
            print(f"Live search failed: {e}")
            live_results = []
            
        source_verification = self.verifier.verify_source(channel_url)
            
        if live_results:
            reputable_sources = {"times of india", "hindustan times", "the hindu", "india today", "ndtv", "indian express", "reuters", "bbc"}
            rep_hits = [r for r in live_results if any(src in r["source"].lower() for src in reputable_sources)]
            
            if rep_hits:
                return {
                    "prediction": "Verified / Likely True",
                    "confidence": 92.0,
                    "fact_check_info": f"Live reputable news confirms this event. Top match: {rep_hits[0]['title']}",
                    "source_verification": source_verification,
                    "supporting_sources": [r["url"] for r in rep_hits]
                }
            else:
                return {
                    "prediction": "Verified Breaking Event",
                    "confidence": 85.0,
                    "fact_check_info": f"Live news articles found matching the claim. Top match: {live_results[0]['title']}",
                    "source_verification": source_verification,
                    "supporting_sources": [r["url"] for r in live_results]
                }

        # --- OFFLINE ML FALLBACK & NEUTRAL CHANNEL HANDLING ---
        prediction = self.model.predict([text])[0]
        probabilities = self.model.predict_proba([text])[0]
        raw_confidence = max(probabilities) * 100
        
        text_real_prob = probabilities[0]
        
        if source_verification["badge"] in ["VERIFIED_OFFICIAL", "TRUSTED_DOMAIN"]:
            combined_real_prob = (text_real_prob * 0.6) + ((source_verification["trust_score"] / 100.0) * 0.4)
        elif source_verification["badge"] == "UNVERIFIED":
            combined_real_prob = (text_real_prob * 0.85) + ((source_verification["trust_score"] / 100.0) * 0.15)
        else:
            combined_real_prob = text_real_prob

        final_prediction = "Potentially Real" if combined_real_prob >= 0.5 else "Potentially Fake"
        final_confidence = round(max(combined_real_prob, 1 - combined_real_prob) * 100, 2)
        
        # Override for neutral/missing channel if live search found nothing
        if final_prediction == "Potentially Fake" and source_verification["status"] in ["No Channel Specified", "Unverified / Unknown Channel"]:
            final_prediction = "Unverified / Needs Further Context"
            
        fact_check = "No live news matches found. Fact-checking requires further context."
        text_lower = text.lower()
        if "covid" in text_lower or "virus" in text_lower:
            fact_check = "Medical claims should be verified with WHO or CDC guidelines."
        elif "earth is flat" in text_lower:
            fact_check = "The Earth is scientifically proven to be a sphere. See NASA."
        elif source_verification["badge"] == "VERIFIED_OFFICIAL":
            fact_check = f"Source verified via {source_verification['channel_name']}. Content is aligned with official publications."
            
        return {
            "prediction": final_prediction,
            "confidence": final_confidence,
            "fact_check_info": fact_check,
            "source_verification": source_verification,
            "supporting_sources": []
        }

# Singleton instance
nlp_model = FakeNewsModel()

