import os
import requests
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import time
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")

load_dotenv()

@dataclass
class RAGResponse:
    answer: str
    sources: List[str]
    confidence: float
    reasoning: str

class AtlanRAGPipeline:
    def __init__(self):
        """Initialize RAG pipeline with proper vectorization"""
        print("🔄 Loading RAG models and building knowledge base...")
        
        # Initialize sentence transformer for embeddings
        try:
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Embeddings model loaded")
        except Exception as e:
            print(f"❌ Failed to load embeddings model: {e}")
            self.embedder = None
        
        # Knowledge base URLs
        self.knowledge_urls = {
            'product': ['https://docs.atlan.com/'],
            'api_sdk': ['https://developer.atlan.com/'],
            'how_to': ['https://docs.atlan.com/'],
            'sso': ['https://docs.atlan.com/'],
            'best_practices': ['https://docs.atlan.com/']
        }
        
        # Fallback documentation content
        self.fallback_docs = {
            'product': """
# Atlan Product Documentation

## Overview
Atlan is a modern data catalog that helps organizations discover, understand, and govern their data assets at scale.

## Key Features
- **Data Discovery**: Search and explore data assets across your organization
- **Automated Lineage**: Track data flow and dependencies automatically
- **Data Governance**: Implement policies and ensure compliance
- **Collaboration**: Work together on data projects with built-in social features
- **Integrations**: Connect with 100+ data sources and tools

## Getting Started
1. Connect your first data source through the Integrations panel
2. Set up automated crawling to discover assets
3. Configure governance policies and assign data stewards
4. Start exploring your data through the catalog interface

## Popular Connectors
- Snowflake: Enterprise data warehouse connector
- Databricks: Unity Catalog integration for lakehouse architecture
- Power BI: Business intelligence and reporting connector
- PostgreSQL: Relational database connector
- dbt: Data transformation workflow integration
            """,
            
            'api_sdk': """
# Atlan Developer Documentation

## SDKs and APIs

### Python SDK
```bash
pip install pyatlan
```

```python
from pyatlan import AtlanClient

# Initialize client
client = AtlanClient(
    base_url="https://tenant.atlan.com",
    api_key="your-api-key"
)

# Search assets
assets = client.asset.search(query="sales_data")

# Create custom attributes
client.typedef.create_custom_attribute(
    name="data_owner",
    display_name="Data Owner",
    type="string"
)
```

### Java SDK
Available via Maven Central. Add to your pom.xml:
```xml
<dependency>
    <groupId>com.atlan</groupId>
    <artifactId>atlan-java</artifactId>
    <version>1.0.0</version>
</dependency>
```

### REST API Endpoints
- **Assets**: `/api/meta/entity/bulk` - Bulk asset operations
- **Search**: `/api/meta/search/basic` - Search across catalog
- **Lineage**: `/api/meta/lineage/entity` - Query lineage information
- **Types**: `/api/meta/types/typedefs` - Custom type definitions

### Authentication
All API calls require API key authentication in the header:
```
Authorization: Bearer YOUR_API_KEY
```
            """,
            
            'how_to': """
# How-To Guides

## Connecting Data Sources

### Snowflake Connection
1. Navigate to Admin > Integrations > Snowflake
2. Enter connection details:
   - Account URL (e.g., https://xy12345.snowflakecomputing.com)
   - Username and Password
   - Warehouse, Database, and Schema
3. Test connection and save
4. Configure crawling schedule

### Databricks Unity Catalog
1. Go to Admin > Integrations > Databricks
2. Provide:
   - Server hostname
   - HTTP path
   - Personal access token
3. Enable Unity Catalog integration
4. Set up automated discovery

## Creating Data Lineage
1. Ensure source systems are properly connected
2. Use dbt integration for transformation lineage
3. Configure custom lineage via API if needed
4. View lineage in the asset detail page

## Setting Up Governance
1. Define data domains and assign domain leads
2. Create classification rules for sensitive data
3. Set up approval workflows for schema changes
4. Configure data quality monitoring
            """,
            
            'sso': """
# SSO Configuration Guide

## Supported Providers
- OKTA
- Azure Active Directory
- Google Workspace
- Generic SAML 2.0

## OKTA Setup
1. Create new SAML application in OKTA admin
2. Configure application with these URLs:
   - Single sign on URL: `https://your-tenant.atlan.com/api/service/saml/login`
   - Audience URI: `https://your-tenant.atlan.com`
3. Download OKTA certificate
4. In Atlan Admin panel:
   - Upload OKTA certificate
   - Configure SAML endpoint URL
   - Map user attributes (email, name, groups)
5. Test integration with a user account

## Azure AD Setup
1. Register Atlan as Enterprise Application
2. Configure SAML-based sign-on:
   - Identifier: `https://your-tenant.atlan.com`
   - Reply URL: `https://your-tenant.atlan.com/api/service/saml/login`
3. Configure claims:
   - Name ID: user.mail
   - Groups: user.assignedroles
4. Download federation metadata
5. Configure in Atlan admin panel

## Troubleshooting
- Verify certificate validity and format
- Check SAML response attributes match configuration
- Ensure users have proper group assignments
- Test with SAML tracer tools for debugging
            """,
            
            'best_practices': """
# Data Governance Best Practices

## Data Discovery Strategy
1. **Start with High-Value Assets**: Focus on business-critical datasets first
2. **Automated Discovery**: Use connectors for comprehensive asset discovery
3. **Consistent Naming**: Establish and enforce naming conventions
4. **Rich Metadata**: Add business context, descriptions, and tags

## Data Ownership and Stewardship
1. **Clear Ownership**: Assign data owners for every important asset
2. **Domain-Driven Approach**: Organize data by business domains
3. **Stewardship Programs**: Train and empower data stewards
4. **Accountability**: Regular ownership reviews and updates

## Data Quality Management
1. **Proactive Monitoring**: Set up automated data quality checks
2. **Quality Metrics**: Define and track key quality indicators
3. **Issue Resolution**: Establish clear processes for quality issues
4. **Communication**: Alert stakeholders about quality problems

## Security and Compliance
1. **Data Classification**: Implement systematic data classification
2. **Access Controls**: Use attribute-based access control (ABAC)
3. **Audit Trails**: Maintain comprehensive audit logs
4. **Privacy by Design**: Consider privacy implications in data processes

## Collaboration and Adoption
1. **Training Programs**: Educate users on data catalog benefits
2. **Champion Network**: Identify and empower data champions
3. **Feedback Loops**: Regularly collect and act on user feedback
4. **Success Metrics**: Track adoption and business value metrics
            """
        }
        
        # Initialize vector storage
        self.chunks = []
        self.chunk_metadata = []
        self.vector_index = None
        
        # Build knowledge base
        self._build_knowledge_base()
    
    def _scrape_content(self, url: str) -> str:
        """Scrape content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:8000] if len(text) > 8000 else text  # Limit content length
            
        except Exception as e:
            print(f"⚠️ Failed to scrape {url}: {e}")
            return ""
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def _build_knowledge_base(self):
        """Build vector knowledge base from documentation"""
        if self.embedder is None:
            print("❌ No embedder available, using fallback content only")
            return
        
        all_chunks = []
        all_metadata = []
        
        # Process fallback documentation
        for category, content in self.fallback_docs.items():
            chunks = self._chunk_text(content)
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadata.append({
                    'source': f'Atlan Documentation ({category})',
                    'category': category,
                    'type': 'documentation'
                })
        
        # Try to scrape additional content
        for category, urls in self.knowledge_urls.items():
            for url in urls:
                scraped_content = self._scrape_content(url)
                if scraped_content:
                    chunks = self._chunk_text(scraped_content)
                    for chunk in chunks:
                        all_chunks.append(chunk)
                        all_metadata.append({
                            'source': url,
                            'category': category,
                            'type': 'web_scraped'
                        })
                time.sleep(1)  # Rate limiting
        
        if not all_chunks:
            print("❌ No content available for knowledge base")
            return
        
        # Create embeddings
        print(f"🔄 Creating embeddings for {len(all_chunks)} chunks...")
        try:
            embeddings = self.embedder.encode(all_chunks)
            
            # Build FAISS index
            dimension = embeddings.shape[1]
            self.vector_index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            self.vector_index.add(embeddings.astype('float32'))
            
            self.chunks = all_chunks
            self.chunk_metadata = all_metadata
            
            print(f"✅ Knowledge base built with {len(all_chunks)} chunks")
            
        except Exception as e:
            print(f"❌ Failed to build knowledge base: {e}")
    
    def _retrieve_relevant_chunks(self, query: str, k: int = 3) -> List[Tuple[str, Dict]]:
        """Retrieve relevant chunks using vector similarity"""
        if self.vector_index is None or self.embedder is None:
            # Fallback to simple keyword matching
            return self._keyword_based_retrieval(query, k)
        
        try:
            # Encode query
            query_embedding = self.embedder.encode([query])
            
            # Search in FAISS index
            scores, indices = self.vector_index.search(query_embedding.astype('float32'), k)
            
            # Return chunks with metadata
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunks):  # Valid index
                    results.append((
                        self.chunks[idx],
                        {
                            'metadata': self.chunk_metadata[idx],
                            'score': float(score)
                        }
                    ))
            
            return results
            
        except Exception as e:
            print(f"❌ Vector retrieval failed: {e}")
            return self._keyword_based_retrieval(query, k)
    
    def _keyword_based_retrieval(self, query: str, k: int = 3) -> List[Tuple[str, Dict]]:
        """Fallback keyword-based retrieval"""
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for i, chunk in enumerate(self.chunks):
            chunk_words = set(chunk.lower().split())
            overlap = len(query_words & chunk_words)
            if overlap > 0:
                scored_chunks.append((
                    chunk,
                    {
                        'metadata': self.chunk_metadata[i],
                        'score': overlap / len(query_words)
                    }
                ))
        
        # Sort by score and return top k
        scored_chunks.sort(key=lambda x: x[1]['score'], reverse=True)
        return scored_chunks[:k]
    
    def should_use_rag(self, topic_tags: List[str]) -> bool:
        """Determine if RAG should be used based on topic tags"""
        rag_suitable_topics = {'How-to', 'Product', 'Best practices', 'API/SDK', 'SSO'}
        return bool(set(topic_tags) & rag_suitable_topics)
    
    def generate_response(self, query: str, topic_tags: List[str]) -> RAGResponse:
        """Generate RAG response using retrieved context"""
        if not self.should_use_rag(topic_tags):
            return self._generate_routing_message(topic_tags)
        
        # Retrieve relevant chunks
        relevant_chunks = self._retrieve_relevant_chunks(query)
        
        if not relevant_chunks:
            return RAGResponse(
                answer="I apologize, but I couldn't find relevant information to answer your question. Please check the Atlan documentation at https://docs.atlan.com/ or contact support.",
                sources=[],
                confidence=0.0,
                reasoning="No relevant content found"
            )
        
        # Generate response based on retrieved content
        context = "\\n\\n".join([chunk for chunk, _ in relevant_chunks])
        sources = list(set([chunk_info['metadata']['source'] for _, chunk_info in relevant_chunks]))
        
        # Simple response generation based on query type and context
        response = self._generate_contextual_response(query, context, topic_tags)
        
        return RAGResponse(
            answer=response,
            sources=sources,
            confidence=0.85,
            reasoning=f"Generated from {len(relevant_chunks)} relevant documentation chunks"
        )
    
    def _generate_contextual_response(self, query: str, context: str, topic_tags: List[str]) -> str:
        """Generate contextual response based on query and retrieved content"""
        query_lower = query.lower()
        
        # Connection/Setup questions
        if any(word in query_lower for word in ['connect', 'setup', 'configure', 'integration']):
            return f"""Based on the Atlan documentation, here are the key steps for setting up data source connections:

