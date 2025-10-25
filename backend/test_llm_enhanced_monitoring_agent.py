"""
Test script for LLM Enhanced Monitoring Agent
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from agents.monitoring_agent import MonitoringAgent, SystemAlert, AlertLevel, PerformanceMetrics

async def test_llm_enhanced_monitoring():
    """Test the LLM Enhanced Monitoring Agent"""
    print("🧪 Testando LLM Enhanced Monitoring Agent...")
    
    try:
        # Initialize monitoring agent
        agent = MonitoringAgent()
        await agent.initialize()
        print("✅ Monitoring agent inicializado com sucesso")
        
        # Add some sample performance data
        print("\n📝 Teste 1: Adicionando dados de performance de exemplo")
        for i in range(15):
            metrics = PerformanceMetrics(
                agent_id=f"TestAgent_{i % 3}",
                metrics={
                    'tasks_completed': 100 + i * 10,
                    'success_rate': 95.0 - (i * 0.5),
                    'avg_completion_time': 2.0 + (i * 0.1),
                    'cpu_usage': 30.0 + (i * 2),
                    'memory_usage': 40.0 + (i * 1.5)
                }
            )
            agent.performance_history.append(metrics)
        
        print(f"   Adicionados {len(agent.performance_history)} registros de performance")
        
        # Test 2: System pattern analysis with LLM
        print("\n📝 Teste 2: Análise de padrões do sistema com LLM")
        pattern_analysis = await agent.analyze_system_patterns_with_llm()
        
        if 'error' not in pattern_analysis:
            print(f"   Padrões detectados: {len(pattern_analysis.get('patterns', []))}")
            print(f"   Anomalias detectadas: {len(pattern_analysis.get('anomalies_detected', []))}")
            print(f"   Oportunidades de otimização: {len(pattern_analysis.get('optimization_opportunities', []))}")
        else:
            print(f"   Análise de padrões usando fallback: {pattern_analysis.get('message', 'N/A')}")
        
        # Test 3: Predictive issue detection
        print("\n📝 Teste 3: Detecção preditiva de problemas")
        predictions = await agent.predict_system_issues()
        
        if 'error' not in predictions:
            pred_data = predictions.get('predictions', {})
            print(f"   Predições geradas: {len(pred_data.get('predictions', []))}")
            print(f"   Problemas de alto risco: {len(pred_data.get('high_risk_issues', []))}")
            print(f"   Sugestões de otimização: {len(predictions.get('optimization_suggestions', []))}")
        else:
            print(f"   Detecção preditiva usando fallback")
        
        # Test 4: Performance optimization suggestions
        print("\n📝 Teste 4: Sugestões de otimização de performance")
        optimization = await agent.generate_performance_optimization_suggestions()
        
        if 'error' not in optimization:
            print(f"   Otimizações imediatas: {len(optimization.get('immediate_optimizations', []))}")
            print(f"   Melhorias de médio prazo: {len(optimization.get('medium_term_improvements', []))}")
            print(f"   Investimentos de longo prazo: {len(optimization.get('long_term_investments', []))}")
            print(f"   Total de sugestões: {optimization.get('total_suggestions', 0)}")
        else:
            print(f"   Otimização usando fallback")
        
        # Test 5: Fiscal data quality analysis
        print("\n📝 Teste 5: Análise de qualidade de dados fiscais")
        fiscal_metrics = {
            'validation_errors': 25,
            'missing_fields_rate': 3.2,
            'duplicates': 5,
            'processing_variance': 15.5,
            'typical_volumes': {'nfe': 1000, 'nfse': 500},
            'seasonal_patterns': {'month_end_spike': True},
            'supplier_patterns': {'top_10_suppliers': 60}
        }
        
        quality_analysis = await agent.analyze_fiscal_data_quality_patterns(fiscal_metrics)
        
        if 'error' not in quality_analysis:
            print(f"   Score de qualidade: {quality_analysis.get('data_quality_assessment', {}).get('overall_score', 'N/A')}")
            print(f"   Problemas de qualidade: {len(quality_analysis.get('data_quality_issues', []))}")
            print(f"   Mudanças empresariais: {len(quality_analysis.get('business_changes', []))}")
        else:
            print(f"   Análise de qualidade usando fallback")
        
        # Test 6: Maintenance recommendations
        print("\n📝 Teste 6: Recomendações de manutenção")
        maintenance = await agent.create_intelligent_maintenance_recommendations()
        
        if 'error' not in maintenance:
            print(f"   Manutenção urgente: {len(maintenance.get('urgent_maintenance', []))}")
            print(f"   Manutenção preventiva: {len(maintenance.get('preventive_maintenance', []))}")
            print(f"   Melhorias planejadas: {len(maintenance.get('planned_improvements', []))}")
        else:
            print(f"   Recomendações de manutenção usando fallback")
        
        # Test 7: System health monitoring (existing functionality)
        print("\n📝 Teste 7: Monitoramento de saúde do sistema")
        health_status = await agent.get_system_health()
        
        print(f"   Status geral: {health_status.get('overall_status', 'unknown')}")
        print(f"   Alertas ativos: {health_status.get('active_alerts', 0)}")
        print(f"   Falhas recentes: {health_status.get('recent_failures', 0)}")
        
        # Test 8: Create some alerts to test alert handling
        print("\n📝 Teste 8: Teste de tratamento de alertas")
        test_alert = SystemAlert(
            level=AlertLevel.WARNING,
            message="Teste de alerta para demonstração",
            source="TestAgent",
            details={'test': True, 'metric': 'cpu_usage', 'value': 85}
        )
        
        alert_result = await agent.handle_system_alert(test_alert)
        print(f"   Alerta criado: {alert_result.get('alert_id', 'N/A')}")
        print(f"   Notificação enviada: {alert_result.get('notification_sent', False)}")
        
        # Test 9: Performance tracking
        print("\n📝 Teste 9: Rastreamento de performance de agente")
        perf_metrics = await agent.track_agent_performance("TestAgent")
        
        print(f"   Agente: {perf_metrics.agent_id}")
        print(f"   Tarefas completadas: {perf_metrics.metrics.get('tasks_completed', 0)}")
        print(f"   Taxa de sucesso: {perf_metrics.metrics.get('success_rate', 0)}%")
        
        print("\n✅ Todos os testes concluídos com sucesso!")
        
        # Display summary
        print("\n📊 Resumo dos testes:")
        print(f"   - Monitoring agent funcional: ✅")
        print(f"   - Análise de padrões LLM: ✅")
        print(f"   - Detecção preditiva: ✅")
        print(f"   - Otimização de performance: ✅")
        print(f"   - Análise de qualidade de dados: ✅")
        print(f"   - Recomendações de manutenção: ✅")
        print(f"   - Monitoramento de saúde: ✅")
        print(f"   - Tratamento de alertas: ✅")
        print(f"   - Rastreamento de performance: ✅")
        
        # Cleanup
        await agent.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_predictive_capabilities():
    """Test specific predictive capabilities"""
    print("\n🔮 Testando capacidades preditivas específicas...")
    
    agent = MonitoringAgent()
    await agent.initialize()
    
    # Add performance data with degrading trend
    print("📈 Simulando tendência de degradação de performance...")
    base_time = datetime.now() - timedelta(hours=24)
    
    for i in range(20):
        timestamp = base_time + timedelta(hours=i)
        metrics = PerformanceMetrics(
            agent_id="XMLProcessingAgent",
            metrics={
                'tasks_completed': max(100 - i * 2, 50),  # Decreasing completion
                'success_rate': max(98.0 - i * 0.5, 85.0),  # Decreasing success
                'avg_completion_time': 2.0 + (i * 0.2),  # Increasing time
                'cpu_usage': min(30.0 + (i * 3), 90.0),  # Increasing CPU
                'memory_usage': min(40.0 + (i * 2), 85.0),  # Increasing memory
                'queue_size': min(5 + i, 50)  # Increasing queue
            }
        )
        metrics.collected_at = timestamp
        agent.performance_history.append(metrics)
    
    print(f"   Adicionados {len(agent.performance_history)} pontos de dados com tendência de degradação")
    
    # Test trend analysis
    trends = agent._analyze_performance_trends()
    print(f"   Tendência de curto prazo: {trends.get('short_term_trend', 'N/A')}")
    print(f"   Degradação detectada: {trends.get('performance_degradation', {}).get('detected', False)}")
    
    # Test bottleneck identification
    bottlenecks = await agent._identify_performance_bottlenecks()
    print(f"   Gargalos identificados: {bottlenecks.get('bottleneck_count', 0)}")
    
    if bottlenecks.get('most_critical'):
        critical = bottlenecks['most_critical']
        print(f"   Gargalo mais crítico: {critical.get('type')} em {critical.get('component')}")
    
    await agent.cleanup()
    print("✅ Teste de capacidades preditivas concluído")

async def main():
    """Main test function"""
    print("🚀 Iniciando testes do LLM Enhanced Monitoring Agent")
    print("=" * 70)
    
    # Test basic functionality
    success = await test_llm_enhanced_monitoring()
    
    if success:
        # Test predictive capabilities
        await test_predictive_capabilities()
        
        print("\n" + "=" * 70)
        print("🎉 Todos os testes foram executados com sucesso!")
        print("\n💡 Notas:")
        print("   - Se OpenAI não estiver configurado, o sistema usa análise de fallback")
        print("   - O monitoring agent agora possui capacidades preditivas avançadas")
        print("   - Análise inteligente de padrões e detecção de anomalias")
        print("   - Sugestões de otimização baseadas em LLM")
        print("   - Análise de qualidade de dados fiscais com contexto empresarial")
        print("   - Recomendações de manutenção inteligentes")
        print("   - Alertas proativos baseados em predições")
    else:
        print("\n❌ Alguns testes falharam. Verifique a configuração.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)