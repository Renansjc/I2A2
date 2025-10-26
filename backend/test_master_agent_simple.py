#!/usr/bin/env python3
"""
Simple test for Master Agent LLM integration
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.master_agent import MasterAgent
from utils.config import settings

async def test_master_agent():
    """Simple test for Master Agent"""
    print("🧪 Testing Master Agent LLM Integration...")
    
    try:
        # Initialize Master Agent
        master_agent = MasterAgent()
        await master_agent.initialize()
        print("✅ Master Agent initialized successfully")
        
        # Test query interpretation
        test_query = "Quais foram os maiores fornecedores no último trimestre?"
        user_context = {"user_role": "CEO", "sector": "industrial"}
        
        print(f"🔍 Testing query: {test_query}")
        
        interpretation = await master_agent.interpret_natural_query(test_query, user_context)
        
        print(f"✅ Query interpreted successfully")
        print(f"   Intent: {interpretation.intent if hasattr(interpretation, 'intent') else 'N/A'}")
        print(f"   Confidence: {interpretation.confidence_level if hasattr(interpretation, 'confidence_level') else 'N/A'}")
        
        # Cleanup
        await master_agent.cleanup()
        print("✅ Master Agent test completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Master Agent test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_master_agent())
    sys.exit(0 if success else 1)