**General Connection Process:**
1. Navigate to Admin > Integrations in your Atlan workspace
2. Select the appropriate data source connector
3. Provide connection credentials and configuration details
4. Test the connection to ensure it's working properly
5. Configure automated crawling and discovery settings

**Specific Configuration:**
{self._extract_relevant_info(context, ['setup', 'configure', 'connect', 'integration'])}

**Next Steps:**
- Test the connection thoroughly before enabling automated crawling
- Set up appropriate governance policies for the new data source
- Train your team on the newly available data assets

For detailed configuration instructions specific to your data source, please refer to the full documentation."""
        
        # API/SDK questions
        elif any(word in query_lower for word in ['api', 'sdk', 'python', 'java', 'code']):
            return f"""Based on the Atlan Developer Documentation:

**Available SDKs:**
- Python SDK: `pip install pyatlan`
- Java SDK: Available via Maven Central

**Key API Operations:**
{self._extract_relevant_info(context, ['api', 'sdk', 'python', 'java', 'client'])}

**Authentication:**
All API calls require an API key. Generate your API key from the Admin panel in your Atlan workspace.

**Getting Started:**
1. Install the appropriate SDK for your language
2. Initialize the client with your tenant URL and API key
3. Start with basic operations like searching assets
4. Explore advanced features like custom attributes and bulk operations

