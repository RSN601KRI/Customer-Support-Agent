import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import re
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings("ignore")

@dataclass
class TicketClassification:
    topic_tags: List[str]
    sentiment: str
    priority: str
    confidence: float
    reasoning: str

class AtlanTicketClassifier:
    def __init__(self):
        """Initialize classifier with specified models"""
        print("🔄 Loading classification models...")
        
        # Initialize sentiment analysis model (cardiffnlp/twitter-roberta-base-sentiment)
        try:
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
        except Exception as e:
            print(f"⚠️ Sentiment model loading failed, using fallback: {e}")
            self.sentiment_pipeline = None
        
        # Initialize zero-shot classification model for topics
        try:
            self.zero_shot_pipeline = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
        except Exception as e:
            print(f"⚠️ Zero-shot model loading failed, using fallback: {e}")
            self.zero_shot_pipeline = None
        
        # Topic labels for zero-shot classification
        self.topic_labels = [
            "How-to questions and tutorials",
            "Product functionality and features", 
            "Data source connector issues",
            "Data lineage and dependency tracking",
            "API and SDK usage questions",
            "Single Sign-On authentication issues",
            "Business glossary and term management",
            "Best practices and recommendations",
            "Sensitive data classification and compliance"
        ]
        
        # Map model outputs to our topic tags
        self.topic_mapping = {
            "How-to questions and tutorials": "How-to",
            "Product functionality and features": "Product",
            "Data source connector issues": "Connector", 
            "Data lineage and dependency tracking": "Lineage",
            "API and SDK usage questions": "API/SDK",
            "Single Sign-On authentication issues": "SSO",
            "Business glossary and term management": "Glossary",
            "Best practices and recommendations": "Best practices",
            "Sensitive data classification and compliance": "Sensitive data"
        }
        
        print("✅ Models loaded successfully!")
    
    def classify_topic(self, text: str) -> List[str]:
        """Classify topic using zero-shot classification"""
        if self.zero_shot_pipeline is None:
            return self._fallback_topic_classification(text)
        
        try:
            result = self.zero_shot_pipeline(text, self.topic_labels)
            
            # Get top predictions with confidence > 0.3
            topics = []
            for label, score in zip(result['labels'], result['scores']):
                if score > 0.3:  # Confidence threshold
                    topics.append(self.topic_mapping.get(label, label))
                if len(topics) >= 2:  # Max 2 topics
                    break
            
            return topics if topics else ["Product"]  # Default fallback
            
        except Exception as e:
            print(f"⚠️ Topic classification failed: {e}")
            return self._fallback_topic_classification(text)
    
    def classify_sentiment(self, text: str) -> str:
        """Classify sentiment using CardiffNLP Twitter RoBERTa model"""
        if self.sentiment_pipeline is None:
            return self._fallback_sentiment_classification(text)
        
        try:
            # Truncate text if too long
            text = text[:512] if len(text) > 512 else text
            result = self.sentiment_pipeline(text)[0]
            
            # Map model output to our sentiment labels
            label_mapping = {
                'LABEL_0': 'Negative',
                'LABEL_1': 'Neutral', 
                'LABEL_2': 'Positive',
                'negative': 'Negative',
                'neutral': 'Neutral',
                'positive': 'Positive'
            }
            
            sentiment_label = label_mapping.get(result['label'].lower(), result['label'])
            
            # Further classify negative sentiments
            if sentiment_label == 'Negative':
                text_lower = text.lower()
                if any(word in text_lower for word in ['angry', 'furious', 'outraged', 'ridiculous']):
                    return 'Angry'
                elif any(word in text_lower for word in ['frustrated', 'disappointing', 'annoyed']):
                    return 'Frustrated'
                else:
                    return 'Frustrated'  # Default negative sentiment
            elif sentiment_label == 'Positive':
                if any(word in text_lower for word in ['curious', 'interested', 'wondering', 'question']):
                    return 'Curious'
                else:
                    return 'Curious'
            else:
                return 'Neutral'
                
        except Exception as e:
            print(f"⚠️ Sentiment classification failed: {e}")
            return self._fallback_sentiment_classification(text)
    
    def classify_priority(self, text: str) -> str:
        """Rule-based priority classification"""
        text_lower = text.lower()
        
        # P0 (High) - Critical/urgent keywords
        p0_keywords = [
            'urgent', 'asap', 'immediately', 'critical', 'broken', 'down', 
            'emergency', 'blocking', 'can\'t work', 'stopped working',
            'demo tomorrow', 'executive team', 'compliance'
        ]
        
        # P1 (Medium) - Important issues
        p1_keywords = [
            'issue', 'problem', 'error', 'not working', 'failed', 'failing',
            'incorrect', 'missing', 'unable', 'can\'t', 'doesn\'t work'
        ]
        
        # Check for P0 indicators
        if any(keyword in text_lower for keyword in p0_keywords):
            return 'P0 (High)'
        
        # Check for P1 indicators  
        elif any(keyword in text_lower for keyword in p1_keywords):
            return 'P1 (Medium)'
        
        # Default to P2 for questions, how-to, etc.
        else:
            return 'P2 (Low)'
    
    def _fallback_topic_classification(self, text: str) -> List[str]:
        """Fallback rule-based topic classification"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['connect', 'connection', 'connector', 'snowflake', 'databricks', 'power bi']):
            return ['Connector']
        elif any(word in text_lower for word in ['api', 'sdk', 'python', 'java', 'endpoint']):
            return ['API/SDK']
        elif any(word in text_lower for word in ['sso', 'authentication', 'login', 'okta', 'saml']):
            return ['SSO']
        elif any(word in text_lower for word in ['lineage', 'dependency', 'upstream', 'downstream']):
            return ['Lineage']
        elif any(word in text_lower for word in ['glossary', 'term', 'definition']):
            return ['Glossary']
        elif any(word in text_lower for word in ['sensitive', 'pii', 'gdpr', 'privacy', 'compliance']):
            return ['Sensitive data']
        elif any(word in text_lower for word in ['how to', 'how do', 'tutorial', 'guide', 'steps']):
            return ['How-to']
        elif any(word in text_lower for word in ['best practice', 'recommendation', 'optimize']):
            return ['Best practices']
        else:
            return ['Product']
    
    def _fallback_sentiment_classification(self, text: str) -> str:
        """Fallback rule-based sentiment classification"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['angry', 'furious', 'outraged', 'ridiculous']):
            return 'Angry'
        elif any(word in text_lower for word in ['frustrated', 'annoyed', 'disappointed']):
            return 'Frustrated'
        elif any(word in text_lower for word in ['urgent', 'asap', 'immediately', 'critical']):
            return 'Urgent'
        elif any(word in text_lower for word in ['curious', 'wondering', 'interested', 'question']):
            return 'Curious'
        else:
            return 'Neutral'
    
    def classify_ticket(self, subject: str, description: str) -> TicketClassification:
        """Classify a single ticket"""
        # Combine subject and description
        full_text = f"{subject}. {description}"
        
        # Perform classification
        topic_tags = self.classify_topic(full_text)
        sentiment = self.classify_sentiment(full_text)
        priority = self.classify_priority(full_text)
        
        # Calculate confidence based on successful model usage
        confidence = 0.9 if (self.sentiment_pipeline and self.zero_shot_pipeline) else 0.7
        
        reasoning = f"Topic: {', '.join(topic_tags)} | Sentiment: {sentiment} | Priority: {priority}"
        
        return TicketClassification(
            topic_tags=topic_tags,
            sentiment=sentiment,
            priority=priority,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def classify_multiple_tickets(self, tickets_df: pd.DataFrame) -> pd.DataFrame:
        """Classify multiple tickets from DataFrame"""
        results = []
        
        for idx, row in tickets_df.iterrows():
            print(f"🔄 Classifying ticket {idx + 1}/{len(tickets_df)}: {row['ticket_id']}")
            
            classification = self.classify_ticket(
                row['subject'], 
                row['description']
            )
            
            result_row = row.to_dict()
            result_row.update({
                'topic_tags': classification.topic_tags,
                'sentiment': classification.sentiment,
                'priority': classification.priority,
                'confidence': classification.confidence,
                'reasoning': classification.reasoning
            })
            results.append(result_row)
        
        return pd.DataFrame(results)

# Utility functions
def load_sample_tickets(file_path: str = "sample_tickets.csv") -> pd.DataFrame:
    """Load sample tickets from CSV file"""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"❌ File {file_path} not found!")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error loading tickets: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test the classifier
    print("🧪 Testing classifier...")
    
    classifier = AtlanTicketClassifier()
    
    # Test single classification
    test_subject = "Unable to connect Snowflake data source"
    test_description = "Hi, I'm trying to set up a Snowflake connection but I keep getting authentication errors."
    
    result = classifier.classify_ticket(test_subject, test_description)
    print(f"✅ Test result: {result}")
    
    # Test loading CSV
    tickets_df = load_sample_tickets()
    if not tickets_df.empty:
        print(f"✅ Loaded {len(tickets_df)} tickets from CSV")
    else:
        print("❌ Failed to load tickets")
