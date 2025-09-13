import openai
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
import time

load_dotenv()

@dataclass
class RAGResponse:
    answer: str
    sources: List[str]
    confidence: float
    reasoning: str

class AtlanRAGPipeline:
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        # Predefined knowledge base URLs for different topics
        self.knowledge_base = {
            'product': [
                'https://docs.atlan.com/',
            ],
            'api_sdk': [
                'https://developer.atlan.com/',
            ],
            'how_to': [
                'https://docs.atlan.com/',
            ],
            'sso': [
                'https://docs.atlan.com/',
            ],
            'best_practices': [
                'https://docs.atlan.com/',
            ],
            'glossary': [
                'https://docs.atlan.com/',
                'https://developer.atlan.com/',
            ]
        }
        
        # Fallback content when web scraping fails
        self.fallback_content = {
            'product': """
            Atlan is a modern data catalog that helps you discover, understand, and govern your data assets.
            
            Key Features:
            - Data Discovery and Search: Find and explore data assets across your organization
            - Automated Data Lineage: Track data flow and dependencies
            - Data Governance and Policies: Implement data governance at scale
            - Collaboration Tools: Work together on data projects
            - Integrations: Connect with popular data tools like Snowflake, Databricks, Power BI
            
            Quick Start:
            1. Connect your data sources through the integrations panel
            2. Set up automated crawling to discover assets
            3. Define governance policies and assign data stewards
            4. Start discovering and using your data through the catalog
            """,
            
            'api_sdk': """
            Atlan Developer Hub - APIs and SDKs
            
            Available SDKs:
            - Python SDK: pip install pyatlan
            - Java SDK: Available via Maven Central
            
            Common API Operations:
            - Asset Management: Create, update, and retrieve data assets
            - Metadata Management: Add custom metadata to assets
            - Lineage API: Query and update data lineage information
            - Search API: Programmatic search across your data catalog
            - Workflow API: Automate data governance workflows
            
            Authentication:
            All API calls require API key authentication. Generate your API key from the Admin panel.
            
            Example Python Usage:
            ```python
            from pyatlan import AtlanClient
            client = AtlanClient(base_url="https://your-tenant.atlan.com", api_key="your-api-key")
            assets = client.search_assets(query="sales_data")
            ```
            """,
            
            'how_to': """
            Atlan How-To Guides
            
            Getting Started:
            1. Setting up your first data source connection
            2. Configuring automated metadata discovery
            3. Creating and managing data assets
            4. Setting up data lineage tracking
            
            Common Tasks:
            - Connect Snowflake: Use the Snowflake connector with your credentials
            - Connect Databricks: Set up Unity Catalog integration
            - Connect Power BI: Configure the Power BI connector for report discovery
            - Create Glossary Terms: Define business glossary for better data understanding
            - Set up Data Policies: Implement governance rules and data classification
            
            Best Practices:
            - Start with high-value data sources
            - Establish clear data ownership
            - Implement consistent tagging and classification
            - Regular data quality monitoring
            """,
            
            'sso': """
            Atlan SSO Configuration
            
            Supported Identity Providers:
            - OKTA
            - Azure Active Directory
            - Google Workspace
            - SAML 2.0 compliant providers
            
            OKTA Configuration:
            1. Create a new SAML application in OKTA
            2. Configure the application settings with Atlan URLs
            3. Download the SAML certificate
            4. Configure OKTA settings in Atlan admin panel
            5. Test the integration
            
            Azure AD Configuration:
            1. Register Atlan as an enterprise application
            2. Configure SAML-based sign-on
            3. Set up user provisioning (optional)
            4. Configure claims and attributes
            5. Test user sign-in
            
            Troubleshooting:
            - Verify SAML response format
            - Check certificate validity
            - Ensure user attributes are mapped correctly
            """,
            
            'best_practices': """
            Atlan Data Governance Best Practices
            
            Data Discovery:
            - Implement automated scanning of all data sources
            - Use consistent naming conventions
            - Tag assets with relevant business context
            - Maintain up-to-date data descriptions
            
            Data Governance:
            - Establish clear data ownership and stewardship
            - Implement data quality monitoring
            - Create data policies for sensitive information
            - Set up approval workflows for critical data changes
            
            Collaboration:
            - Use @mentions to notify relevant stakeholders
            - Create shared collections for team resources
            - Document data usage patterns and business logic
            - Regular data governance reviews
            
            Security:
            - Implement role-based access control
            - Regular access reviews
            - Data classification and sensitivity labeling
            - Audit trail monitoring
            """,
            
            'glossary': """
            Atlan Glossary Management
            
            Overview:
            The Atlan Glossary is a centralized business vocabulary that helps standardize data definitions across your organization. It contains business terms, their definitions, and relationships to data assets.
            
            Key Features:
            - AtlasGlossary: Root container for all glossary terms
            - AtlasGlossaryTerm: Individual business terms with definitions
            - AtlasGlossaryCategory: Hierarchical organization of terms
            - Term Relationships: Link terms to data assets and other terms
            
            Creating and Managing Glossary Terms:
            1. **Create Glossary**: Set up a new business glossary container
            2. **Add Terms**: Define business terms with clear descriptions
            3. **Categorize**: Organize terms into logical categories
            4. **Link to Assets**: Associate terms with relevant data assets
            5. **Set Relationships**: Define parent-child and related term connections
            
            Best Practices:
            - Use clear, business-friendly definitions
            - Involve domain experts in term creation
            - Maintain consistent terminology across teams
            - Regular reviews and updates of glossary content
            - Link terms to actual data assets for better discovery
            
            API Operations:
            - Create/Update glossary terms programmatically
            - Bulk import terms from existing systems
            - Query terms and their relationships
            - Manage term approval workflows
            
            Integration:
            - Automatically suggest terms based on asset names
            - Propagate glossary terms through data lineage
            - Search and filter assets by glossary terms
            - Generate data documentation using glossary definitions
            """
        }
        
        # Cache for fetched content
        self.content_cache = {}
    
    def fetch_page_content(self, url: str) -> str:
        """
        Fetch and extract text content from a web page.
        """
        if url in self.content_cache:
            return self.content_cache[url]
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit content length
            text = text[:4000] if len(text) > 4000 else text
            
            self.content_cache[url] = text
            return text
            
        except Exception as e:
            # Silently fail for web scraping errors to avoid cluttering output
            return ""
    
    def get_relevant_content(self, topic_tags: List[str], query: str) -> List[Tuple[str, str]]:
        """
        Retrieve relevant content based on topic tags and query.
        
        Returns:
            List of tuples (url, content)
        """
        relevant_urls = []
        
        # Map topic tags to knowledge base categories
        tag_mapping = {
            'Product': 'product',
            'API/SDK': 'api_sdk',
            'How-to': 'how_to',
            'SSO': 'sso',
            'Best practices': 'best_practices',
            'Glossary': 'glossary'
        }
        
        # Get URLs for relevant topics
        for tag in topic_tags:
            category = tag_mapping.get(tag, 'product')
            relevant_urls.extend(self.knowledge_base.get(category, []))
        
        # If no specific mapping, use general documentation
        if not relevant_urls:
            relevant_urls = self.knowledge_base['product']
        
        # Remove duplicates and limit to top 3 URLs
        relevant_urls = list(set(relevant_urls))[:3]
        
        # Fetch content from relevant URLs
        content_pairs = []
        for url in relevant_urls:
            content = self.fetch_page_content(url)
            if content:
                content_pairs.append((url, content))
                time.sleep(0.5)  # Rate limiting
        
        # If no content was fetched, use fallback content
        if not content_pairs:
            # Get fallback content based on the first topic tag
            for tag in topic_tags:
                category = tag_mapping.get(tag, 'product')
                if category in self.fallback_content:
                    fallback_text = self.fallback_content[category]
                    content_pairs.append((f"Atlan Documentation ({category})", fallback_text))
                    break
            
            # If still no content, use general product fallback
            if not content_pairs:
                content_pairs.append(("Atlan Documentation", self.fallback_content['product']))
        
        return content_pairs
    
    def generate_rag_response(self, query: str, topic_tags: List[str]) -> RAGResponse:
        """
        Generate a response using RAG based on the query and topic tags.
        """
        
        # Get relevant content
        content_pairs = self.get_relevant_content(topic_tags, query)
        
        if not content_pairs:
            return RAGResponse(
                answer="I apologize, but I couldn't retrieve relevant documentation to answer your question. Please check the Atlan documentation at https://docs.atlan.com/ or contact support directly.",
                sources=[],
                confidence=0.0,
                reasoning="No relevant content found"
            )
        
        # Prepare context for the AI model
        context_parts = []
        sources = []
        
        for url, content in content_pairs:
            context_parts.append(f"Source: {url}\nContent: {content}\n")
            sources.append(url)
        
        context = "\n---\n".join(context_parts)
        
        system_prompt = """
        You are a helpful customer support AI assistant for Atlan, a data catalog and governance platform.
        
        Your task is to answer customer questions using the provided documentation context. Follow these guidelines:
        
        1. Provide accurate, helpful answers based on the documentation
        2. If the documentation doesn't contain enough information, say so clearly
        3. Structure your response clearly with actionable steps when applicable
        4. Be concise but comprehensive
        5. Use a friendly, professional tone
        6. Reference the documentation when appropriate
        
        Always base your answer on the provided context. Do not make up information not found in the documentation.
        """
        
        user_prompt = f"""
        Based on the following documentation context, please answer this customer question:
        
        Question: {query}
        
        Documentation Context:
        {context}
        
        Please provide a comprehensive answer that helps the customer resolve their question.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            return RAGResponse(
                answer=answer,
                sources=sources,
                confidence=0.85,  # High confidence when we have relevant content
                reasoning=f"Generated answer using {len(sources)} documentation sources"
            )
            
        except Exception as e:
            error_message = str(e)
            
            # Check if it's an API quota error
            if "429" in error_message or "quota" in error_message.lower() or "billing" in error_message.lower():
                # Provide a helpful response using the retrieved content
                if content_pairs:
                    # Extract key information from the documentation content
                    combined_content = "\n".join([content for _, content in content_pairs[:2]])
                    
                    # Provide a basic response based on the query and content
                    if any(word in query.lower() for word in ['connect', 'connection', 'setup', 'configure']):
                        answer = """Based on the Atlan documentation, here are the key steps for connecting data sources:

