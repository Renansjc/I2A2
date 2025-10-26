"""
Integration test for Dimensional Processing Agent with real XML data
"""

import asyncio
from agents.dimensional_processing_agent import DimensionalProcessingAgent
from agents.dimensional_coordinator import DimensionalCoordinator


async def test_dimensional_processing_with_sample_xml():
    """Test dimensional processing with sample XML data"""
    
    # Sample NF-e XML content (simplified)
    sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe Id="NFe35200714200166000187550010000000046123456789">
            <ide>
                <cUF>35</cUF>
                <cNF>12345678</cNF>
                <natOp>Venda de produtos</natOp>
                <mod>55</mod>
                <serie>1</serie>
                <nNF>46</nNF>
                <dhEmi>2020-07-01T10:00:00-03:00</dhEmi>
                <tpNF>1</tpNF>
                <idDest>1</idDest>
                <cMunFG>3550308</cMunFG>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <cDV>9</cDV>
                <tpAmb>2</tpAmb>
                <finNFe>1</finNFe>
                <indFinal>0</indFinal>
                <indPres>1</indPres>
            </ide>
            <emit>
                <CNPJ>14200166000187</CNPJ>
                <xNome>Empresa Teste Ltda</xNome>
                <xFant>Teste</xFant>
                <enderEmit>
                    <xLgr>Rua das Flores</xLgr>
                    <nro>123</nro>
                    <xBairro>Centro</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>São Paulo</xMun>
                    <UF>SP</UF>
                    <CEP>01234567</CEP>
                    <cPais>1058</cPais>
                    <xPais>Brasil</xPais>
                </enderEmit>
                <IE>123456789012</IE>
                <CRT>3</CRT>
            </emit>
            <dest>
                <CNPJ>11222333000181</CNPJ>
                <xNome>Cliente Teste Ltda</xNome>
                <enderDest>
                    <xLgr>Av. Paulista</xLgr>
                    <nro>1000</nro>
                    <xBairro>Bela Vista</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>São Paulo</xMun>
                    <UF>SP</UF>
                    <CEP>01310100</CEP>
                    <cPais>1058</cPais>
                    <xPais>Brasil</xPais>
                </enderDest>
                <indIEDest>1</indIEDest>
                <IE>987654321098</IE>
            </dest>
            <det nItem="1">
                <prod>
                    <cProd>PROD001</cProd>
                    <cEAN>7891234567890</cEAN>
                    <xProd>Notebook Dell Inspiron 15</xProd>
                    <NCM>84713012</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>1.0000</qCom>
                    <vUnCom>2500.0000000000</vUnCom>
                    <vProd>2500.00</vProd>
                    <cEANTrib>7891234567890</cEANTrib>
                    <uTrib>UN</uTrib>
                    <qTrib>1.0000</qTrib>
                    <vUnTrib>2500.0000000000</vUnTrib>
                </prod>
            </det>
            <total>
                <ICMSTot>
                    <vBC>2500.00</vBC>
                    <vICMS>450.00</vICMS>
                    <vICMSDeson>0.00</vICMSDeson>
                    <vFCP>0.00</vFCP>
                    <vBCST>0.00</vBCST>
                    <vST>0.00</vST>
                    <vFCPST>0.00</vFCPST>
                    <vFCPSTRet>0.00</vFCPSTRet>
                    <vProd>2500.00</vProd>
                    <vFrete>0.00</vFrete>
                    <vSeg>0.00</vSeg>
                    <vDesc>0.00</vDesc>
                    <vII>0.00</vII>
                    <vIPI>0.00</vIPI>
                    <vIPIDevol>0.00</vIPIDevol>
                    <vPIS>0.00</vPIS>
                    <vCOFINS>0.00</vCOFINS>
                    <vOutro>0.00</vOutro>
                    <vNF>2500.00</vNF>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>'''
    
    # Test dimensional processing agent
    agent = DimensionalProcessingAgent()
    await agent.initialize()
    
    try:
        # Test data extraction methods
        from lxml import etree
        root = etree.fromstring(sample_xml.encode('utf-8'))
        
        # Test emitente extraction
        emitente_data = agent._extract_emitente_data(root, "NFE")
        print("Emitente data extracted:", emitente_data)
        assert emitente_data['cnpj'] == '14200166000187'
        assert emitente_data['razao_social'] == 'Empresa Teste Ltda'
        
        # Test destinatario extraction
        destinatario_data = agent._extract_destinatario_data(root, "NFE")
        print("Destinatario data extracted:", destinatario_data)
        assert destinatario_data['cnpj'] == '11222333000181'
        assert destinatario_data['razao_social'] == 'Cliente Teste Ltda'
        
        # Test products extraction
        produtos_data = agent._extract_produtos_data(root)
        print("Products data extracted:", produtos_data)
        assert len(produtos_data) == 1
        assert produtos_data[0]['codigo_produto'] == 'PROD001'
        assert produtos_data[0]['descricao'] == 'Notebook Dell Inspiron 15'
        
        # Test NFE items extraction
        nfe_items = agent._extract_nfe_items_data(root)
        print("NFE items extracted:", nfe_items)
        assert len(nfe_items) == 1
        assert nfe_items[0]['codigo_produto'] == 'PROD001'
        assert float(nfe_items[0]['valor_total_bruto']) == 2500.00
        
        # Test data normalization
        normalized_emitente = agent._normalize_emitente_data(emitente_data)
        print("Normalized emitente:", normalized_emitente)
        assert normalized_emitente['cnpj'] == '14.200.166/0001-87'
        
        normalized_produto = agent._normalize_produto_data(produtos_data[0])
        print("Normalized produto:", normalized_produto)
        assert normalized_produto['codigo_produto'] == 'PROD001'
        
        # Test basic categorization
        categorized_produto = await agent._apply_basic_categorization(normalized_produto)
        print("Categorized produto:", categorized_produto)
        assert categorized_produto['categoria'] == 'Eletrônicos'
        assert categorized_produto['subcategoria'] == 'Informática'
        
        print("✅ All dimensional processing tests passed!")
        
    finally:
        await agent.cleanup()


async def test_dimensional_coordinator():
    """Test dimensional coordinator functionality"""
    
    coordinator = DimensionalCoordinator()
    await coordinator.initialize()
    
    try:
        # Test status determination
        test_statuses = [
            {'agent_name': 'xml_processing_agent', 'status': 'completed'},
            {'agent_name': 'ai_categorization_agent', 'status': 'completed'},
            {'agent_name': 'dimensional_processing_agent', 'status': 'completed'}
        ]
        
        overall_status = coordinator._determine_overall_status(test_statuses)
        print("Overall status:", overall_status)
        assert overall_status == 'completed'
        
        # Test with failed status
        test_statuses_failed = [
            {'agent_name': 'xml_processing_agent', 'status': 'completed'},
            {'agent_name': 'ai_categorization_agent', 'status': 'failed'},
            {'agent_name': 'dimensional_processing_agent', 'status': 'pending'}
        ]
        
        overall_status_failed = coordinator._determine_overall_status(test_statuses_failed)
        print("Overall status with failure:", overall_status_failed)
        assert overall_status_failed == 'failed'
        
        print("✅ Dimensional coordinator tests passed!")
        
    finally:
        await coordinator.cleanup()


if __name__ == "__main__":
    print("Running dimensional processing integration tests...")
    
    asyncio.run(test_dimensional_processing_with_sample_xml())
    asyncio.run(test_dimensional_coordinator())
    
    print("🎉 All integration tests passed!")