#!/usr/bin/env python3

from lxml import etree
from pathlib import Path

def test_upload_detection():
    """Test the same detection logic used in upload"""
    
    nfse_file = Path("../xml_nf/42054072257653110000170000000000000725050541353120.xml")
    
    with open(nfse_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    root = etree.fromstring(xml_content.encode('utf-8'))
    
    # Same logic as in upload
    document_type = 'NFE'  # Default
    
    nfse_indicators = []
    
    try:
        # Root element checks
        nfse_indicators.extend([
            root.tag.lower() == 'nfse',
            'nfse' in root.tag.lower(),
        ])
        
        # Namespace checks (safe)
        if hasattr(root, 'nsmap') and root.nsmap:
            nfse_indicators.extend([
                'nfse' in str(root.nsmap),
                'http://www.sped.fazenda.gov.br/nfse' in str(root.nsmap.values())
            ])
        
        # Element checks (using xpath for local-name or direct namespace)
        nfse_indicators.extend([
            len(root.xpath('.//*[local-name()="NFSe"]')) > 0 if hasattr(root, 'xpath') else False,
            len(root.xpath('.//*[local-name()="infNFSe"]')) > 0 if hasattr(root, 'xpath') else False,
            len(root.xpath('.//*[local-name()="DPS"]')) > 0 if hasattr(root, 'xpath') else False,
            len(root.xpath('.//*[local-name()="CompNfse"]')) > 0 if hasattr(root, 'xpath') else False,
            len(root.xpath('.//*[local-name()="RPS"]')) > 0 if hasattr(root, 'xpath') else False,
            
            # Fallback namespace-aware search
            root.find('.//NFSe') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}NFSe') is not None,
            root.find('.//infNFSe') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}infNFSe') is not None,
            root.find('.//DPS') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}DPS') is not None,
        ])
        
        # Content checks
        nfse_indicators.extend([
            'nfse' in xml_content.lower(),
            'infnfse' in xml_content.lower(),
            'servico' in xml_content.lower() and 'prestador' in xml_content.lower()
        ])
        
    except Exception as e:
        print(f"Error in NFSE detection: {e}")
    
    if any(nfse_indicators):
        document_type = 'NFSE'
    
    print(f"📄 File: {nfse_file.name}")
    print(f"🔍 Detected type: {document_type}")
    print(f"📊 Positive indicators: {sum(nfse_indicators)}/{len(nfse_indicators)}")
    print(f"✅ Detection result: {'CORRECT' if document_type == 'NFSE' else 'INCORRECT'}")

if __name__ == "__main__":
    test_upload_detection()