For complete API reference and code examples, visit the Atlan Developer Hub."""
        
        # SSO questions
        elif any(word in query_lower for word in ['sso', 'authentication', 'login', 'okta', 'azure']):
            return f"""Based on the Atlan SSO Documentation:

**Supported Identity Providers:**
- OKTA
- Azure Active Directory 
- Google Workspace
- Generic SAML 2.0 providers

**Configuration Steps:**
{self._extract_relevant_info(context, ['sso', 'saml', 'okta', 'azure', 'authentication'])}

**Important Notes:**
- Ensure your identity provider certificate is valid and properly formatted
- Map user attributes correctly (email, name, groups)
- Test thoroughly with a test user before rolling out to all users

**Troubleshooting:**
- Verify SAML response format matches expectations
- Check certificate validity dates
- Ensure user group assignments are correct

For step-by-step configuration guides, refer to the SSO documentation section."""
        
        # General/Product questions
        else:
            return f"""Based on the Atlan documentation:

**Key Information:**
{self._extract_relevant_info(context, query_lower.split())}

**Atlan Core Features:**
- Data Discovery: Search and explore data assets across your organization
- Automated Lineage: Track data flow and dependencies
- Data Governance: Implement policies and ensure compliance  
- Collaboration: Work together on data projects
- Integrations: Connect with 100+ data sources and tools

