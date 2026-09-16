from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import json

class FakeNewsModel:
    def __init__(self):
        # A tiny hardcoded dataset for demonstration purposes.
        # In a real scenario, you'd load a large CSV (like ISOT Fake News Dataset)
        # and train it, or load a pre-trained pickle file.
        self.dataset = [
            ("The earth is flat and scientists have been lying to us.", 1),
            ("New study shows that eating apples cures all forms of cancer instantly.", 1),
            ("Aliens landed in New York yesterday and nobody noticed.", 1),
            ("The government is secretly controlled by lizard people.", 1),
            ("Breaking: Water found to be wet.", 1), # Satire/fake
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
        self.train_model()

    def train_model(self):
        print("Training demo Fake News ML model...")
        texts = [item[0] for item in self.dataset]
        labels = [item[1] for item in self.dataset] # 1 = Fake, 0 = Real

        # Pipeline: TF-IDF -> Logistic Regression
        self.model = make_pipeline(TfidfVectorizer(), LogisticRegression())
        self.model.fit(texts, labels)
        print("Model training complete.")

    def predict(self, text):
        if not self.model:
            return {"prediction": "Error", "confidence": 0.0}
            
        prediction = self.model.predict([text])[0]
        probabilities = self.model.predict_proba([text])[0]
        
        confidence = max(probabilities) * 100
        
        result_str = "Potentially Fake" if prediction == 1 else "Potentially Real"
        
        # Simple fact check info based on keywords
        fact_check = "No specific claims identified for external verification."
        text_lower = text.lower()
        if "covid" in text_lower or "virus" in text_lower:
            fact_check = "Medical claims should be verified with WHO or CDC guidelines."
        elif "earth is flat" in text_lower:
            fact_check = "The Earth is scientifically proven to be a sphere. See NASA."
            
        return {
            "prediction": result_str,
            "confidence": round(confidence, 2),
            "fact_check_info": fact_check
        }

# Singleton instance
nlp_model = FakeNewsModel()
