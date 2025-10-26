"""
Dimensional Data Quality Validation Tests
Task 7.2: Implementar validação de qualidade de dados

This test suite validates data quality by comparing extracted data with original XML documents,
ensuring accuracy of calculations, formatting, and consistency between dimensional and fact tables.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import structlog
from decimal import Decimal, ROUND_HALF_UP
import re
from lxml import etree

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

# Import dimensional processing components
from agents.dimensional_coordinator import DimensionalCoordinator
from utils.database import get_supabase_client


class DataQualityValidator:
    """Comprehensive data quality validator for dimensional processing"""
    
    def __init__(self):
        self.coordinator = DimensionalCoordinator()
        self.supabase_client = get_supabase_client(admin_mode=True)
        self.validation_results = []
        self.quality_metrics = {
            'total_validations': 0,
            'cnpj_validations': 0,
            'cpf_validations': 0,
            'financial_validations': 0,
            'consistency_validations': 0,
            'formatting_validations': 0,
            'calculation_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0
        }
    
    async def run_data_quality_validation_tests(self):
        """Run comprehensive data quality validation tests"""
        print("🔍 Starting Data Quality Validation Tests")
        print("=" * 80)
        
        # Initialize coordinator
        await self.coordinator.initialize()
        
        try:
            # Get XML files
            xml_files_dir = Path("../xml_nf")
            if not xml_files_dir.exists():
                xml_files_dir = Path("xml_nf")
            
            if not xml_files_dir.exists():
                print("❌ XML files directory not found")
                return
            
            # Get all XML files (both .xml and .XML extensions)
            xml_files = []
            xml_files.extend(xml_files_dir.glob("*.xml"))
            xml_files.extend(xml_files_dir.glob("*.XML"))
            
            # Remove duplicates by converting to set and back to list
            xml_files = list(set(xml_files))
            
            if not xml_files:
                print("❌ No XML files found")
                return
            
            print(f"📁 Found {len(xml_files)} XML files for data quality validation")
            
            # Process and validate each file
            for i, xml_file in enumerate(xml_files, 1):
                await self._validate_file_data_quality(xml_file, i, len(xml_files))
            
            # Generate quality report
            await self._generate_quality_report()
            
            print("\n🎉 Data Quality Validation Tests Completed!")
            
        finally:
            # Cleanup coordinator
            await self.coordinator.cleanup()
    
    async def _validate_file_data_quality(self, xml_file: Path, file_num: int, total_files: int):
        """Validate data quality for a single XML file"""
        print(f"\n📄 Validating Data Quality {file_num}/{total_files}: {xml_file.name}")
        print("-" * 70)
        
        validation_start_time = datetime.now()
        
        validation_result = {
            "filename": xml_file.name,
            "file_size": xml_file.stat().st_size,
            "timestamp": validation_start_time.isoformat(),
            "success": False,
            "validations": {},
            "total_validation_time": 0,
            "errors": []
        }
        
        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Parse XML for validation
            xml_root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Process document through dimensional pipeline first
            import uuid
            document_id = str(uuid.uuid4())
            
            print("🔄 Processing document through dimensional pipeline...")
            pipeline_result = await self.coordinator.process_document_pipeline(
                xml_content, document_id, 'NFE'
            )
            
            # Perform comprehensive data quality validations
            print("🔍 Performing Data Quality Validations...")
            
            # 1. CNPJ/CPF Format and Validation
            print("   📋 Validating CNPJ/CPF formats...")
            cnpj_validation = await self._validate_cnpj_cpf_quality(xml_root, pipeline_result)
            validation_result["validations"]["cnpj_cpf"] = cnpj_validation
            
            # 2. Financial Calculations and Totals
            print("   💰 Validating financial calculations...")
            financial_validation = await self._validate_financial_calculations(xml_root, pipeline_result)
            validation_result["validations"]["financial"] = financial_validation
            
            # 3. Data Formatting and Normalization
            print("   📝 Validating data formatting...")
            formatting_validation = await self._validate_data_formatting(xml_root, pipeline_result)
            validation_result["validations"]["formatting"] = formatting_validation
            
            # 4. Dimensional vs Fact Table Consistency
            print("   🔗 Validating table consistency...")
            consistency_validation = await self._validate_table_consistency(xml_root, pipeline_result)
            validation_result["validations"]["consistency"] = consistency_validation
            
            # 5. Business Rules Validation
            print("   📊 Validating business rules...")
            business_validation = await self._validate_business_rules(xml_root, pipeline_result)
            validation_result["validations"]["business_rules"] = business_validation
            
            # 6. Data Completeness Validation
            print("   ✅ Validating data completeness...")
            completeness_validation = await self._validate_data_completeness(xml_root, pipeline_result)
            validation_result["validations"]["completeness"] = completeness_validation
            
            # Calculate overall validation success
            all_validations = [
                cnpj_validation.get("overall_success", False),
                financial_validation.get("overall_success", False),
                formatting_validation.get("overall_success", False),
                consistency_validation.get("overall_success", False),
                business_validation.get("overall_success", False),
                completeness_validation.get("overall_success", False)
            ]
            
            validation_result["success"] = all(all_validations)
            validation_result["validation_score"] = sum(all_validations) / len(all_validations)
            
            # Calculate total validation time
            total_time = (datetime.now() - validation_start_time).total_seconds()
            validation_result["total_validation_time"] = total_time
            
            # Update metrics
            self._update_quality_metrics(validation_result)
            
            print(f"\n✅ Data Quality Validation completed in {total_time:.2f}s")
            print(f"   📊 Validation Score: {validation_result['validation_score']:.2%}")
            self._print_validation_summary(validation_result)
            
        except Exception as e:
            validation_result["errors"].append(str(e))
            print(f"❌ Data Quality Validation failed: {str(e)}")
            logger.error("Data quality validation failed", filename=xml_file.name, error=str(e))
        
        self.validation_results.append(validation_result)
    
    async def _validate_cnpj_cpf_quality(self, xml_root, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate CNPJ/CPF format, check digits, and consistency"""
        try:
            validation_result = {
                "cnpj_format_valid": False,
                "cnpj_check_digit_valid": False,
                "cpf_format_valid": True,  # Default true if no CPF
                "cpf_check_digit_valid": True,  # Default true if no CPF
                "xml_db_consistency": False,
                "validation_errors": []
            }
            
            # Extract CNPJ from XML
            xml_cnpj = self._extract_cnpj_from_xml(xml_root)
            
            # Get CNPJ from database
            dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
            db_cnpj = dimensional_result.get("emitente_id")
            
            if xml_cnpj and db_cnpj:
                # Validate CNPJ format
                cnpj_clean = re.sub(r'[^0-9]', '', xml_cnpj)
                db_cnpj_clean = re.sub(r'[^0-9]', '', db_cnpj)
                
                # Check format
                validation_result["cnpj_format_valid"] = len(cnpj_clean) == 14
                if not validation_result["cnpj_format_valid"]:
                    validation_result["validation_errors"].append(f"Invalid CNPJ length: {len(cnpj_clean)}")
                
                # Validate check digits
                validation_result["cnpj_check_digit_valid"] = self._validate_cnpj_check_digits(cnpj_clean)
                if not validation_result["cnpj_check_digit_valid"]:
                    validation_result["validation_errors"].append(f"Invalid CNPJ check digits: {cnpj_clean}")
                
                # Check XML vs DB consistency
                validation_result["xml_db_consistency"] = cnpj_clean == db_cnpj_clean
                if not validation_result["xml_db_consistency"]:
                    validation_result["validation_errors"].append(f"CNPJ mismatch: XML={cnpj_clean}, DB={db_cnpj_clean}")
            
            # Check for CPF in destinatario (if present)
            xml_cpf = self._extract_cpf_from_xml(xml_root)
            if xml_cpf:
                cpf_clean = re.sub(r'[^0-9]', '', xml_cpf)
                validation_result["cpf_format_valid"] = len(cpf_clean) == 11
                validation_result["cpf_check_digit_valid"] = self._validate_cpf_check_digits(cpf_clean)
                
                if not validation_result["cpf_format_valid"]:
                    validation_result["validation_errors"].append(f"Invalid CPF length: {len(cpf_clean)}")
                if not validation_result["cpf_check_digit_valid"]:
                    validation_result["validation_errors"].append(f"Invalid CPF check digits: {cpf_clean}")
            
            validation_result["overall_success"] = (
                validation_result["cnpj_format_valid"] and
                validation_result["cnpj_check_digit_valid"] and
                validation_result["cpf_format_valid"] and
                validation_result["cpf_check_digit_valid"] and
                validation_result["xml_db_consistency"]
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("CNPJ/CPF validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    async def _validate_financial_calculations(self, xml_root, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate financial calculations and totals accuracy"""
        try:
            validation_result = {
                "item_totals_match": False,
                "document_total_match": False,
                "tax_calculations_correct": False,
                "decimal_precision_correct": False,
                "calculation_errors": []
            }
            
            # Extract financial data from XML
            xml_financial_data = self._extract_financial_data_from_xml(xml_root)
            
            # Get financial data from database
            db_financial_data = await self._extract_financial_data_from_db(pipeline_result)
            
            # Validate item totals
            if xml_financial_data["items"] and db_financial_data["items"]:
                item_matches = 0
                total_items = len(xml_financial_data["items"])
                
                for xml_item in xml_financial_data["items"]:
                    xml_total = xml_item.get("total", 0)
                    xml_code = xml_item.get("code", "")
                    
                    # Find matching item in DB
                    db_item = next((item for item in db_financial_data["items"] 
                                  if item.get("code") == xml_code), None)
                    
                    if db_item:
                        db_total = db_item.get("total", 0)
                        
                        # Allow small differences due to decimal precision
                        if abs(float(xml_total) - float(db_total)) < 0.01:
                            item_matches += 1
                        else:
                            validation_result["calculation_errors"].append(
                                f"Item {xml_code} total mismatch: XML={xml_total}, DB={db_total}"
                            )
                
                validation_result["item_totals_match"] = item_matches == total_items
            else:
                validation_result["item_totals_match"] = True  # No items to compare
            
            # Validate document total
            xml_doc_total = xml_financial_data.get("document_total", 0)
            db_doc_total = db_financial_data.get("document_total", 0)
            
            if xml_doc_total and db_doc_total:
                validation_result["document_total_match"] = abs(float(xml_doc_total) - float(db_doc_total)) < 0.01
                
                if not validation_result["document_total_match"]:
                    validation_result["calculation_errors"].append(
                        f"Document total mismatch: XML={xml_doc_total}, DB={db_doc_total}"
                    )
            else:
                validation_result["document_total_match"] = True
            
            # Validate tax calculations (basic check)
            xml_taxes = xml_financial_data.get("taxes", {})
            db_taxes = db_financial_data.get("taxes", {})
            
            tax_matches = 0
            total_taxes = len(xml_taxes)
            
            for tax_type, xml_value in xml_taxes.items():
                db_value = db_taxes.get(tax_type, 0)
                if abs(float(xml_value) - float(db_value)) < 0.01:
                    tax_matches += 1
                else:
                    validation_result["calculation_errors"].append(
                        f"Tax {tax_type} mismatch: XML={xml_value}, DB={db_value}"
                    )
            
            validation_result["tax_calculations_correct"] = (
                tax_matches == total_taxes if total_taxes > 0 else True
            )
            
            # Check decimal precision (should be 2 decimal places for currency)
            precision_errors = 0
            for item in db_financial_data["items"]:
                total_str = str(item.get("total", "0.00"))
                if '.' in total_str:
                    decimal_places = len(total_str.split('.')[1])
                    if decimal_places > 2:
                        precision_errors += 1
            
            validation_result["decimal_precision_correct"] = precision_errors == 0
            
            validation_result["overall_success"] = (
                validation_result["item_totals_match"] and
                validation_result["document_total_match"] and
                validation_result["tax_calculations_correct"] and
                validation_result["decimal_precision_correct"]
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Financial calculations validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    async def _validate_data_formatting(self, xml_root, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data formatting and normalization"""
        try:
            validation_result = {
                "cnpj_formatting_correct": False,
                "cep_formatting_correct": False,
                "phone_formatting_correct": False,
                "text_length_limits_respected": False,
                "encoding_correct": False,
                "formatting_errors": []
            }
            
            # Get emitente data from database
            dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
            emitente_id = dimensional_result.get("emitente_id")
            
            if emitente_id:
                emitente_data = self.supabase_client.table('dim_emitente').select('*').eq('cnpj', emitente_id).execute()
                
                if emitente_data.data:
                    emitente = emitente_data.data[0]
                    
                    # Validate CNPJ formatting (XX.XXX.XXX/XXXX-XX)
                    cnpj = emitente.get('cnpj', '')
                    cnpj_pattern = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$'
                    validation_result["cnpj_formatting_correct"] = bool(re.match(cnpj_pattern, cnpj))
                    
                    if not validation_result["cnpj_formatting_correct"]:
                        validation_result["formatting_errors"].append(f"Invalid CNPJ format: {cnpj}")
                    
                    # Validate CEP formatting (XXXXXXXX or XXXXX-XXX)
                    cep = emitente.get('cep', '')
                    if cep:
                        cep_pattern = r'^\d{8}$|^\d{5}-\d{3}$'
                        validation_result["cep_formatting_correct"] = bool(re.match(cep_pattern, cep))
                        
                        if not validation_result["cep_formatting_correct"]:
                            validation_result["formatting_errors"].append(f"Invalid CEP format: {cep}")
                    else:
                        validation_result["cep_formatting_correct"] = True  # CEP is optional
                    
                    # Validate phone formatting (digits only)
                    telefone = emitente.get('telefone', '')
                    if telefone:
                        phone_pattern = r'^\d+$'
                        validation_result["phone_formatting_correct"] = bool(re.match(phone_pattern, telefone))
                        
                        if not validation_result["phone_formatting_correct"]:
                            validation_result["formatting_errors"].append(f"Invalid phone format: {telefone}")
                    else:
                        validation_result["phone_formatting_correct"] = True  # Phone is optional
                    
                    # Validate text length limits
                    length_violations = []
                    field_limits = {
                        'razao_social': 60,
                        'nome_fantasia': 60,
                        'logradouro': 60,
                        'bairro': 60,
                        'nome_municipio': 60,
                        'email': 60
                    }
                    
                    for field, limit in field_limits.items():
                        value = emitente.get(field, '')
                        if value and len(value) > limit:
                            length_violations.append(f"{field}: {len(value)} > {limit}")
                    
                    validation_result["text_length_limits_respected"] = len(length_violations) == 0
                    
                    if length_violations:
                        validation_result["formatting_errors"].extend(length_violations)
                    
                    # Check encoding (should be UTF-8 compatible)
                    encoding_errors = []
                    for field, value in emitente.items():
                        if isinstance(value, str):
                            try:
                                value.encode('utf-8')
                            except UnicodeEncodeError:
                                encoding_errors.append(f"Encoding error in field {field}")
                    
                    validation_result["encoding_correct"] = len(encoding_errors) == 0
                    
                    if encoding_errors:
                        validation_result["formatting_errors"].extend(encoding_errors)
            
            validation_result["overall_success"] = (
                validation_result["cnpj_formatting_correct"] and
                validation_result["cep_formatting_correct"] and
                validation_result["phone_formatting_correct"] and
                validation_result["text_length_limits_respected"] and
                validation_result["encoding_correct"]
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Data formatting validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    async def _validate_table_consistency(self, xml_root, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate consistency between dimensional and fact tables"""
        try:
            validation_result = {
                "dimensional_fact_consistency": False,
                "foreign_key_integrity": False,
                "data_synchronization": False,
                "consistency_errors": []
            }
            
            dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
            
            # Check dimensional to fact table consistency
            emitente_id = dimensional_result.get("emitente_id")
            produtos_count = dimensional_result.get("produtos_processed", 0)
            fact_records_count = dimensional_result.get("fact_records_created", 0)
            
            # Validate that fact records reference existing dimensional records
            if fact_records_count > 0:
                # Check fact_itens_nfe table
                fact_items = self.supabase_client.table('fact_itens_nfe').select('codigo_produto').limit(100).execute()
                
                foreign_key_errors = 0
                for fact_item in fact_items.data:
                    produto_code = fact_item.get('codigo_produto')
                    if produto_code:
                        produto_exists = self.supabase_client.table('dim_produtos').select('codigo_produto').eq('codigo_produto', produto_code).execute()
                        if not produto_exists.data:
                            foreign_key_errors += 1
                            validation_result["consistency_errors"].append(f"Fact item references non-existent product: {produto_code}")
                
                validation_result["foreign_key_integrity"] = foreign_key_errors == 0
            else:
                validation_result["foreign_key_integrity"] = True  # No fact records to validate
            
            # Check data synchronization (timestamps should be recent)
            if emitente_id:
                emitente_data = self.supabase_client.table('dim_emitente').select('updated_at').eq('cnpj', emitente_id).execute()
                if emitente_data.data:
                    updated_at = emitente_data.data[0].get('updated_at')
                    if updated_at:
                        # Check if updated recently (within last hour)
                        from datetime import datetime, timezone, timedelta
                        update_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        current_time = datetime.now(timezone.utc)
                        time_diff = current_time - update_time
                        
                        validation_result["data_synchronization"] = time_diff < timedelta(hours=1)
                        
                        if not validation_result["data_synchronization"]:
                            validation_result["consistency_errors"].append(f"Data not recently synchronized: {time_diff}")
            
            # Overall dimensional-fact consistency
            validation_result["dimensional_fact_consistency"] = (
                produtos_count > 0 and fact_records_count > 0 and
                validation_result["foreign_key_integrity"]
            )
            
            validation_result["overall_success"] = (
                validation_result["dimensional_fact_consistency"] and
                validation_result["foreign_key_integrity"] and
                validation_result["data_synchronization"]
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Table consistency validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    async def _validate_business_rules(self, xml_root, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Brazilian business rules and fiscal requirements"""
        try:
            validation_result = {
                "ncm_codes_valid": False,
                "cfop_codes_valid": False,
                "tax_rates_reasonable": False,
                "business_logic_correct": False,
                "business_errors": []
            }
            
            # Get produtos data for validation
            dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
            produtos_count = dimensional_result.get("produtos_processed", 0)
            
            if produtos_count > 0:
                produtos_data = self.supabase_client.table('dim_produtos').select('*').limit(100).execute()
                
                ncm_valid_count = 0
                cfop_valid_count = 0
                total_produtos = len(produtos_data.data)
                
                for produto in produtos_data.data:
                    # Validate NCM codes (8 digits)
                    ncm = produto.get('ncm', '')
                    if ncm:
                        if re.match(r'^\d{8}$', ncm):
                            ncm_valid_count += 1
                        else:
                            validation_result["business_errors"].append(f"Invalid NCM format: {ncm}")
                    
                    # Validate CFOP codes (4 digits)
                    cfop = produto.get('cfop', '')
                    if cfop:
                        if re.match(r'^\d{4}$', cfop):
                            cfop_valid_count += 1
                        else:
                            validation_result["business_errors"].append(f"Invalid CFOP format: {cfop}")
                
                validation_result["ncm_codes_valid"] = ncm_valid_count == total_produtos if total_produtos > 0 else True
                validation_result["cfop_codes_valid"] = cfop_valid_count == total_produtos if total_produtos > 0 else True
            else:
                validation_result["ncm_codes_valid"] = True
                validation_result["cfop_codes_valid"] = True
            
            # Validate tax rates (should be reasonable percentages)
            fact_items = self.supabase_client.table('fact_itens_nfe').select('valor_total_bruto, valor_unitario_comercial, quantidade_comercial').limit(50).execute()
            
            reasonable_tax_count = 0
            total_items = len(fact_items.data)
            
            for item in fact_items.data:
                valor_total = float(item.get('valor_total_bruto', 0))
                valor_unitario = float(item.get('valor_unitario_comercial', 0))
                quantidade = float(item.get('quantidade_comercial', 0))
                
                # Basic business logic: total should equal unit price * quantity (approximately)
                if quantidade > 0 and valor_unitario > 0:
                    expected_total = valor_unitario * quantidade
                    if abs(valor_total - expected_total) / expected_total < 0.05:  # 5% tolerance
                        reasonable_tax_count += 1
                    else:
                        validation_result["business_errors"].append(
                            f"Business logic error: total={valor_total}, expected={expected_total}"
                        )
            
            validation_result["tax_rates_reasonable"] = reasonable_tax_count == total_items if total_items > 0 else True
            validation_result["business_logic_correct"] = reasonable_tax_count == total_items if total_items > 0 else True
            
            validation_result["overall_success"] = (
                validation_result["ncm_codes_valid"] and
                validation_result["cfop_codes_valid"] and
                validation_result["tax_rates_reasonable"] and
                validation_result["business_logic_correct"]
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Business rules validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    async def _validate_data_completeness(self, xml_root, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data completeness and required field presence"""
        try:
            validation_result = {
                "required_fields_present": False,
                "optional_fields_reasonable": False,
                "data_coverage_adequate": False,
                "completeness_errors": []
            }
            
            dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
            emitente_id = dimensional_result.get("emitente_id")
            
            # Check required fields in emitente
            if emitente_id:
                emitente_data = self.supabase_client.table('dim_emitente').select('*').eq('cnpj', emitente_id).execute()
                
                if emitente_data.data:
                    emitente = emitente_data.data[0]
                    
                    # Required fields
                    required_fields = ['cnpj', 'razao_social']
                    missing_required = []
                    
                    for field in required_fields:
                        if not emitente.get(field):
                            missing_required.append(field)
                    
                    validation_result["required_fields_present"] = len(missing_required) == 0
                    
                    if missing_required:
                        validation_result["completeness_errors"].extend([f"Missing required field: {field}" for field in missing_required])
                    
                    # Optional fields coverage
                    optional_fields = ['nome_fantasia', 'logradouro', 'bairro', 'nome_municipio', 'uf', 'cep']
                    present_optional = sum(1 for field in optional_fields if emitente.get(field))
                    
                    validation_result["optional_fields_reasonable"] = present_optional >= len(optional_fields) * 0.5  # At least 50% coverage
                    
                    if not validation_result["optional_fields_reasonable"]:
                        validation_result["completeness_errors"].append(f"Low optional field coverage: {present_optional}/{len(optional_fields)}")
            
            # Check data coverage for produtos
            produtos_count = dimensional_result.get("produtos_processed", 0)
            fact_records_count = dimensional_result.get("fact_records_created", 0)
            
            validation_result["data_coverage_adequate"] = (
                produtos_count > 0 and fact_records_count > 0 and
                fact_records_count >= produtos_count  # At least one fact record per product
            )
            
            if not validation_result["data_coverage_adequate"]:
                validation_result["completeness_errors"].append(
                    f"Inadequate data coverage: {produtos_count} products, {fact_records_count} fact records"
                )
            
            validation_result["overall_success"] = (
                validation_result["required_fields_present"] and
                validation_result["optional_fields_reasonable"] and
                validation_result["data_coverage_adequate"]
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Data completeness validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    # Helper methods for data extraction and validation
    
    def _extract_cnpj_from_xml(self, xml_root) -> Optional[str]:
        """Extract CNPJ from XML emitente"""
        try:
            emit = xml_root.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
            if emit is not None:
                cnpj_elem = emit.find('.//{http://www.portalfiscal.inf.br/nfe}CNPJ')
                return cnpj_elem.text if cnpj_elem is not None else None
            return None
        except Exception:
            return None
    
    def _extract_cpf_from_xml(self, xml_root) -> Optional[str]:
        """Extract CPF from XML destinatario"""
        try:
            dest = xml_root.find('.//{http://www.portalfiscal.inf.br/nfe}dest')
            if dest is not None:
                cpf_elem = dest.find('.//{http://www.portalfiscal.inf.br/nfe}CPF')
                return cpf_elem.text if cpf_elem is not None else None
            return None
        except Exception:
            return None
    
    def _validate_cnpj_check_digits(self, cnpj: str) -> bool:
        """Validate CNPJ check digits using Brazilian algorithm"""
        try:
            if len(cnpj) != 14:
                return False
            
            # Calculate first check digit
            weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
            remainder1 = sum1 % 11
            digit1 = 0 if remainder1 < 2 else 11 - remainder1
            
            # Calculate second check digit
            weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
            remainder2 = sum2 % 11
            digit2 = 0 if remainder2 < 2 else 11 - remainder2
            
            return int(cnpj[12]) == digit1 and int(cnpj[13]) == digit2
            
        except Exception:
            return False
    
    def _validate_cpf_check_digits(self, cpf: str) -> bool:
        """Validate CPF check digits using Brazilian algorithm"""
        try:
            if len(cpf) != 11:
                return False
            
            # Calculate first check digit
            sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
            remainder1 = sum1 % 11
            digit1 = 0 if remainder1 < 2 else 11 - remainder1
            
            # Calculate second check digit
            sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
            remainder2 = sum2 % 11
            digit2 = 0 if remainder2 < 2 else 11 - remainder2
            
            return int(cpf[9]) == digit1 and int(cpf[10]) == digit2
            
        except Exception:
            return False
    
    def _extract_financial_data_from_xml(self, xml_root) -> Dict[str, Any]:
        """Extract financial data from XML for comparison"""
        try:
            financial_data = {
                "items": [],
                "document_total": 0,
                "taxes": {}
            }
            
            # Extract items
            det_elements = xml_root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
            for det in det_elements:
                prod = det.find('.//{http://www.portalfiscal.inf.br/nfe}prod')
                if prod is not None:
                    code_elem = prod.find('.//{http://www.portalfiscal.inf.br/nfe}cProd')
                    total_elem = prod.find('.//{http://www.portalfiscal.inf.br/nfe}vProd')
                    
                    if code_elem is not None and total_elem is not None:
                        financial_data["items"].append({
                            "code": code_elem.text,
                            "total": Decimal(total_elem.text or '0')
                        })
            
            # Extract document total
            total_elem = xml_root.find('.//{http://www.portalfiscal.inf.br/nfe}vNF')
            if total_elem is not None:
                financial_data["document_total"] = Decimal(total_elem.text or '0')
            
            return financial_data
            
        except Exception as e:
            logger.error("Failed to extract financial data from XML", error=str(e))
            return {"items": [], "document_total": 0, "taxes": {}}
    
    async def _extract_financial_data_from_db(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract financial data from database for comparison"""
        try:
            financial_data = {
                "items": [],
                "document_total": 0,
                "taxes": {}
            }
            
            # Get fact records
            fact_records = self.supabase_client.table('fact_itens_nfe').select('codigo_produto, valor_total_bruto').execute()
            
            for record in fact_records.data:
                financial_data["items"].append({
                    "code": record.get('codigo_produto'),
                    "total": Decimal(str(record.get('valor_total_bruto', 0)))
                })
            
            # Calculate document total from items
            financial_data["document_total"] = sum(item["total"] for item in financial_data["items"])
            
            return financial_data
            
        except Exception as e:
            logger.error("Failed to extract financial data from DB", error=str(e))
            return {"items": [], "document_total": 0, "taxes": {}}
    
    def _update_quality_metrics(self, validation_result: Dict[str, Any]):
        """Update quality metrics with validation results"""
        self.quality_metrics['total_validations'] += 1
        
        validations = validation_result.get("validations", {})
        
        # Count specific validation types
        if validations.get("cnpj_cpf"):
            self.quality_metrics['cnpj_validations'] += 1
        
        if validations.get("financial"):
            self.quality_metrics['financial_validations'] += 1
        
        if validations.get("formatting"):
            self.quality_metrics['formatting_validations'] += 1
        
        if validations.get("consistency"):
            self.quality_metrics['consistency_validations'] += 1
        
        # Count overall success/failure
        if validation_result.get("success"):
            self.quality_metrics['passed_validations'] += 1
        else:
            self.quality_metrics['failed_validations'] += 1
    
    def _print_validation_summary(self, validation_result: Dict[str, Any]):
        """Print summary of validation results"""
        validations = validation_result.get("validations", {})
        
        print(f"   🔍 Validation Results:")
        print(f"     CNPJ/CPF: {'✅' if validations.get('cnpj_cpf', {}).get('overall_success') else '❌'}")
        print(f"     Financial: {'✅' if validations.get('financial', {}).get('overall_success') else '❌'}")
        print(f"     Formatting: {'✅' if validations.get('formatting', {}).get('overall_success') else '❌'}")
        print(f"     Consistency: {'✅' if validations.get('consistency', {}).get('overall_success') else '❌'}")
        print(f"     Business Rules: {'✅' if validations.get('business_rules', {}).get('overall_success') else '❌'}")
        print(f"     Completeness: {'✅' if validations.get('completeness', {}).get('overall_success') else '❌'}")
    
    async def _generate_quality_report(self):
        """Generate comprehensive data quality report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE DATA QUALITY VALIDATION REPORT")
        print("=" * 80)
        
        total_validations = len(self.validation_results)
        successful_validations = sum(1 for r in self.validation_results if r.get("success", False))
        failed_validations = total_validations - successful_validations
        
        print(f"📁 Total Files Validated: {total_validations}")
        print(f"✅ Successful Validations: {successful_validations}")
        print(f"❌ Failed Validations: {failed_validations}")
        print(f"📈 Overall Success Rate: {(successful_validations/total_validations*100):.1f}%")
        
        if successful_validations > 0:
            # Calculate average validation score
            validation_scores = [r.get("validation_score", 0) for r in self.validation_results if r.get("success")]
            avg_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
            
            print(f"\n📊 Quality Metrics:")
            print(f"   Average Validation Score: {avg_score:.2%}")
            print(f"   CNPJ Validations: {self.quality_metrics['cnpj_validations']}")
            print(f"   Financial Validations: {self.quality_metrics['financial_validations']}")
            print(f"   Formatting Validations: {self.quality_metrics['formatting_validations']}")
            print(f"   Consistency Validations: {self.quality_metrics['consistency_validations']}")
            
            # Validation type success rates
            validation_types = ['cnpj_cpf', 'financial', 'formatting', 'consistency', 'business_rules', 'completeness']
            
            print(f"\n🔍 Validation Type Success Rates:")
            for val_type in validation_types:
                successes = sum(1 for r in self.validation_results 
                              if r.get("success") and 
                              r.get("validations", {}).get(val_type, {}).get("overall_success"))
                rate = (successes / successful_validations * 100) if successful_validations > 0 else 0
                print(f"   {val_type.replace('_', ' ').title()}: {rate:.1f}%")
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_quality_validation_results_{timestamp}.json"
        
        try:
            comprehensive_results = {
                "validation_results": self.validation_results,
                "quality_metrics": self.quality_metrics,
                "summary": {
                    "total_validations": total_validations,
                    "successful_validations": successful_validations,
                    "failed_validations": failed_validations,
                    "success_rate": (successful_validations/total_validations*100) if total_validations > 0 else 0,
                    "average_validation_score": avg_score if successful_validations > 0 else 0
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Comprehensive results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results to file: {str(e)}")


async def main():
    """Main test execution"""
    print("🔍 Data Quality Validation Test Suite")
    print("=" * 80)
    
    validator = DataQualityValidator()
    await validator.run_data_quality_validation_tests()


if __name__ == "__main__":
    asyncio.run(main())