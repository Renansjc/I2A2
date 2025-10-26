# Dimensional Processing Test Suite

This directory contains comprehensive tests for the dimensional processing pipeline using real XML data from Brazilian fiscal documents.

## Test Files Created

### 1. End-to-End Processing Tests
**File:** `test_dimensional_end_to_end_real_data.py`

Tests the complete dimensional processing pipeline:
- XML processing and data extraction
- AI categorization integration
- Dimensional table population
- Fact table creation
- Referential integrity validation

**Features:**
- Processes all XML files from `xml_nf/` directory
- Validates data extraction accuracy
- Checks categorization results
- Verifies referential integrity
- Generates comprehensive reports

### 2. Data Quality Validation Tests
**File:** `test_dimensional_data_quality_validation.py`

Validates data quality by comparing extracted data with original XML:
- CNPJ/CPF format and check digit validation
- Financial calculations accuracy
- Data formatting and normalization
- Table consistency checks
- Brazilian business rules validation
- Data completeness verification

**Features:**
- Compares XML data with database records
- Validates Brazilian tax document formats
- Checks calculation accuracy
- Verifies business logic compliance

### 3. Performance and Load Tests
**File:** `test_dimensional_performance_load.py`

Tests system performance under various conditions:
- Single document processing performance
- Concurrent processing capabilities
- Memory usage patterns
- Load testing with multiple simulated users
- Stress testing to find system limits

**Features:**
- Performance monitoring with CPU and memory tracking
- Concurrent processing tests
- Load testing with multiple users
- Stress testing capabilities
- Performance recommendations

### 4. Comprehensive Test Runner
**File:** `run_dimensional_tests.py`

Executes all test suites in sequence and generates overall summary:
- Runs all three test phases
- Generates comprehensive reports
- Provides overall recommendations
- Saves detailed results to JSON files

## How to Run the Tests

### Prerequisites

1. Ensure you have the dimensional processing agents implemented:
   - `agents/dimensional_processing_agent.py`
   - `agents/dimensional_coordinator.py`

2. Have XML files in the `xml_nf/` directory (6 files are available)

3. Database connection configured (Supabase)

4. Required Python packages installed:
   ```bash
   pip install psutil lxml structlog
   ```

### Running Individual Test Suites

#### 1. End-to-End Processing Tests
```bash
python test_dimensional_end_to_end_real_data.py
```

#### 2. Data Quality Validation Tests
```bash
python test_dimensional_data_quality_validation.py
```

#### 3. Performance and Load Tests
```bash
python test_dimensional_performance_load.py
```

### Running Complete Test Suite
```bash
python run_dimensional_tests.py
```

This will run all tests in sequence and generate a comprehensive report.

## Test Results

Each test suite generates detailed JSON reports with timestamps:

- `dimensional_end_to_end_results_YYYYMMDD_HHMMSS.json`
- `data_quality_validation_results_YYYYMMDD_HHMMSS.json`
- `dimensional_performance_load_results_YYYYMMDD_HHMMSS.json`
- `dimensional_test_suite_results_YYYYMMDD_HHMMSS.json` (comprehensive)

## Expected Test Coverage

### End-to-End Tests Validate:
- ✅ Document processing through complete pipeline
- ✅ Emitente data extraction and storage
- ✅ Destinatário data processing (when present)
- ✅ Product/service categorization
- ✅ Fact table population
- ✅ Referential integrity

### Data Quality Tests Validate:
- ✅ CNPJ/CPF format and check digits
- ✅ Financial calculation accuracy
- ✅ Data normalization and formatting
- ✅ Table consistency
- ✅ Brazilian business rules compliance
- ✅ Data completeness

### Performance Tests Validate:
- ✅ Single document processing speed
- ✅ Concurrent processing capabilities
- ✅ Memory usage patterns
- ✅ System behavior under load
- ✅ Stress testing limits

## Test Files Available

### 1. Basic Dimensional Processing Test (RECOMMENDED)
**File:** `test_dimensional_basic.py`

**Status:** ✅ Working - Tests core functionality without database dependencies

Tests XML parsing and data extraction:
- XML parsing and validation
- Data extraction from fiscal documents
- Data normalization and formatting
- Basic categorization logic
- Data validation and integrity checks

**Usage:**
```bash
python test_dimensional_basic.py
```

This test is ideal for:
- Validating core XML processing functionality
- Testing without database setup requirements
- Quick validation of data extraction logic
- Development and debugging

### 2. End-to-End Processing Tests
**File:** `test_dimensional_end_to_end_real_data.py`

**Status:** ⚠️ Requires database setup and fiscal_documents table population

### 3. Data Quality Validation Tests
**File:** `test_dimensional_data_quality_validation.py`

**Status:** ⚠️ Requires database setup and fiscal_documents table population

### 4. Performance and Load Tests
**File:** `test_dimensional_performance_load.py`

**Status:** ⚠️ Requires database setup and fiscal_documents table population

## Troubleshooting

### Common Issues

1. **XML files not found**
   - Ensure XML files are in `xml_nf/` directory
   - Check file permissions

2. **Database connection errors (for full tests)**
   - Verify Supabase configuration
   - Check environment variables
   - Ensure fiscal_documents table is populated first

3. **Import errors**
   - Ensure all required agents are implemented
   - Check Python path configuration

4. **Memory issues during performance tests**
   - Reduce concurrency levels in performance tests
   - Monitor system resources

5. **UUID/Document ID errors**
   - The system expects documents to exist in fiscal_documents table first
   - Use the basic test for core functionality validation
   - For full pipeline tests, ensure proper document upload workflow

### Performance Expectations

- **Single document processing:** 2-10 seconds per document
- **Memory usage:** 50-200 MB peak during processing
- **Concurrent processing:** Should handle 3-5 documents simultaneously
- **Success rate:** Target >80% for end-to-end processing

## Test Results Interpretation

### Success Criteria

- **End-to-End Success Rate:** >80%
- **Data Quality Validation Rate:** >90%
- **Performance:** <10 seconds average processing time
- **Memory Efficiency:** <500 MB peak usage
- **Concurrent Processing:** >80% success rate with 3+ concurrent documents

### Failure Investigation

If tests fail, check:
1. Database connectivity and permissions
2. XML file format and content
3. Agent implementation completeness
4. System resource availability
5. Configuration settings

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```bash
# Quick validation (end-to-end only)
python test_dimensional_end_to_end_real_data.py

# Full validation (all tests)
python run_dimensional_tests.py
```

## Maintenance

- Update test data when XML schemas change
- Adjust performance expectations based on hardware
- Review and update validation rules for new business requirements
- Monitor test execution times and optimize as needed

## Support

For issues with the dimensional processing tests:
1. Check the generated JSON reports for detailed error information
2. Review the console output for specific failure points
3. Verify all prerequisites are met
4. Check system resources during test execution