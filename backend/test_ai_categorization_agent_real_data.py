"""
Test script for AI Categorization Agent with real Brazilian fiscal documents
Task 4.2: Test AI Categorization Agent with real products/services
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import structlog

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Import the agent directly
from agents.ai_categorization_agent import LLMEnhancedAICategorizationAgent


async def test_ai_categorization_with_real_data():
    """Test AI Categorization Agent with real Brazilian fiscal documents"""
    print("🚀 Testing AI Categorization Agent with Real Data")
    print("=" * 60)
    
    # Initialize agent
    agent = LLMEnhancedAICategorizationAgent()
    
    # Get XML files
    xml_files_dir = Path("../xml_nf")
    if not xml_files_dir.exists():
        print("❌ XML files directory not found")
        return
    
    xml_files = list(xml_files_dir.glob("*.xml")) + list(xml_files_dir.glob("*.XML"))
    
    if not xml_files:
        print("❌ No XML files found")
        return
    
    print(f"📁 Found {len(xml_files)} XML files to test")
    
    test_results = []
    all_categories = set()
    all_subcategories = set()
    supplier_analysis = {}
    
    # Test each XML file
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n📄 Testing file {i}/{len(xml_files)}: {xml_file.name}")
        print("-" * 50)
        
        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📊 File size: {xml_file.stat().st_size:,} bytes")
            
            # Prepare context
            context = {
                'document_id': f"test_{xml_file.stem}",
                'document_type': 'NFE',  # Will be detected by agent
                'test_mode': True
            }
            
            # Test item extraction
            print("📋 Extracting items for categorization...")
            items = await agent._extract_items_for_categorization(xml_content, context.get('document_type', 'NFE'))
            
            if items:
                print(f"   Found {len(items)} items to categorize")
                for j, item in enumerate(items[:3], 1):  # Show first 3 items
                    print(f"   {j}. {item.get('description', 'N/A')[:50]}...")
                    print(f"      Code: {item.get('code', 'N/A')}, Value: R$ {item.get('value', 0):.2f}")
            else:
                print("   No items found for categorization")
                continue
            
            # Test categorization
            print("🏷️  Categorizing items...")
            categorized_items = await agent._categorize_items_with_llm(items)
            
            if categorized_items:
                print(f"   Categorized {len(categorized_items)} items")
                
                # Show categorization results
                categories_found = {}
                for item in categorized_items:
                    category = item.get('category', 'Unknown')
                    subcategory = item.get('subcategory', 'Unknown')
                    categories_found[category] = categories_found.get(category, 0) + 1
                    all_categories.add(category)
                    all_subcategories.add(subcategory)
                
                print("   Categories found:")
                for category, count in categories_found.items():
                    print(f"     - {category}: {count} items")
            
            # Test category insights generation
            print("💡 Generating category insights...")
            category_insights = await agent._generate_category_insights(categorized_items)
            
            if category_insights:
                print(f"   Generated {len(category_insights)} insights:")
                for insight in category_insights[:2]:  # Show first 2
                    print(f"     - {insight.get('description', 'N/A')}")
            
            # Test pattern detection
            print("🔍 Detecting category patterns...")
            patterns = await agent._detect_category_patterns(categorized_items)
            
            if patterns:
                print(f"   Detected {len(patterns)} patterns:")
                for pattern in patterns:
                    print(f"     - {pattern.get('description', 'N/A')}")
            else:
                print("   No patterns detected")
            
            # Test full categorization workflow
            print("🔄 Testing full categorization workflow...")
            full_result = await agent.categorize_document(xml_content, context)
            
            if full_result:
                print(f"   Workflow completed successfully")
                print(f"   Total items: {full_result.get('total_items', 0)}")
                print(f"   Unique categories: {full_result.get('unique_categories', 0)}")
                print(f"   Confidence: {full_result.get('confidence', 0):.2f}")
            
            # Analyze supplier patterns
            supplier_name = None
            try:
                from lxml import etree
                root = etree.fromstring(xml_content.encode('utf-8'))
                emit = root.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
                if emit is not None:
                    nome_elem = emit.find('.//{http://www.portalfiscal.inf.br/nfe}xNome')
                    if nome_elem is not None:
                        supplier_name = nome_elem.text
            except:
                pass
            
            if supplier_name:
                if supplier_name not in supplier_analysis:
                    supplier_analysis[supplier_name] = {
                        'documents': 0,
                        'categories': set(),
                        'total_items': 0,
                        'total_value': 0
                    }
                
                supplier_analysis[supplier_name]['documents'] += 1
                supplier_analysis[supplier_name]['total_items'] += len(categorized_items)
                
                for item in categorized_items:
                    supplier_analysis[supplier_name]['categories'].add(item.get('category', 'Unknown'))
                    supplier_analysis[supplier_name]['total_value'] += item.get('value', 0)
            
            # Store test result
            test_result = {
                "filename": xml_file.name,
                "file_size": xml_file.stat().st_size,
                "items_found": len(items) if items else 0,
                "items_categorized": len(categorized_items) if categorized_items else 0,
                "categories_found": len(categories_found) if 'categories_found' in locals() else 0,
                "insights_generated": len(category_insights) if category_insights else 0,
                "patterns_detected": len(patterns) if patterns else 0,
                "supplier_name": supplier_name,
                "full_result": full_result,
                "success": True
            }
            
            test_results.append(test_result)
            print("✅ Categorization completed successfully")
            
        except Exception as e:
            print(f"❌ Error processing {xml_file.name}: {str(e)}")
            test_results.append({
                "filename": xml_file.name,
                "error": str(e),
                "success": False
            })
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY REPORT - AI CATEGORIZATION AGENT")
    print("=" * 60)
    
    total_files = len(test_results)
    successful_files = sum(1 for r in test_results if r.get("success", False))
    failed_files = total_files - successful_files
    
    print(f"📁 Total Files Tested: {total_files}")
    print(f"✅ Successful: {successful_files}")
    print(f"❌ Failed: {failed_files}")
    print(f"📈 Success Rate: {(successful_files/total_files*100):.1f}%")
    
    if successful_files > 0:
        # Items analysis
        total_items = sum(r.get("items_found", 0) for r in test_results if r.get("success"))
        total_categorized = sum(r.get("items_categorized", 0) for r in test_results if r.get("success"))
        
        print(f"\n📦 Items Analysis:")
        print(f"   Total Items Found: {total_items}")
        print(f"   Total Items Categorized: {total_categorized}")
        if total_items > 0:
            print(f"   Categorization Rate: {(total_categorized/total_items*100):.1f}%")
        
        # Categories analysis
        print(f"\n🏷️  Categories Analysis:")
        print(f"   Unique Categories Found: {len(all_categories)}")
        print(f"   Categories: {', '.join(sorted(all_categories))}")
        
        print(f"\n🏷️  Subcategories Analysis:")
        print(f"   Unique Subcategories Found: {len(all_subcategories)}")
        if len(all_subcategories) <= 10:
            print(f"   Subcategories: {', '.join(sorted(all_subcategories))}")
        else:
            print(f"   Top Subcategories: {', '.join(sorted(list(all_subcategories))[:10])}")
        
        # Insights analysis
        total_insights = sum(r.get("insights_generated", 0) for r in test_results if r.get("success"))
        total_patterns = sum(r.get("patterns_detected", 0) for r in test_results if r.get("success"))
        
        print(f"\n💡 Insights Analysis:")
        print(f"   Total Insights Generated: {total_insights}")
        print(f"   Total Patterns Detected: {total_patterns}")
        if successful_files > 0:
            print(f"   Average Insights per Document: {total_insights/successful_files:.1f}")
            print(f"   Average Patterns per Document: {total_patterns/successful_files:.1f}")
        
        # Supplier analysis
        if supplier_analysis:
            print(f"\n🏢 Supplier Analysis:")
            print(f"   Unique Suppliers: {len(supplier_analysis)}")
            
            # Top suppliers by document count
            top_suppliers = sorted(supplier_analysis.items(), 
                                 key=lambda x: x[1]['documents'], reverse=True)[:5]
            
            print(f"   Top Suppliers by Document Count:")
            for supplier, data in top_suppliers:
                categories_count = len(data['categories'])
                print(f"     - {supplier}: {data['documents']} docs, {categories_count} categories, R$ {data['total_value']:.2f}")
            
            # Category diversity analysis
            print(f"\n📊 Category Diversity by Supplier:")
            diverse_suppliers = sorted(supplier_analysis.items(), 
                                     key=lambda x: len(x[1]['categories']), reverse=True)[:3]
            
            for supplier, data in diverse_suppliers:
                categories_list = ', '.join(sorted(data['categories']))
                print(f"     - {supplier}: {len(data['categories'])} categories ({categories_list})")
    
    # Failed files details
    if failed_files > 0:
        print(f"\n❌ Failed Files:")
        for result in test_results:
            if not result["success"]:
                print(f"   {result['filename']}: {result.get('error', 'Unknown error')}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_categorization_test_results_{timestamp}.json"
    
    try:
        # Convert sets to lists for JSON serialization
        for supplier_data in supplier_analysis.values():
            supplier_data['categories'] = list(supplier_data['categories'])
        
        results_to_save = {
            "test_results": test_results,
            "summary": {
                "total_files": total_files,
                "successful_files": successful_files,
                "failed_files": failed_files,
                "all_categories": list(all_categories),
                "all_subcategories": list(all_subcategories),
                "supplier_analysis": supplier_analysis
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_to_save, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Detailed results saved to: {filename}")
        
    except Exception as e:
        print(f"⚠️  Could not save results to file: {str(e)}")
    
    print("\n🎉 AI Categorization Agent Real Data Test Completed!")


async def test_categorization_methods():
    """Test individual categorization methods"""
    print("\n🧪 Testing Individual Categorization Methods")
    print("-" * 50)
    
    agent = LLMEnhancedAICategorizationAgent()
    
    # Test sample items
    test_items = [
        {
            "code": "COMP001",
            "description": "Notebook Dell Inspiron 15 3000",
            "type": "product",
            "value": 2500.00
        },
        {
            "code": "MOV001", 
            "description": "Mesa de escritório em madeira",
            "type": "product",
            "value": 800.00
        },
        {
            "code": "SERV001",
            "description": "Consultoria em tecnologia da informação",
            "type": "service",
            "value": 5000.00
        },
        {
            "code": "MAT001",
            "description": "Papel A4 sulfite 500 folhas",
            "type": "product", 
            "value": 25.00
        }
    ]
    
    print("🏷️  Testing category determination...")
    for item in test_items:
        category = await agent._determine_category(item)
        subcategory = await agent._determine_subcategory(item, category)
        
        print(f"   Item: {item['description']}")
        print(f"   Category: {category}")
        print(f"   Subcategory: {subcategory}")
        print()
    
    print("📊 Testing categorization with LLM...")
    categorized = await agent._categorize_items_with_llm(test_items)
    
    for item in categorized:
        print(f"   {item['description'][:30]}...")
        print(f"   Category: {item.get('category', 'N/A')}")
        print(f"   Subcategory: {item.get('subcategory', 'N/A')}")
        print(f"   Confidence: {item.get('confidence', 0):.2f}")
        print()


if __name__ == "__main__":
    print("🧪 AI Categorization Agent Real Data Test Suite")
    print("=" * 60)
    
    async def main():
        # Test individual methods
        await test_categorization_methods()
        
        # Run comprehensive test suite
        await test_ai_categorization_with_real_data()
    
    # Run the tests
    asyncio.run(main())