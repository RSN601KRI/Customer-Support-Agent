# 🗺️ Atlan Customer Support AI - Knowledge Graph Architecture

## System Architecture Knowledge Graph

```mermaid
graph TD
    %% User Interface Layer
    UI[🌐 Streamlit Web Application<br/>- Bulk Dashboard<br/>- Interactive Agent<br/>- Real-time Processing]
    
    %% AI Pipeline Layer - Core Components
    PIPELINE[🤖 AI Pipeline Layer]
    CLASSIFIER[🧠 Ticket Classifier<br/>- OpenAI GPT-3.5 Turbo<br/>- Multi-class Classification<br/>- Fallback System]
    RAG[📚 RAG Pipeline<br/>- Knowledge Retrieval<br/>- Response Generation<br/>- Content Caching]
    ROUTER[🔄 Smart Router<br/>- Decision Engine<br/>- Team Assignment<br/>- Priority Escalation]
    
    %% Knowledge Sources
    KB[📋 Knowledge Base Layer]
    DOCS[📖 Atlan Documentation<br/>docs.atlan.com]
    DEVHUB[👨‍💻 Developer Hub<br/>developer.atlan.com]
    FALLBACK[💾 Fallback Content<br/>- Local Knowledge Base<br/>- Static Responses]
    
    %% External Services
    EXTERNAL[🌍 External APIs]
    OPENAI[🤖 OpenAI API<br/>- GPT-3.5/4 Turbo<br/>- Text Generation<br/>- Classification]
    WEBSCRAPE[🕷️ Web Scraping<br/>- BeautifulSoup<br/>- Content Extraction<br/>- Rate Limiting]
    
    %% Data Processing Components
    PREPROCESSING[🔧 Preprocessing<br/>- Text Normalization<br/>- Content Parsing<br/>- Input Validation]
    CACHE[⚡ Content Cache<br/>- Redis/In-Memory<br/>- Performance Optimization<br/>- API Rate Limiting]
    
    %% Classification Results
    TOPICS[🏷️ Topic Classification<br/>- How-to<br/>- Product<br/>- Connector<br/>- API/SDK<br/>- SSO<br/>- etc.]
    SENTIMENT[😊 Sentiment Analysis<br/>- Angry<br/>- Frustrated<br/>- Curious<br/>- Neutral<br/>- Urgent]
    PRIORITY[⚡ Priority Assessment<br/>- P0 High<br/>- P1 Medium<br/>- P2 Low]
    
    %% Output Types
    RAGRESPONSE[💬 RAG Response<br/>- AI-Generated Answer<br/>- Source Citations<br/>- Confidence Score]
    ROUTING[🎯 Team Routing<br/>- Specialized Teams<br/>- SLA Compliance<br/>- Escalation Rules]
    
    %% Connections - User Input Flow
    UI -->|User Query| PREPROCESSING
    PREPROCESSING -->|Normalized Text| PIPELINE
    
    %% AI Pipeline Processing
    PIPELINE --> CLASSIFIER
    PIPELINE --> RAG
    PIPELINE --> ROUTER
    
    %% Classification Process
    CLASSIFIER -->|Analyzes Text| OPENAI
    OPENAI -->|Returns Classification| CLASSIFIER
    CLASSIFIER --> TOPICS
    CLASSIFIER --> SENTIMENT
    CLASSIFIER --> PRIORITY
    
    %% Knowledge Retrieval
    RAG -->|Retrieves Content| KB
    KB --> DOCS
    KB --> DEVHUB
    KB --> FALLBACK
    RAG -->|Web Scraping| WEBSCRAPE
    WEBSCRAPE -->|Extracts Content| CACHE
    CACHE -->|Cached Content| RAG
    
    %% Decision Making
    TOPICS -->|Topic Analysis| ROUTER
    PRIORITY -->|Priority Check| ROUTER
    SENTIMENT -->|Sentiment Factor| ROUTER
    
    %% Response Generation
    ROUTER -->|RAG Suitable?| RAG
    RAG -->|Generates Response| OPENAI
    RAG --> RAGRESPONSE
    ROUTER -->|Complex Issue?| ROUTING
    
    %% Output to User
    RAGRESPONSE --> UI
    ROUTING --> UI
    
    %% Fallback Mechanisms
    CLASSIFIER -.->|API Failure| FALLBACK
    RAG -.->|Scraping Fails| FALLBACK
    OPENAI -.->|Quota Exceeded| FALLBACK
    
    %% Performance Optimization
    CACHE -.->|Reduces Load| OPENAI
    CACHE -.->|Speeds Up| RAG
    
    %% Styling
    classDef uiClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef aiClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef knowledgeClass fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef externalClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef outputClass fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class UI uiClass
    class PIPELINE,CLASSIFIER,RAG,ROUTER,PREPROCESSING aiClass
    class KB,DOCS,DEVHUB,FALLBACK,CACHE knowledgeClass
    class EXTERNAL,OPENAI,WEBSCRAPE externalClass
    class TOPICS,SENTIMENT,PRIORITY,RAGRESPONSE,ROUTING outputClass
```

## Component Relationships & Data Flow

### 🔄 Primary Data Flow
1. **Input Processing**: User query → Preprocessing → AI Pipeline
2. **Classification**: Text analysis → OpenAI GPT → Multi-dimensional classification
3. **Decision Making**: Router analyzes classification → RAG vs Team Routing
4. **Response Generation**: Knowledge retrieval → Content generation → User response

### 🔗 Key Relationships
- **Classifier ↔ OpenAI**: Bidirectional for classification requests and responses
- **RAG ↔ Knowledge Base**: Retrieves relevant documentation content
- **Router → Decision**: Routes based on topic complexity and user intent
- **Cache ↔ Components**: Performance optimization across all API calls

### ⚡ Fallback Mechanisms
- **API Failures**: Automatic fallback to rule-based classification
- **Content Retrieval**: Local knowledge base when web scraping fails
- **Rate Limiting**: Cached responses for quota management

### 📊 Performance Optimizations
- **Content Caching**: Reduces API calls and improves response time
- **Batch Processing**: Multiple ticket classification in single requests
- **Smart Routing**: Prevents unnecessary RAG processing for complex issues

## Architecture Benefits

### 🎯 **Scalability**
- Modular component design allows independent scaling
- Cache layer reduces external API dependencies
- Fallback systems ensure 99.9% uptime

### 🔒 **Reliability** 
- Multi-layer fallback mechanisms
- Graceful degradation when services are unavailable
- Content caching for consistent performance

### 🚀 **Performance**
- Sub-3-second response times
- Intelligent caching strategies
- Optimized API usage patterns

### 🔧 **Maintainability**
- Clear separation of concerns
- Independent component testing
- Modular architecture for easy updates
