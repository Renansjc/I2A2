#!/usr/bin/env python3
"""
Prompt Effectiveness and Context Preservation Testing
Tests the quality and effectiveness of LLM prompts across different scenarios
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import settings
from utils.openai_integration import OpenAIIntegrationService
from utils.prompt_manager import gerenciador_prompts
from utils.context_manager import GerenciadorContexto

import structlog
logger = structlog.get_logger(__name__)

@dataclass
class PromptTestCase:
    """Test case for prompt effectiveness"""
    template_name: str
    variables: Dict[str, Any]
    expected_elements: List[str]
    business_context: Dict[str, Any]
    quality_criteria: Dict[str, float]

@dataclass
class ContextTestCase:
    """Test case for context preservation"""
    conversation_history: List[Dict[str, Any]]
    new_query: str
    expected_context_elements: List[str]
    context_window_size: int

class PromptEffectivenessTestSuite:
    """Test suite for prompt effectiveness and context preservation"""
    
    def __init__(self):
        self.llm_service = None
        self.context_manager = None
        self.test_results = {}
        
    async def initialize(self):
        """Initialize test suite components"""
        try:
            if settings.OPENAI_API_KEY:
                self.llm_service = OpenAIIntegrationService()
                self.context_manager = GerenciadorContexto()
                logger.info("Prompt testing components initialized")
            else:
                logger.warning("OpenAI API key not configured - using mock testing")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
    
    async def test_prompt_template_rendering(self) -> Dict[str, Any]:
        """Test prompt template rendering accuracy and completeness"""
        print("\n📝 Testing Prompt Template Rendering...")
        
        test_cases = [
            PromptTestCase(
                template_name="master_agent_interpretacao_consulta",
                variables={
                    "consulta": "Quais foram os maiores fornecedores no último trimestre?",
                    "cargo_usuario": "CEO",
                    "contexto_empresarial": {"setor": "industrial", "foco": "otimização"},
                    "dados_disponiveis": ["nfe", "nfse", "fornecedores"],
                    "historico_conversa": []
                },
                expected_elements=["consulta", "cargo", "contexto", "dados", "análise"],
                business_context={"user_role": "executive", "domain": "fiscal"},
                quality_criteria={"completeness": 0.8, "clarity": 0.7, "business_relevance": 0.8}
            ),
            PromptTestCase(
                template_name="categorizacao_produtos",
                variables={
                    "itens": ["Açúcar cristal especial", "Notebook Dell Inspiron"],
                    "tipo_categoria": "produto",
                    "contexto_empresarial": {"setor": "varejo", "fornecedor": "Distribuidora ABC"}
                },
                expected_elements=["produtos", "categorização", "contexto", "critérios"],
                business_context={"user_role": "analyst", "domain": "categorization"},
                quality_criteria={"completeness": 0.9, "clarity": 0.8, "business_relevance": 0.9}
            ),
            PromptTestCase(
                template_name="traducao_consulta_sql",
                variables={
                    "consulta_natural": "Mostre os fornecedores com mais de R$ 50.000 em vendas",
                    "schema_banco": {"tables": ["fornecedores", "documentos_fiscais"]},
                    "regras_negocio": ["valor_minimo_analise: 50000"],
                    "cargo_usuario": "analista"
                },
                expected_elements=["consulta", "schema", "regras", "sql", "lógica"],
                business_context={"user_role": "analyst", "domain": "sql_generation"},
                quality_criteria={"completeness": 0.9, "clarity": 0.8, "technical_accuracy": 0.9}
            )
        ]
        
        results = {
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "template_scores": {},
            "rendering_times": [],
            "quality_assessments": []
        }
        
        for i, test_case in enumerate(test_cases):
            start_time = time.time()
            
            try:
                # Render template
                rendered_prompt, errors = gerenciador_prompts.renderizar_template(
                    test_case.template_name,
                    test_case.variables
                )
                
                rendering_time = time.time() - start_time
                results["rendering_times"].append(rendering_time)
                
                if errors:
                    results["failed"] += 1
                    print(f"   ❌ Template {test_case.template_name}: Rendering errors - {errors}")
                    continue
                
                # Evaluate prompt quality
                quality_score = self._evaluate_prompt_quality(rendered_prompt, test_case)
                results["template_scores"][test_case.template_name] = quality_score
                
                # Assess business context integration
                context_integration = self._assess_business_context_integration(
                    rendered_prompt, test_case.business_context
                )
                results["quality_assessments"].append({
                    "template": test_case.template_name,
                    "quality_score": quality_score,
                    "context_integration": context_integration,
                    "rendering_time": rendering_time
                })
                
                if quality_score >= 0.7:
                    results["passed"] += 1
                    print(f"   ✅ Template {test_case.template_name}: Quality {quality_score:.2f}")
                else:
                    results["failed"] += 1
                    print(f"   ❌ Template {test_case.template_name}: Quality {quality_score:.2f}")
                    
            except Exception as e:
                results["failed"] += 1
                print(f"   ❌ Template {test_case.template_name}: Error - {str(e)}")
        
        # Calculate averages
        results["average_quality"] = sum(results["template_scores"].values()) / len(results["template_scores"]) if results["template_scores"] else 0
        results["average_rendering_time"] = sum(results["rendering_times"]) / len(results["rendering_times"]) if results["rendering_times"] else 0
        
        print(f"   📊 Results: {results['passed']}/{results['total_tests']} templates passed")
        print(f"   🎯 Average quality: {results['average_quality']:.2f}")
        print(f"   ⏱️  Average rendering time: {results['average_rendering_time']:.3f}s")
        
        return results
    
    async def test_context_preservation(self) -> Dict[str, Any]:
        """Test conversation context preservation across interactions"""
        print("\n🧠 Testing Context Preservation...")
        
        test_cases = [
            ContextTestCase(
                conversation_history=[
                    {"role": "user", "content": "Mostre os fornecedores do último trimestre", "timestamp": datetime.now()},
                    {"role": "assistant", "content": "Aqui estão os principais fornecedores...", "timestamp": datetime.now()},
                    {"role": "user", "content": "Qual foi o valor total?", "timestamp": datetime.now()}
                ],
                new_query="E qual foi o ICMS pago?",
                expected_context_elements=["fornecedores", "último trimestre", "valor total", "ICMS"],
                context_window_size=3
            ),
            ContextTestCase(
                conversation_history=[
                    {"role": "user", "content": "Preciso de um relatório de impostos", "timestamp": datetime.now()},
                    {"role": "assistant", "content": "Que tipo de relatório de impostos?", "timestamp": datetime.now()},
                    {"role": "user", "content": "ICMS por estado", "timestamp": datetime.now()}
                ],
                new_query="Inclua também o período de janeiro a março",
                expected_context_elements=["relatório", "impostos", "ICMS", "estado", "período"],
                context_window_size=3
            )
        ]
        
        results = {
            "total_tests": len(test_cases),
            "passed": 0,
            "failed": 0,
            "context_preservation_scores": [],
            "context_retrieval_times": [],
            "memory_efficiency_scores": []
        }
        
        if not self.context_manager:
            print("   ⚠️ Context manager not available - skipping context tests")
            return results
        
        for i, test_case in enumerate(test_cases):
            start_time = time.time()
            
            try:
                # Set up conversation context
                session_id = f"test_session_{i}"
                user_id = f"test_user_{i}"
                
                # Add conversation history
                for message in test_case.conversation_history:
                    await self.context_manager.adicionar_interacao(
                        user_id, session_id, message["content"], message.get("role", "user")
                    )
                
                # Retrieve context for new query
                context = await self.context_manager.obter_contexto_conversa(
                    user_id, session_id, test_case.context_window_size
                )
                
                retrieval_time = time.time() - start_time
                results["context_retrieval_times"].append(retrieval_time)
                
                # Evaluate context preservation
                preservation_score = self._evaluate_context_preservation(context, test_case)
                results["context_preservation_scores"].append(preservation_score)
                
                # Evaluate memory efficiency
                memory_score = self._evaluate_memory_efficiency(context, test_case)
                results["memory_efficiency_scores"].append(memory_score)
                
                if preservation_score >= 0.7:
                    results["passed"] += 1
                    print(f"   ✅ Context Test {i+1}: Preservation {preservation_score:.2f}")
                else:
                    results["failed"] += 1
                    print(f"   ❌ Context Test {i+1}: Preservation {preservation_score:.2f}")
                    
            except Exception as e:
                results["failed"] += 1
                print(f"   ❌ Context Test {i+1}: Error - {str(e)}")
        
        # Calculate averages
        results["average_preservation"] = sum(results["context_preservation_scores"]) / len(results["context_preservation_scores"]) if results["context_preservation_scores"] else 0
        results["average_retrieval_time"] = sum(results["context_retrieval_times"]) / len(results["context_retrieval_times"]) if results["context_retrieval_times"] else 0
        results["average_memory_efficiency"] = sum(results["memory_efficiency_scores"]) / len(results["memory_efficiency_scores"]) if results["memory_efficiency_scores"] else 0
        
        print(f"   📊 Results: {results['passed']}/{results['total_tests']} context tests passed")
        print(f"   🧠 Average preservation: {results['average_preservation']:.2f}")
        print(f"   ⏱️  Average retrieval time: {results['average_retrieval_time']:.3f}s")
        print(f"   💾 Memory efficiency: {results['average_memory_efficiency']:.2f}")
        
        return results
    
    async def test_prompt_optimization_effectiveness(self) -> Dict[str, Any]:
        """Test the effectiveness of prompt optimization techniques"""
        print("\n⚡ Testing Prompt Optimization Effectiveness...")
        
        # Test different prompt variations for the same task
        optimization_tests = [
            {
                "base_prompt": "Categorize this product: {product}",
                "optimized_prompt": "Você é um especialista em categorização de produtos brasileiros. Analise o produto '{product}' considerando: 1) Descrição técnica, 2) Uso empresarial, 3) Categoria fiscal NCM. Forneça categorização detalhada com justificativa.",
                "test_input": {"product": "Açúcar cristal especial 1kg"},
                "evaluation_criteria": ["specificity", "context_awareness", "actionability"]
            },
            {
                "base_prompt": "Convert to SQL: {query}",
                "optimized_prompt": "Você é um especialista em SQL para dados fiscais brasileiros. Converta a consulta empresarial '{query}' em SQL otimizado. Considere: 1) Schema de NF-e/NFS-e, 2) Relacionamentos entre tabelas, 3) Performance. Inclua explicação da lógica empresarial.",
                "test_input": {"query": "Fornecedores com mais de R$ 100.000 no trimestre"},
                "evaluation_criteria": ["accuracy", "optimization", "business_logic"]
            }
        ]
        
        results = {
            "total_tests": len(optimization_tests),
            "optimization_improvements": [],
            "response_quality_comparisons": [],
            "processing_time_comparisons": []
        }
        
        if not self.llm_service:
            print("   ⚠️ LLM service not available - using mock optimization testing")
            # Mock results for demonstration
            results["optimization_improvements"] = [0.3, 0.4]  # 30% and 40% improvement
            results["average_improvement"] = 0.35
            print("   📊 Mock Results: Average optimization improvement: 35%")
            return results
        
        for i, test in enumerate(optimization_tests):
            try:
                # Test base prompt
                base_start = time.time()
                base_response = await self._test_prompt_response(
                    test["base_prompt"].format(**test["test_input"])
                )
                base_time = time.time() - base_start
                
                # Test optimized prompt
                opt_start = time.time()
                opt_response = await self._test_prompt_response(
                    test["optimized_prompt"].format(**test["test_input"])
                )
                opt_time = time.time() - opt_start
                
                # Compare quality
                base_quality = self._assess_response_quality(base_response, test["evaluation_criteria"])
                opt_quality = self._assess_response_quality(opt_response, test["evaluation_criteria"])
                
                improvement = (opt_quality - base_quality) / base_quality if base_quality > 0 else 0
                results["optimization_improvements"].append(improvement)
                
                results["response_quality_comparisons"].append({
                    "test_id": i,
                    "base_quality": base_quality,
                    "optimized_quality": opt_quality,
                    "improvement": improvement
                })
                
                results["processing_time_comparisons"].append({
                    "test_id": i,
                    "base_time": base_time,
                    "optimized_time": opt_time,
                    "time_difference": opt_time - base_time
                })
                
                print(f"   ✅ Optimization Test {i+1}: {improvement:.1%} improvement")
                
            except Exception as e:
                print(f"   ❌ Optimization Test {i+1}: Error - {str(e)}")
        
        results["average_improvement"] = sum(results["optimization_improvements"]) / len(results["optimization_improvements"]) if results["optimization_improvements"] else 0
        
        print(f"   📊 Average optimization improvement: {results['average_improvement']:.1%}")
        
        return results
    
    def _evaluate_prompt_quality(self, rendered_prompt: str, test_case: PromptTestCase) -> float:
        """Evaluate the quality of a rendered prompt"""
        score = 0.0
        
        # Check completeness - all expected elements present
        completeness = sum(1 for element in test_case.expected_elements 
                          if element.lower() in rendered_prompt.lower()) / len(test_case.expected_elements)
        score += completeness * 0.4
        
        # Check clarity - prompt length and structure
        if 100 <= len(rendered_prompt) <= 2000:  # Reasonable length
            score += 0.2
        
        # Check variable substitution
        if all(f"{{{var}}}" not in rendered_prompt for var in test_case.variables.keys()):
            score += 0.2  # All variables were substituted
        
        # Check business context integration
        business_terms = ["empresarial", "fiscal", "fornecedor", "análise", "relatório"]
        business_integration = sum(1 for term in business_terms if term in rendered_prompt.lower()) / len(business_terms)
        score += business_integration * 0.2
        
        return min(score, 1.0)
    
    def _assess_business_context_integration(self, prompt: str, business_context: Dict[str, Any]) -> float:
        """Assess how well business context is integrated into the prompt"""
        score = 0.0
        
        # Check for role-specific language
        if business_context.get("user_role") == "executive":
            executive_terms = ["estratégico", "executivo", "impacto", "decisão"]
            if any(term in prompt.lower() for term in executive_terms):
                score += 0.5
        
        # Check for domain-specific terminology
        domain = business_context.get("domain", "")
        if domain == "fiscal" and any(term in prompt.lower() for term in ["nf-e", "nfs-e", "icms", "iss"]):
            score += 0.5
        elif domain == "sql_generation" and any(term in prompt.lower() for term in ["select", "from", "where", "join"]):
            score += 0.5
        
        return min(score, 1.0)
    
    def _evaluate_context_preservation(self, context: Dict[str, Any], test_case: ContextTestCase) -> float:
        """Evaluate how well conversation context is preserved"""
        score = 0.0
        
        if not context or not context.get("historico_conversa"):
            return 0.0
        
        # Check if expected context elements are preserved
        context_text = json.dumps(context, ensure_ascii=False).lower()
        preserved_elements = sum(1 for element in test_case.expected_context_elements 
                               if element.lower() in context_text)
        score += (preserved_elements / len(test_case.expected_context_elements)) * 0.7
        
        # Check conversation history completeness
        history = context.get("historico_conversa", [])
        if len(history) >= min(len(test_case.conversation_history), test_case.context_window_size):
            score += 0.3
        
        return min(score, 1.0)
    
    def _evaluate_memory_efficiency(self, context: Dict[str, Any], test_case: ContextTestCase) -> float:
        """Evaluate memory efficiency of context management"""
        score = 0.0
        
        if not context:
            return 0.0
        
        # Check context size efficiency
        context_size = len(json.dumps(context, ensure_ascii=False))
        if context_size < 5000:  # Reasonable size
            score += 0.5
        
        # Check relevance of preserved information
        history = context.get("historico_conversa", [])
        if history and len(history) <= test_case.context_window_size:
            score += 0.5  # Respects context window limits
        
        return min(score, 1.0)
    
    async def _test_prompt_response(self, prompt: str) -> str:
        """Test a prompt and return the response"""
        try:
            response = await self.llm_service.generate_completion(
                prompt, {}, max_tokens=500, temperature=0.1
            )
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _assess_response_quality(self, response: str, criteria: List[str]) -> float:
        """Assess the quality of an LLM response based on criteria"""
        score = 0.0
        
        if not response or "Error:" in response:
            return 0.0
        
        # Basic quality checks
        if len(response) > 50:  # Non-trivial response
            score += 0.3
        
        # Criteria-specific assessment
        for criterion in criteria:
            if criterion == "specificity" and len(response.split()) > 20:
                score += 0.2
            elif criterion == "context_awareness" and any(term in response.lower() for term in ["brasileiro", "fiscal", "nf-e"]):
                score += 0.2
            elif criterion == "actionability" and any(term in response.lower() for term in ["recomendo", "sugiro", "deve"]):
                score += 0.2
            elif criterion == "accuracy" and "select" in response.lower() and "from" in response.lower():
                score += 0.2
        
        return min(score, 1.0)
    
    async def run_prompt_effectiveness_tests(self) -> Dict[str, Any]:
        """Run all prompt effectiveness tests"""
        print("🚀 Starting Prompt Effectiveness Test Suite")
        print("=" * 60)
        print(f"⏰ Date/Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔑 OpenAI API Key: {'Configured' if settings.OPENAI_API_KEY else 'Not Configured'}")
        print("=" * 60)
        
        await self.initialize()
        
        # Run all test categories
        test_results = {}
        
        # Test 1: Prompt Template Rendering
        test_results["template_rendering"] = await self.test_prompt_template_rendering()
        
        # Test 2: Context Preservation
        test_results["context_preservation"] = await self.test_context_preservation()
        
        # Test 3: Prompt Optimization Effectiveness
        test_results["optimization_effectiveness"] = await self.test_prompt_optimization_effectiveness()
        
        # Calculate overall results
        overall_results = self._calculate_overall_prompt_results(test_results)
        
        # Display final summary
        self._display_prompt_test_summary(test_results, overall_results)
        
        return {
            "test_results": test_results,
            "overall_results": overall_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_overall_prompt_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall prompt test results"""
        total_tests = sum(result.get("total_tests", 0) for result in test_results.values() if "total_tests" in result)
        total_passed = sum(result.get("passed", 0) for result in test_results.values() if "passed" in result)
        
        quality_scores = []
        for result in test_results.values():
            if "average_quality" in result:
                quality_scores.append(result["average_quality"])
            elif "average_preservation" in result:
                quality_scores.append(result["average_preservation"])
            elif "average_improvement" in result:
                quality_scores.append(result["average_improvement"])
        
        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0
        }
    
    def _display_prompt_test_summary(self, test_results: Dict[str, Any], overall_results: Dict[str, Any]):
        """Display prompt test summary"""
        print("\n" + "=" * 60)
        print("📊 PROMPT EFFECTIVENESS TEST SUMMARY")
        print("=" * 60)
        
        for test_name, results in test_results.items():
            if "total_tests" in results:
                status = "✅ PASSED" if results["passed"] == results["total_tests"] else "⚠️ PARTIAL" if results["passed"] > 0 else "❌ FAILED"
                print(f"{test_name.upper()}: {status} ({results.get('passed', 0)}/{results.get('total_tests', 0)})")
            else:
                print(f"{test_name.upper()}: ✅ COMPLETED")
        
        print(f"\n📈 OVERALL METRICS:")
        print(f"   Success Rate: {overall_results['success_rate']:.1%}")
        print(f"   Average Quality Score: {overall_results['average_quality_score']:.2f}")
        
        # Specific recommendations
        print(f"\n💡 PROMPT OPTIMIZATION RECOMMENDATIONS:")
        if overall_results['average_quality_score'] >= 0.8:
            print("   🎉 Excellent prompt quality! Templates are well-optimized.")
        elif overall_results['average_quality_score'] >= 0.6:
            print("   ⚠️ Good prompt quality with room for improvement:")
            print("   - Consider adding more business context to templates")
            print("   - Optimize variable substitution patterns")
        else:
            print("   ❌ Prompt quality needs significant improvement:")
            print("   - Review template structure and clarity")
            print("   - Enhance business context integration")
            print("   - Implement A/B testing for prompt variations")


async def main():
    """Main test execution function"""
    test_suite = PromptEffectivenessTestSuite()
    results = await test_suite.run_prompt_effectiveness_tests()
    
    # Return appropriate exit code
    success_rate = results["overall_results"]["success_rate"]
    return 0 if success_rate >= 0.7 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)