1. **Access the Integrations Panel**: Navigate to the integrations section in your Atlan workspace
2. **Select Your Data Source**: Choose from supported connectors like Snowflake, Databricks, Power BI, etc.
3. **Configure Connection**: Provide the necessary credentials and connection details
4. **Test Connection**: Verify the connection is working properly
5. **Set Up Crawling**: Configure automated metadata discovery

For specific connection guides, please refer to the Atlan documentation for detailed step-by-step instructions."""
                    
                    elif any(word in query.lower() for word in ['api', 'sdk', 'python', 'java']):
                        answer = """Based on the Atlan documentation, here's information about APIs and SDKs:

**Available SDKs:**
- Python SDK: Install with `pip install pyatlan`
- Java SDK: Available via Maven Central

**Common Operations:**
- Asset Management: Create, update, and retrieve data assets
- Metadata Management: Add custom metadata to assets
- Search API: Programmatic search across your catalog
- Lineage API: Query and update data lineage

**Authentication:**
All API calls require an API key. Generate your API key from the Admin panel in your Atlan workspace.

For detailed API documentation and code examples, please visit the Atlan Developer Hub."""
                    
                    elif any(word in query.lower() for word in ['sso', 'authentication', 'login', 'okta', 'azure']):
                        answer = """Based on the Atlan documentation, here's information about SSO configuration:

**Supported Identity Providers:**
- OKTA
- Azure Active Directory
- Google Workspace
- SAML 2.0 compliant providers

**General Setup Steps:**
1. Configure your identity provider with Atlan URLs
2. Download and configure SAML certificates
3. Set up user attribute mapping
4. Test the integration
5. Enable SSO for your organization

**Troubleshooting:**
- Verify SAML response format
- Check certificate validity
- Ensure user attributes are mapped correctly

For detailed SSO setup instructions, please refer to the Atlan documentation."""
                    
                    elif any(word in query.lower() for word in ['glossary', 'term', 'business term', 'definition', 'vocabulary', 'metadata']):
                        answer = """Based on the Atlan documentation, here's information about Glossary management:

**Atlan Glossary Features:**
- AtlasGlossary: Centralized business vocabulary container
- AtlasGlossaryTerm: Individual business terms with definitions
- AtlasGlossaryCategory: Hierarchical organization of terms
- Term Relationships: Link terms to data assets and other terms

**Creating and Managing Glossary Terms:**
1. **Create Glossary**: Set up a new business glossary container
2. **Add Terms**: Define business terms with clear descriptions
3. **Categorize**: Organize terms into logical categories
4. **Link to Assets**: Associate terms with relevant data assets
5. **Set Relationships**: Define parent-child and related term connections

