#!/usr/bin/env python3
"""
Test script for the Atlan Customer Support AI Copilot
Run this to validate core functionality without API calls
"""

import json
import os
from pathlib import Path

def test_file_structure():
    """Test if all required files exist"""
    print("🔍 Testing file structure...")
    
    required_files = [
        'app.py',
        'ticket_classifier.py', 
        'rag_pipeline.py',
        'sample_tickets.json',
        'requirements.txt',
        'README.md',
        'Dockerfile',
        '.env.example'
    ]
    
    missing_files = []
    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def test_sample_data():
    """Test sample data format"""
    print("🔍 Testing sample data...")
    
    try:
        with open('sample_tickets.json', 'r') as f:
            tickets = json.load(f)
        
        if not isinstance(tickets, list):
            print("❌ Sample tickets should be a list")
            return False
        
        if len(tickets) == 0:
            print("❌ No sample tickets found")
            return False
        
        # Check required fields
        required_fields = ['ticket_id', 'subject', 'description', 'customer_name', 'created_at']
        for i, ticket in enumerate(tickets[:3]):  # Check first 3 tickets
            for field in required_fields:
                if field not in ticket:
                    print(f"❌ Ticket {i+1} missing field: {field}")
                    return False
        
        print(f"✅ Sample data valid ({len(tickets)} tickets)")
        return True
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in sample_tickets.json")
        return False
    except Exception as e:
        print(f"❌ Error reading sample data: {e}")
        return False

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from ticket_classifier import TicketClassifier, load_sample_tickets
        print("✅ ticket_classifier imported")
        
        from rag_pipeline import AtlanRAGPipeline
        print("✅ rag_pipeline imported")
        
        # Test basic functionality without API calls
        tickets = load_sample_tickets()
        if tickets:
            print(f"✅ Sample tickets loaded: {len(tickets)} tickets")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during import test: {e}")
        return False

def test_rag_logic():
    """Test RAG pipeline logic without API calls"""
    print("🔍 Testing RAG logic...")
    
    try:
        from rag_pipeline import AtlanRAGPipeline
        
        rag = AtlanRAGPipeline("dummy_key")  # Won't make API calls
        
        # Test topic classification logic
        test_cases = [
            (['How-to'], True),
            (['Product'], True),
            (['API/SDK'], True),
            (['SSO'], True),
            (['Best practices'], True),
            (['Connector'], False),
            (['Lineage'], False),
            (['Glossary'], False),
            (['Sensitive data'], False),
        ]
        
        for topics, should_use_rag in test_cases:
            result = rag.should_use_rag(topics)
            if result != should_use_rag:
                print(f"❌ RAG logic failed for {topics}: expected {should_use_rag}, got {result}")
                return False
        
        # Test routing message generation
        routing_msg = rag.generate_routing_message(['Connector'], 'P1 (Medium)')
        if not isinstance(routing_msg, str) or len(routing_msg) < 10:
            print("❌ Routing message generation failed")
            return False
        
        print("✅ RAG logic tests passed")
        return True
        
    except Exception as e:
        print(f"❌ RAG logic test failed: {e}")
        return False

def test_streamlit_syntax():
    """Test if Streamlit app has valid syntax"""
    print("🔍 Testing Streamlit app syntax...")
    
    try:
        import ast
        
        with open('app.py', 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse the AST to check for syntax errors
        ast.parse(source_code)
        
        print("✅ Streamlit app syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in app.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking app syntax: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 Atlan Customer Support AI Copilot - Test Suite")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Sample Data", test_sample_data),
        ("Module Imports", test_imports),
        ("RAG Logic", test_rag_logic),
        ("Streamlit Syntax", test_streamlit_syntax),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed_tests += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Application is ready to run.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up OpenAI API key in .env file")
        print("3. Run: streamlit run app.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues before running.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
