import openai
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TicketClassification:
    topic_tags: List[str]
    sentiment: str
    priority: str
    confidence: float
    reasoning: str

class TicketClassifier:
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
    def classify_ticket(self, subject: str, description: str) -> TicketClassification:
        """
        Classify a support ticket using OpenAI's GPT model.
        
        Args:
            subject: Ticket subject line
            description: Ticket description/content
            
        Returns:
            TicketClassification object with classification results
        """
        
        system_prompt = """
        You are an AI assistant that classifies customer support tickets for Atlan, a data catalog and governance platform.
        
        Your task is to analyze support tickets and classify them according to these criteria:
        
        1. TOPIC TAGS (select multiple if applicable):
           - How-to: Basic usage questions and tutorials
           - Product: General product functionality and features
           - Connector: Issues with data source connectors (Snowflake, Databricks, Power BI, etc.)
           - Lineage: Data lineage and dependency tracking
           - API/SDK: API usage, SDK questions, developer tools
           - SSO: Single Sign-On and authentication issues
           - Glossary: Business glossary and term management
           - Best practices: Recommendations and best practices
           - Sensitive data: Data classification, PII detection, compliance
        
        2. SENTIMENT (choose one):
           - Frustrated: Customer expresses frustration, anger, or dissatisfaction
           - Curious: Customer is asking questions to learn or understand
           - Angry: Customer is clearly upset or demanding immediate action
           - Neutral: Professional, matter-of-fact tone
           - Urgent: Time-sensitive request without negative emotion
        
        3. PRIORITY (choose one):
           - P0 (High): Critical issues blocking work, angry customers, urgent business needs
           - P1 (Medium): Important issues that impact productivity but have workarounds
           - P2 (Low): Nice-to-have features, general questions, documentation requests
        
        Respond ONLY with valid JSON in this exact format:
        {
            "topic_tags": ["tag1", "tag2"],
            "sentiment": "sentiment_value",
            "priority": "priority_value",
            "confidence": 0.85,
            "reasoning": "Brief explanation of classification decisions"
        }
        """
        
        user_prompt = f"""
        Please classify this support ticket:
        
        Subject: {subject}
        Description: {description}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            try:
                result_dict = json.loads(result_text)
                return TicketClassification(
                    topic_tags=result_dict.get('topic_tags', []),
                    sentiment=result_dict.get('sentiment', 'Neutral'),
                    priority=result_dict.get('priority', 'P1 (Medium)'),
                    confidence=result_dict.get('confidence', 0.0),
                    reasoning=result_dict.get('reasoning', 'No reasoning provided')
                )
            except json.JSONDecodeError as e:
                # Fallback classification if JSON parsing fails
                return TicketClassification(
                    topic_tags=['Product'],
                    sentiment='Neutral',
                    priority='P1 (Medium)',
                    confidence=0.1,
                    reasoning=f'JSON parsing failed: {str(e)}'
                )
                
        except Exception as e:
            error_message = str(e)
            
            # Provide intelligent fallback based on content analysis if API fails
            fallback_topic = ['Product']
            fallback_sentiment = 'Neutral'
            fallback_priority = 'P1 (Medium)'
            fallback_reasoning = 'API quota exceeded - using rule-based classification'
            
            # Simple keyword-based classification as fallback
            combined_text = f"{subject} {description}".lower()
            
            # Topic classification
            if any(word in combined_text for word in ['connect', 'connection', 'connector', 'snowflake', 'databricks', 'power bi']):
                fallback_topic = ['Connector']
            elif any(word in combined_text for word in ['api', 'sdk', 'python', 'java', 'endpoint']):
                fallback_topic = ['API/SDK']
            elif any(word in combined_text for word in ['sso', 'authentication', 'login', 'okta', 'saml']):
                fallback_topic = ['SSO']
            elif any(word in combined_text for word in ['lineage', 'dependency', 'upstream', 'downstream']):
                fallback_topic = ['Lineage']
            elif any(word in combined_text for word in ['glossary', 'term', 'definition']):
                fallback_topic = ['Glossary']
            elif any(word in combined_text for word in ['sensitive', 'pii', 'gdpr', 'privacy', 'compliance']):
                fallback_topic = ['Sensitive data']
            elif any(word in combined_text for word in ['how to', 'how do', 'tutorial', 'guide', 'steps']):
                fallback_topic = ['How-to']
            elif any(word in combined_text for word in ['best practice', 'recommendation', 'optimize']):
                fallback_topic = ['Best practices']
            
            # Sentiment classification
            if any(word in combined_text for word in ['angry', 'furious', 'outraged', 'disgusted']):
                fallback_sentiment = 'Angry'
            elif any(word in combined_text for word in ['frustrated', 'annoyed', 'disappointed']):
                fallback_sentiment = 'Frustrated'
            elif any(word in combined_text for word in ['urgent', 'asap', 'immediately', 'critical']):
                fallback_sentiment = 'Urgent'
            elif any(word in combined_text for word in ['curious', 'wondering', 'interested', 'question']):
                fallback_sentiment = 'Curious'
            
            # Priority classification
            if any(word in combined_text for word in ['critical', 'urgent', 'blocking', 'down', 'broken', 'emergency']):
                fallback_priority = 'P0 (High)'
            elif any(word in combined_text for word in ['important', 'needed', 'issue', 'problem']):
                fallback_priority = 'P1 (Medium)'
            else:
                fallback_priority = 'P2 (Low)'
            
            return TicketClassification(
                topic_tags=fallback_topic,
                sentiment=fallback_sentiment,
                priority=fallback_priority,
                confidence=0.6,  # Moderate confidence for rule-based classification
                reasoning=fallback_reasoning
            )
    
    def classify_multiple_tickets(self, tickets: List[Dict]) -> List[Dict]:
        """
        Classify multiple tickets and return results.
        
        Args:
            tickets: List of ticket dictionaries with 'subject' and 'description'
            
        Returns:
            List of dictionaries containing original ticket data plus classification
        """
        results = []
        
        for ticket in tickets:
            classification = self.classify_ticket(
                ticket.get('subject', ''),
                ticket.get('description', '')
            )
            
            result = ticket.copy()
            result['classification'] = {
                'topic_tags': classification.topic_tags,
                'sentiment': classification.sentiment,
                'priority': classification.priority,
                'confidence': classification.confidence,
                'reasoning': classification.reasoning
            }
            results.append(result)
            
        return results

# Utility functions for the application
def load_sample_tickets(file_path: str = "sample_tickets.json") -> List[Dict]:
    """Load sample tickets from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def format_classification_display(classification: Dict) -> str:
    """Format classification results for display."""
    tags_str = ", ".join(classification['topic_tags'])
    
    return f"""
    **Topic Tags:** {tags_str}
    **Sentiment:** {classification['sentiment']}
    **Priority:** {classification['priority']}
    **Confidence:** {classification['confidence']:.2f}
    **Reasoning:** {classification['reasoning']}
    """

if __name__ == "__main__":
    # Test the classifier
    classifier = TicketClassifier()
    
    test_subject = "Unable to connect Snowflake data source"
    test_description = "Hi, I'm trying to set up a Snowflake connection but I keep getting authentication errors."
    
    result = classifier.classify_ticket(test_subject, test_description)
    print(f"Classification result: {result}")