**Getting Help:**
If you need more specific guidance, please refer to the complete Atlan documentation or contact our support team."""
    
    def _extract_relevant_info(self, context: str, keywords: List[str]) -> str:
        """Extract the most relevant sentences from context based on keywords"""
        sentences = context.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in keywords) and len(sentence) > 10:
                relevant_sentences.append(f"• {sentence}")
                if len(relevant_sentences) >= 5:  # Limit to top 5 relevant points
                    break
        
        return "\\n".join(relevant_sentences) if relevant_sentences else "Please refer to the documentation for detailed information."
    
    def _generate_routing_message(self, topic_tags: List[str]) -> RAGResponse:
        """Generate routing message for non-RAG topics"""
        primary_topic = topic_tags[0] if topic_tags else "General"
        
        routing_messages = {
            'Connector': f"This ticket involves data connector issues and has been routed to our Data Integration team. They specialize in troubleshooting connectivity problems and will review your case promptly.",
            'Lineage': f"This ticket relates to data lineage and has been routed to our Data Engineering team. They will help you with lineage tracking and dependency mapping questions.",
            'Glossary': f"This ticket concerns business glossary management and has been routed to our Data Governance team. They will assist you with terminology and metadata management.",
            'Sensitive data': f"This ticket involves sensitive data classification and has been routed to our Data Security team. They specialize in compliance and data privacy matters."
        }
        
        message = routing_messages.get(primary_topic, 
            f"This ticket has been classified as '{primary_topic}' and routed to the appropriate specialized team.")
        
        return RAGResponse(
            answer=message,
            sources=["Internal Routing System"],
            confidence=1.0,
            reasoning="Ticket routed to specialized team"
        )

if __name__ == "__main__":
    # Test the RAG pipeline
    print("🧪 Testing RAG pipeline...")
    
    rag = AtlanRAGPipeline()
    
    test_query = "How do I connect a Snowflake data source?"
    test_topics = ["How-to", "Connector"]
    
    if rag.should_use_rag(test_topics):
        response = rag.generate_response(test_query, test_topics)
        print(f"✅ RAG Response generated: {len(response.answer)} characters")
        print(f"Sources: {response.sources}")
    else:
        print("❌ Topic not suitable for RAG")
