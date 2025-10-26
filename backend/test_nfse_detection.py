#!/usr/bin/env python3

from lxml import etree
from pathlib import Path

def test_nfse_detection():
    """Test NFSE detection logic"""
    
    nfse_file = Path("../xml_nf/42054072257653110000170000000000000725050541353120.xml")
    
    print("🧪 Testing NFSE Detection Logic")
    print("=" * 50)
    
    # Read the file
    with open(nfse_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    print(f"📄 File: {nfse_file.name}")
    print(f"📊 Size: {len(xml_content)} characters")
    
    # Parse XML
    root = etree.fromstring(xml_content.encode('utf-8'))
    
    print(f"\n🔍 XML Analysis:")
    print(f"   Root tag: {root.tag}")
    print(f"   Root namespace: {root.nsmap if hasattr(root, 'nsmap') else 'None'}")
    
    # Test each detection method
    print(f"\n🧪 Detection Tests:")
    
    # Test 1: Root element checks
    test1a = root.tag.lower() == 'nfse'
    test1b = 'nfse' in root.tag.lower()
    print(f"   1a. Root tag == 'nfse': {test1a}")
    print(f"   1b. 'nfse' in root tag: {test1b}")
    
    # Test 2: Namespace checks
    if hasattr(root, 'nsmap') and root.nsmap:
        test2a = 'nfse' in str(root.nsmap)
        test2b = 'http://www.sped.fazenda.gov.br/nfse' in str(root.nsmap.values())
        print(f"   2a. 'nfse' in nsmap: {test2a}")
        print(f"   2b. SPED namespace in nsmap: {test2b}")
    else:
        print(f"   2. No nsmap available")
    
    # Test 3: Element checks (using xpath for local-name)
    try:
        test3a = len(root.xpath('.//*[local-name()="NFSe"]')) > 0
        test3b = len(root.xpath('.//*[local-name()="infNFSe"]')) > 0
        test3c = len(root.xpath('.//*[local-name()="DPS"]')) > 0
        test3d = len(root.xpath('.//*[local-name()="CompNfse"]')) > 0
        test3e = len(root.xpath('.//*[local-name()="RPS"]')) > 0
    except Exception as e:
        print(f"   XPath error: {e}")
        # Fallback to simple element search
        test3a = root.find('.//NFSe') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}NFSe') is not None
        test3b = root.find('.//infNFSe') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}infNFSe') is not None
        test3c = root.find('.//DPS') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}DPS') is not None
        test3d = root.find('.//CompNfse') is not None
        test3e = root.find('.//RPS') is not None
    
    print(f"   3a. Has NFSe element: {test3a}")
    print(f"   3b. Has infNFSe element: {test3b}")
    print(f"   3c. Has DPS element: {test3c}")
    print(f"   3d. Has CompNfse element: {test3d}")
    print(f"   3e. Has RPS element: {test3e}")
    
    # Test 4: Content checks
    test4a = 'nfse' in xml_content.lower()
    test4b = 'infnfse' in xml_content.lower()
    test4c = 'servico' in xml_content.lower() and 'prestador' in xml_content.lower()
    
    print(f"   4a. 'nfse' in content: {test4a}")
    print(f"   4b. 'infnfse' in content: {test4b}")
    print(f"   4c. 'servico' and 'prestador' in content: {test4c}")
    
    # Overall result
    all_tests = [test1a, test1b, test3a, test3b, test3c, test3d, test3e, test4a, test4b, test4c]
    if hasattr(root, 'nsmap') and root.nsmap:
        test2a = 'nfse' in str(root.nsmap)
        test2b = 'http://www.sped.fazenda.gov.br/nfse' in str(root.nsmap.values())
        all_tests.extend([test2a, test2b])
    
    positive_tests = sum(all_tests)
    should_be_nfse = any(all_tests)
    
    print(f"\n📊 Results:")
    print(f"   Positive tests: {positive_tests}/{len(all_tests)}")
    print(f"   Should be detected as NFSE: {should_be_nfse}")
    
    if should_be_nfse:
        print("   ✅ NFSE detection should work!")
    else:
        print("   ❌ NFSE detection failed - need to improve logic")
        
        # Show first 500 chars of content for debugging
        print(f"\n🔍 Content preview (first 500 chars):")
        print(xml_content[:500])

if __name__ == "__main__":
    test_nfse_detection()