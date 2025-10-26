# LLM Integration Testing Suite

## Overview

This comprehensive testing suite validates all LLM-powered functionality across the AI Agents Invoice Analysis System. It includes tests for prompt effectiveness, context preservation, business logic accuracy, and end-to-end workflow validation.

## Test Suites

### 1. LLM Integration Test Suite (`test_llm_integration_suite.py`)

Tests core LLM functionality across all agents:

- **Master Agent Query Interpretation**: Validates natural language understanding and intent recognition
- **SQL Agent Business Translation**: Tests business-to-SQL translation accuracy and logic preservation
- **Report Agent Insight Generation**: Validates intelligent report generation and business relevance

**Key Metrics:**
- Query interpretation accuracy (target: ≥70%)
- SQL translation confidence (target: ≥70%)
- Business logic preservation (target: ≥80%)
- Insight quality and relevance (target: ≥70%)

### 2. Prompt Effectiveness Test Suite (`test_prompt_effectiveness.py`)

Tests prompt template quality and optimization:

- **Template Rendering**: Validates prompt template completeness and variable substitution
- **Context Preservation**: Tests conversation context management and memory efficiency
- **Optimization Effectiveness**: Compares base vs optimized prompt performance

**Key Metrics:**
- Template quality score (target: ≥70%)
- Context preservation accuracy (target: ≥80%)
- Optimization improvement (target: ≥20%)

### 3. End-to-End Integration Test Suite (`test_end_to_end_integration.py`)

Tests complete workflows from query to report:

- **Supplier Analysis Workflow**: Complete supplier analysis from query to executive report
- **Tax Analysis Workflow**: Tax optimization analysis with ICMS/ISS focus
- **Portuguese Interface Integration**: Brazilian Portuguese language preservation

**Key Metrics:**
- Workflow completion rate (target: ≥80%)
- Portuguese language preservation (target: ≥70%)
- End-to-end execution time (target: ≤30s)

### 4. Comprehensive Test Runner (`test_comprehensive_llm_suite.py`)

Orchestrates all test suites and generates detailed reports:

- Runs all test categories with configurable options
- Generates comprehensive performance and quality metrics
- Provides actionable recommendations for improvement
- Saves detailed results to JSON files

## Usage

### Running Individual Test Suites

```bash
# Run LLM integration tests
python test_llm_integration_suite.py

# Run prompt effectiveness tests
python test_prompt_effectiveness.py

# Run end-to-end integration tests
python test_end_to_end_integration.py
```

### Running Comprehensive Test Suite

```bash
# Run all tests
python test_comprehensive_llm_suite.py

# Run specific test categories
python test_comprehensive_llm_suite.py --categories integration prompts

# Run with custom configuration
python test_comprehensive_llm_suite.py --config-file test_config.json
```

### Configuration Options

The test suite supports configuration via `test_config.json`:

```json
{
  "save_results": true,
  "test_timeout": 300,
  "performance_thresholds": {
    "query_interpretation_max_time": 5.0,
    "sql_translation_max_time": 8.0,
    "report_generation_max_time": 15.0
  },
  "quality_thresholds": {
    "minimum_accuracy_score": 0.7,
    "minimum_business_relevance": 0.8
  }
}
```

## Test Results Interpretation

### Success Criteria

- **Excellent (≥90%)**: Production-ready with high confidence
- **Very Good (≥80%)**: Production-ready with monitoring
- **Good (≥70%)**: Functional with room for improvement
- **Moderate (≥50%)**: Needs optimization before production
- **Poor (<50%)**: Requires major improvements

### Key Performance Indicators

1. **Overall Success Rate**: Percentage of tests passing across all suites
2. **Average Accuracy**: Mean accuracy score across all LLM operations
3. **Business Logic Preservation**: How well business context is maintained
4. **Portuguese Language Support**: Accuracy of Brazilian Portuguese processing
5. **Execution Performance**: Average response times for different operations

## Fallback Testing

The test suite includes fallback mechanisms for environments without OpenAI API access:

- Mock LLM responses for basic functionality testing
- Rule-based validation for business logic testing
- Template rendering validation without API calls
- Performance benchmarking with simulated data

## Troubleshooting

### Common Issues

1. **OpenAI API Key Not Configured**
   - Tests will use fallback mechanisms
   - Configure `OPENAI_API_KEY` environment variable for full testing

2. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify Python path includes backend directory

3. **Test Timeouts**
   - Adjust timeout values in `test_config.json`
   - Check network connectivity for API calls

4. **Low Success Rates**
   - Review prompt templates for optimization opportunities
   - Check agent initialization and configuration
   - Validate business logic implementation

## Integration with CI/CD

The test suite returns appropriate exit codes for CI/CD integration:

- **Exit Code 0**: Tests passed (≥70% success rate)
- **Exit Code 1**: Tests failed (<70% success rate)

Example GitHub Actions integration:

```yaml
- name: Run LLM Integration Tests
  run: |
    cd backend
    python test_comprehensive_llm_suite.py
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

## Extending the Test Suite

### Adding New Test Cases

1. **Agent-Specific Tests**: Add test methods to respective agent test files
2. **Business Scenario Tests**: Create new test cases in end-to-end suite
3. **Prompt Variations**: Add prompt optimization tests for new templates

### Custom Metrics

Implement custom evaluation functions:

```python
def _evaluate_custom_metric(self, result, expected) -> float:
    """Custom evaluation logic"""
    # Implementation here
    return score
```

## Performance Benchmarks

### Target Performance Metrics

- Query Interpretation: ≤5 seconds
- SQL Translation: ≤8 seconds  
- Report Generation: ≤15 seconds
- End-to-End Workflow: ≤30 seconds

### Quality Benchmarks

- Business Logic Accuracy: ≥80%
- Portuguese Language Preservation: ≥70%
- Context Preservation: ≥80%
- Prompt Template Quality: ≥70%

## Monitoring and Alerting

The test suite generates metrics suitable for monitoring:

- Success rates by agent and operation type
- Performance trends over time
- Error patterns and frequency
- Business accuracy degradation alerts

Results can be integrated with monitoring systems like Prometheus, Grafana, or custom dashboards.