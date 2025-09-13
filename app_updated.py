import streamlit as st
import pandas as pd
from typing import Dict, List
import os
from datetime import datetime
import sys

# Import our updated modules
try:
    from classifier import AtlanTicketClassifier, load_sample_tickets
    from rag_corrected import AtlanRAGPipeline
    MODELS_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Some models not available: {e}")
    MODELS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Atlan Customer Support AI Copilot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .classification-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .response-box {
        background-color: #f1f8e9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .model-info {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #ff9800;
    }
    .priority-high {
        color: #d32f2f;
        font-weight: bold;
    }
    .priority-medium {
        color: #f57c00;
        font-weight: bold;
    }
    .priority-low {
        color: #388e3c;
        font-weight: bold;
    }
    .sentiment-angry {
        color: #d32f2f;
    }
    .sentiment-frustrated {
        color: #f57c00;
    }
    .sentiment-neutral {
        color: #666;
    }
    .sentiment-curious {
        color: #1976d2;
    }
    .sentiment-urgent {
        color: #9c27b0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'classified_tickets_df' not in st.session_state:
        st.session_state.classified_tickets_df = None
    if 'classifier' not in st.session_state:
        st.session_state.classifier = None
    if 'rag_pipeline' not in st.session_state:
        st.session_state.rag_pipeline = None

def setup_sidebar_info():
    """Setup sidebar with model information"""
    with st.sidebar:
        st.header("🔧 AI Pipeline Configuration")
        
        st.markdown('<div class="model-info">', unsafe_allow_html=True)
        st.markdown("**🤖 Core AI Models:**")
        
        if MODELS_AVAILABLE:
            st.markdown("✅ **Topic Classification**")
            st.markdown("   • Zero-shot: `facebook/bart-large-mnli`")
            st.markdown("   • Fallback: Rule-based keywords")
            
            st.markdown("✅ **Sentiment Analysis**") 
            st.markdown("   • Model: `cardiffnlp/twitter-roberta-base-sentiment`")
            st.markdown("   • Fallback: Keyword-based rules")
            
            st.markdown("✅ **Priority Detection**")
            st.markdown("   • Rule-based: urgent/critical keywords")
            
            st.markdown("✅ **RAG Pipeline**")
            st.markdown("   • Embeddings: `sentence-transformers/all-MiniLM-L6-v2`")
            st.markdown("   • Vector Storage: FAISS IndexFlatIP")
            st.markdown("   • Chunking: 500 words with 50 overlap")
        else:
            st.markdown("❌ **Models not loaded**")
            st.markdown("Run: `pip install -r requirements_new.txt`")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("**📊 Data Format:**")
        st.markdown("• CSV format: `sample_tickets.csv`")
        st.markdown("• 12 realistic support scenarios")
        
        st.markdown("**🎯 Response Logic:**")
        st.markdown("• RAG: How-to, Product, API/SDK, SSO, Best practices")
        st.markdown("• Routing: Connector, Lineage, Glossary, Sensitive data")

def format_priority_class(priority: str) -> str:
    """Return CSS class for priority formatting."""
    if "P0" in priority or "High" in priority:
        return "priority-high"
    elif "P1" in priority or "Medium" in priority:
        return "priority-medium"
    else:
        return "priority-low"

def format_sentiment_class(sentiment: str) -> str:
    """Return CSS class for sentiment formatting."""
    sentiment_lower = sentiment.lower()
    if "angry" in sentiment_lower:
        return "sentiment-angry"
    elif "frustrated" in sentiment_lower:
        return "sentiment-frustrated"
    elif "curious" in sentiment_lower:
        return "sentiment-curious"
    elif "urgent" in sentiment_lower:
        return "sentiment-urgent"
    else:
        return "sentiment-neutral"

def display_classification_dashboard():
    """Display the bulk classification dashboard."""
    st.markdown('<div class="section-header">📊 Bulk Ticket Classification Dashboard</div>', unsafe_allow_html=True)
    
    if not MODELS_AVAILABLE:
        st.error("❌ AI models not available. Please install requirements: `pip install -r requirements_new.txt`")
        return
    
    # Load and classify tickets button
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🔄 Load & Classify Sample Tickets", type="primary"):            
            with st.spinner("Loading classification models and processing tickets..."):
                try:
                    # Initialize classifier if needed
                    if st.session_state.classifier is None:
                        st.session_state.classifier = AtlanTicketClassifier()
                    
                    # Load sample tickets from CSV
                    tickets_df = load_sample_tickets("sample_tickets.csv")
                    if tickets_df.empty:
                        st.error("❌ Could not load sample tickets. Please check if sample_tickets.csv exists.")
                        return
                    
                    # Classify tickets
                    classified_df = st.session_state.classifier.classify_multiple_tickets(tickets_df)
                    st.session_state.classified_tickets_df = classified_df
                    
                    st.success(f"✅ Successfully classified {len(classified_df)} tickets using ML models!")
                    
                except Exception as e:
                    st.error(f"❌ Error during classification: {str(e)}")
                    return
    
    # Display classified tickets
    if st.session_state.classified_tickets_df is not None:
        tickets_df = st.session_state.classified_tickets_df
        
        st.markdown("### Classification Results")
        
        # Statistics
        total_tickets = len(tickets_df)
        
        # Create metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tickets", total_tickets)
        
        with col2:
            high_priority = sum(1 for _, row in tickets_df.iterrows() if "P0" in row['priority'])
            st.metric("High Priority", high_priority)
        
        with col3:
            angry_frustrated = sum(1 for _, row in tickets_df.iterrows() if row['sentiment'] in ['Angry', 'Frustrated'])
            st.metric("Angry/Frustrated", angry_frustrated)
        
        with col4:
            avg_confidence = tickets_df['confidence'].mean()
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")
        
        # Display tickets in expandable format
        for idx, row in tickets_df.iterrows():
            with st.expander(f"Ticket {idx + 1}: {row['subject']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Ticket ID:** {row['ticket_id']}")
                    st.markdown(f"**Customer:** {row['customer_name']}")
                    st.markdown(f"**Created:** {row['created_at']}")
                    st.markdown(f"**Description:** {row['description']}")
                
                with col2:
                    tags_str = ", ".join(row['topic_tags']) if isinstance(row['topic_tags'], list) else str(row['topic_tags'])
                    
                    priority_class = format_priority_class(row['priority'])
                    sentiment_class = format_sentiment_class(row['sentiment'])
                    
                    st.markdown(f'<div class="classification-box">', unsafe_allow_html=True)
                    st.markdown(f"**Topic Tags:** {tags_str}")
                    st.markdown(f'**Sentiment:** <span class="{sentiment_class}">{row["sentiment"]}</span>', unsafe_allow_html=True)
                    st.markdown(f'**Priority:** <span class="{priority_class}">{row["priority"]}</span>', unsafe_allow_html=True)
                    st.markdown(f"**Confidence:** {row['confidence']:.2f}")
                    st.markdown(f"**Reasoning:** {row['reasoning']}")
                    st.markdown('</div>', unsafe_allow_html=True)

def display_interactive_agent():
    """Display the interactive AI agent interface."""
    st.markdown('<div class="section-header">🤖 Interactive AI Agent</div>', unsafe_allow_html=True)
    
    if not MODELS_AVAILABLE:
        st.error("❌ AI models not available. Please install requirements: `pip install -r requirements_new.txt`")
        return
    
    # Initialize components if needed
    if st.session_state.classifier is None:
        with st.spinner("Loading classification models..."):
            st.session_state.classifier = AtlanTicketClassifier()
    
    if st.session_state.rag_pipeline is None:
        with st.spinner("Loading RAG pipeline..."):
            st.session_state.rag_pipeline = AtlanRAGPipeline()
    
    # Input form
    with st.form("ticket_form", clear_on_submit=True):
        st.markdown("### Submit a New Query")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            subject = st.text_input("Subject:", placeholder="Brief description of your issue...")
            description = st.text_area("Description:", placeholder="Detailed description of your question or issue...", height=100)
        
        with col2:
            st.markdown("**Supported Topics:**")
            st.markdown("• How-to questions")
            st.markdown("• Product features")
            st.markdown("• API/SDK usage")
            st.markdown("• SSO configuration")
            st.markdown("• Best practices")
            st.markdown("• Connector issues")
            st.markdown("• Data lineage")
            st.markdown("• Glossary management")
            st.markdown("• Sensitive data")
        
        submitted = st.form_submit_button("🚀 Analyze & Respond", type="primary")
    
    if submitted and subject and description:
        with st.spinner("Analyzing your query with ML models..."):
            try:
                # Step 1: Classify the ticket
                classification = st.session_state.classifier.classify_ticket(subject, description)
                
                # Step 2: Display internal analysis
                st.markdown("### 🔍 Internal Analysis (Back-end View)")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown('<div class="classification-box">', unsafe_allow_html=True)
                    st.markdown("**Classification Results:**")
                    
                    tags_str = ", ".join(classification.topic_tags)
                    priority_class = format_priority_class(classification.priority)
                    sentiment_class = format_sentiment_class(classification.sentiment)
                    
                    st.markdown(f"**Topic Tags:** {tags_str}")
                    st.markdown(f'**Sentiment:** <span class="{sentiment_class}">{classification.sentiment}</span>', unsafe_allow_html=True)
                    st.markdown(f'**Priority:** <span class="{priority_class}">{classification.priority}</span>', unsafe_allow_html=True)
                    st.markdown(f"**Confidence:** {classification.confidence:.2f}")
                    st.markdown(f"**Reasoning:** {classification.reasoning}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="classification-box">', unsafe_allow_html=True)
                    st.markdown("**Processing Decision:**")
                    
                    if st.session_state.rag_pipeline.should_use_rag(classification.topic_tags):
                        st.markdown("✅ **RAG Response** - Using knowledge base")
                        st.markdown("Vector similarity search in FAISS index")
                        st.markdown("Contextual response generation")
                    else:
                        st.markdown("🔄 **Route to Team** - Specialized handling")
                        st.markdown("Topic requires human expertise")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Step 3: Generate and display final response
                st.markdown("### 💬 Final Response (Front-end View)")
                
                if st.session_state.rag_pipeline.should_use_rag(classification.topic_tags):
                    # Generate RAG response
                    with st.spinner("Retrieving from knowledge base and generating response..."):
                        rag_response = st.session_state.rag_pipeline.generate_response(
                            f"{subject} {description}", classification.topic_tags
                        )
                    
                    st.markdown('<div class="response-box">', unsafe_allow_html=True)
                    st.markdown("**AI Response:**")
                    st.markdown(rag_response.answer)
                    
                    if rag_response.sources:
                        st.markdown("**Sources:**")
                        for source in rag_response.sources:
                            if source.startswith('http'):
                                st.markdown(f"• [{source}]({source})")
                            else:
                                st.markdown(f"• {source}")
                    
                    st.markdown(f"**Response Confidence:** {rag_response.confidence:.2f}")
                    st.markdown(f"**Generation Method:** {rag_response.reasoning}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                else:
                    # Generate routing message
                    routing_response = st.session_state.rag_pipeline._generate_routing_message(classification.topic_tags)
                    
                    st.markdown('<div class="response-box">', unsafe_allow_html=True)
                    st.markdown("**Routing Information:**")
                    st.markdown(routing_response.answer)
                    st.markdown(f"**Routing Confidence:** {routing_response.confidence:.2f}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error processing your query: {str(e)}")

def main():
    """Main application function."""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🎯 Atlan Customer Support AI Copilot</div>', unsafe_allow_html=True)
    st.markdown("**AI-powered ticket classification and intelligent response system**")
    st.markdown("*Built with Zero-shot Classification, CardiffNLP Sentiment Analysis, and FAISS Vector Retrieval*")
    
    # Sidebar setup
    setup_sidebar_info()
    
    # Main content
    tab1, tab2 = st.tabs(["📊 Bulk Classification Dashboard", "🤖 Interactive AI Agent"])
    
    with tab1:
        display_classification_dashboard()
    
    with tab2:
        display_interactive_agent()
    
    # Footer with technical information
    st.markdown("---")
    with st.expander("ℹ️ Technical Implementation Details"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔍 Classification Pipeline:**
            - **Topic Tags**: Zero-shot classification using `facebook/bart-large-mnli`
            - **Sentiment**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
            - **Priority**: Rule-based detection (urgent, critical, blocking keywords)
            - **Fallback**: Keyword-based rules for robustness
            
            **🤖 RAG Pipeline:**
            - **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
            - **Vector Storage**: FAISS IndexFlatIP for similarity search
            - **Chunking**: 500 words with 50-word overlap
            - **Retrieval**: Top-k similarity with keyword fallback
            """)
        
        with col2:
            st.markdown("""
            **📊 Data & Features:**
            - **Data Format**: CSV format (`sample_tickets.csv`)
            - **Sample Size**: 12 diverse customer support scenarios
            - **Topics Covered**: All major support categories
            - **Response Types**: RAG-powered answers + team routing
            
            **🎯 Model Selection Rationale:**
            - Zero-shot classification for flexible topic detection
            - Twitter RoBERTa for informal text sentiment analysis
            - FAISS for efficient vector similarity search
            - Rule-based priority for business logic alignment
            """)

if __name__ == "__main__":
    main()