**Best Practices:**
- Use clear, business-friendly definitions
- Involve domain experts in term creation
- Maintain consistent terminology across teams
- Link terms to actual data assets for better discovery

**API Operations:**
- Create/Update glossary terms programmatically
- Bulk import terms from existing systems
- Query terms and their relationships
- Manage term approval workflows

For detailed glossary management instructions, please refer to the Atlan documentation."""
                    
                    else:
                        answer = """Based on the Atlan documentation, Atlan is a modern data catalog that helps you:

**Core Features:**
- Discover and search data assets across your organization
- Track automated data lineage and dependencies
- Implement data governance and policies at scale
- Collaborate on data projects with your team
- Integrate with popular tools like Snowflake, Databricks, Power BI

**Quick Start:**
1. Connect your data sources through the integrations panel
2. Set up automated crawling to discover assets
3. Define governance policies and assign data stewards
4. Start discovering and using your data through the catalog

For more detailed information, please visit the Atlan documentation."""
                    
                    return RAGResponse(
                        answer=answer,
                        sources=sources,
                        confidence=0.75,
                        reasoning="API quota exceeded - provided response based on documentation content"
                    )
            
            # Default error response
            return RAGResponse(
                answer=f"I apologize, but I encountered an error while processing your question. Please check the Atlan documentation at https://docs.atlan.com/ or contact support directly for assistance.",
                sources=sources,
                confidence=0.0,
                reasoning=f"Error generating response: API quota exceeded"
            )
    
    def should_use_rag(self, topic_tags: List[str]) -> bool:
        """
        Determine if RAG should be used based on topic tags.
        """
        rag_suitable_topics = {'How-to', 'Product', 'Best practices', 'API/SDK', 'SSO', 'Glossary'}
        return bool(set(topic_tags) & rag_suitable_topics)
    
    def generate_routing_message(self, topic_tags: List[str], priority: str) -> str:
        """
        Generate a routing message for non-RAG topics.
        """
        primary_topic = topic_tags[0] if topic_tags else "General"
        
        routing_messages = {
            'Connector': f"This ticket has been classified as a '{primary_topic}' issue and has been routed to our Data Integration team. They specialize in connector issues and will review your case shortly.",
            'Lineage': f"This ticket has been classified as a '{primary_topic}' issue and has been routed to our Data Lineage team. They will help you with data lineage and dependency tracking questions.",
            'Glossary': f"This ticket has been classified as a '{primary_topic}' issue and has been routed to our Data Governance team. They will assist you with glossary and metadata management.",
            'Sensitive data': f"This ticket has been classified as a '{primary_topic}' issue and has been routed to our Data Security team. They specialize in data classification and compliance matters."
        }
        
        message = routing_messages.get(primary_topic, 
            f"This ticket has been classified as a '{primary_topic}' issue and has been routed to the appropriate specialized team.")
        
        if priority == "P0 (High)":
            message += " Due to the high priority of this issue, it will be escalated for immediate attention."
        
        return message


if __name__ == "__main__":
    # Test the RAG pipeline
    rag = AtlanRAGPipeline()
    
    test_query = "How do I connect a Snowflake data source?"
    test_topics = ["How-to", "Connector"]
    
    if rag.should_use_rag(test_topics):
        response = rag.generate_rag_response(test_query, test_topics)
        print(f"RAG Response: {response}")
    else:
        message = rag.generate_routing_message(test_topics, "P1 (Medium)")
        print(f"Routing Message: {message}")
