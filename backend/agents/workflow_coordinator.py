"""
Workflow Coordination System for Master Agent
Implements task coordination between specialized agents and user interaction management
"""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    """Status de tarefas individuais"""
    PENDENTE = "pendente"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDA = "concluida"
    FALHOU = "falhou"
    CANCELADA = "cancelada"
    AGUARDANDO_DEPENDENCIA = "aguardando_dependencia"


class TaskPriority(Enum):
    """Prioridade de tarefas"""
    BAIXA = 1
    NORMAL = 2
    ALTA = 3
    CRITICA = 4


@dataclass
class Task:
    """Representa uma tarefa individual no workflow"""
    id: str
    name: str
    agent_type: str
    action: str
    data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDENTE
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class WorkflowExecution:
    """Representa a execução de um workflow"""
    id: str
    name: str
    tasks: List[Task]
    status: TaskStatus = TaskStatus.PENDENTE
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_id: str = "default"
    context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class WorkflowCoordinator:
    """
    Coordenador de workflows que gerencia execução de tarefas entre agentes
    Implementa coordenação de tarefas, gerenciamento de dependências e interação com usuário
    """
    
    def __init__(self, master_agent):
        self.master_agent = master_agent
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.user_confirmations: Dict[str, Dict[str, Any]] = {}
        self.workflow_templates: Dict[str, List[Dict[str, Any]]] = {}
        self.max_concurrent_tasks = 5
        self.is_running = False
        
    async def initialize(self):
        """Inicializa o coordenador de workflows"""
        try:
            logger.info("Inicializando coordenador de workflows...")
            
            # Carrega templates de workflow
            await self._load_workflow_templates()
            
            # Inicia loop de processamento de tarefas
            self.is_running = True
            asyncio.create_task(self._task_processing_loop())
            
            logger.info("Coordenador de workflows inicializado")
            
        except Exception as e:
            logger.error("Erro ao inicializar coordenador", error=str(e))
            raise
    
    async def shutdown(self):
        """Finaliza o coordenador de workflows"""
        try:
            self.is_running = False
            
            # Cancela workflows ativos
            for workflow_id in list(self.active_workflows.keys()):
                await self.cancel_workflow(workflow_id)
            
            logger.info("Coordenador de workflows finalizado")
            
        except Exception as e:
            logger.error("Erro ao finalizar coordenador", error=str(e))
    
    async def _load_workflow_templates(self):
        """Carrega templates de workflow pré-definidos"""
        self.workflow_templates = {
            "consulta_dados": [
                {
                    "name": "Gerar consulta SQL",
                    "agent_type": "sql",
                    "action": "gerar_consulta",
                    "priority": TaskPriority.ALTA,
                    "timeout_seconds": 30
                },
                {
                    "name": "Executar consulta",
                    "agent_type": "data_lake",
                    "action": "executar_consulta",
                    "dependencies": ["Gerar consulta SQL"],
                    "priority": TaskPriority.ALTA,
                    "timeout_seconds": 60
                },
                {
                    "name": "Formatar resposta",
                    "agent_type": "master",
                    "action": "formatar_resposta",
                    "dependencies": ["Executar consulta"],
                    "priority": TaskPriority.NORMAL,
                    "timeout_seconds": 15
                }
            ],
            "gerar_relatorio": [
                {
                    "name": "Gerar consulta SQL",
                    "agent_type": "sql",
                    "action": "gerar_consulta",
                    "priority": TaskPriority.ALTA,
                    "timeout_seconds": 30
                },
                {
                    "name": "Executar consulta",
                    "agent_type": "data_lake",
                    "action": "executar_consulta",
                    "dependencies": ["Gerar consulta SQL"],
                    "priority": TaskPriority.ALTA,
                    "timeout_seconds": 60
                },
                {
                    "name": "Gerar relatório",
                    "agent_type": "report",
                    "action": "gerar_relatorio",
                    "dependencies": ["Executar consulta"],
                    "priority": TaskPriority.NORMAL,
                    "timeout_seconds": 120
                },
                {
                    "name": "Apresentar relatório",
                    "agent_type": "master",
                    "action": "apresentar_relatorio",
                    "dependencies": ["Gerar relatório"],
                    "priority": TaskPriority.NORMAL,
                    "timeout_seconds": 15
                }
            ],
            "agendar_tarefa": [
                {
                    "name": "Validar parâmetros",
                    "agent_type": "master",
                    "action": "validar_parametros_agendamento",
                    "priority": TaskPriority.ALTA,
                    "timeout_seconds": 15
                },
                {
                    "name": "Criar agendamento",
                    "agent_type": "scheduler",
                    "action": "criar_agendamento",
                    "dependencies": ["Validar parâmetros"],
                    "priority": TaskPriority.ALTA,
                    "timeout_seconds": 30
                },
                {
                    "name": "Confirmar agendamento",
                    "agent_type": "master",
                    "action": "confirmar_agendamento",
                    "dependencies": ["Criar agendamento"],
                    "priority": TaskPriority.NORMAL,
                    "timeout_seconds": 15
                }
            ]
        }
        
        logger.info("Templates de workflow carregados", 
                   total_templates=len(self.workflow_templates))
    
    async def create_workflow(self, template_name: str, context: Dict[str, Any], 
                            user_id: str = "default") -> str:
        """Cria novo workflow baseado em template"""
        try:
            if template_name not in self.workflow_templates:
                raise ValueError(f"Template '{template_name}' não encontrado")
            
            workflow_id = str(uuid.uuid4())
            template = self.workflow_templates[template_name]
            
            # Cria tarefas baseadas no template
            tasks = []
            task_name_to_id = {}
            
            for task_template in template:
                task_id = str(uuid.uuid4())
                task_name_to_id[task_template["name"]] = task_id
                
                task = Task(
                    id=task_id,
                    name=task_template["name"],
                    agent_type=task_template["agent_type"],
                    action=task_template["action"],
                    data=context.copy(),
                    priority=task_template.get("priority", TaskPriority.NORMAL),
                    timeout_seconds=task_template.get("timeout_seconds", 300),
                    max_retries=task_template.get("max_retries", 3)
                )
                tasks.append(task)
            
            # Resolve dependências
            for i, task_template in enumerate(template):
                if "dependencies" in task_template:
                    for dep_name in task_template["dependencies"]:
                        if dep_name in task_name_to_id:
                            tasks[i].dependencies.append(task_name_to_id[dep_name])
            
            # Cria execução do workflow
            workflow = WorkflowExecution(
                id=workflow_id,
                name=template_name,
                tasks=tasks,
                user_id=user_id,
                context=context
            )
            
            self.active_workflows[workflow_id] = workflow
            
            # Adiciona tarefas prontas à fila
            await self._queue_ready_tasks(workflow_id)
            
            logger.info("Workflow criado", 
                       workflow_id=workflow_id,
                       template=template_name,
                       total_tasks=len(tasks))
            
            return workflow_id
            
        except Exception as e:
            logger.error("Erro ao criar workflow", template=template_name, error=str(e))
            raise
    
    async def create_custom_workflow(self, tasks_config: List[Dict[str, Any]], 
                                   context: Dict[str, Any], user_id: str = "default") -> str:
        """Cria workflow personalizado"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Cria tarefas personalizadas
            tasks = []
            for i, task_config in enumerate(tasks_config):
                task_id = str(uuid.uuid4())
                
                task = Task(
                    id=task_id,
                    name=task_config.get("name", f"Tarefa {i+1}"),
                    agent_type=task_config["agent_type"],
                    action=task_config["action"],
                    data={**context, **task_config.get("data", {})},
                    priority=TaskPriority(task_config.get("priority", 2)),
                    dependencies=task_config.get("dependencies", []),
                    timeout_seconds=task_config.get("timeout_seconds", 300),
                    max_retries=task_config.get("max_retries", 3)
                )
                tasks.append(task)
            
            # Cria execução do workflow
            workflow = WorkflowExecution(
                id=workflow_id,
                name="workflow_personalizado",
                tasks=tasks,
                user_id=user_id,
                context=context
            )
            
            self.active_workflows[workflow_id] = workflow
            
            # Adiciona tarefas prontas à fila
            await self._queue_ready_tasks(workflow_id)
            
            logger.info("Workflow personalizado criado", 
                       workflow_id=workflow_id,
                       total_tasks=len(tasks))
            
            return workflow_id
            
        except Exception as e:
            logger.error("Erro ao criar workflow personalizado", error=str(e))
            raise
    
    async def _queue_ready_tasks(self, workflow_id: str):
        """Adiciona tarefas prontas para execução à fila"""
        if workflow_id not in self.active_workflows:
            return
        
        workflow = self.active_workflows[workflow_id]
        
        for task in workflow.tasks:
            if task.status == TaskStatus.PENDENTE and await self._are_dependencies_met(task):
                task.status = TaskStatus.PENDENTE
                self.task_queue.append(task)
                logger.debug("Tarefa adicionada à fila", task_id=task.id, task_name=task.name)
        
        # Ordena fila por prioridade
        self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
    
    async def _are_dependencies_met(self, task: Task) -> bool:
        """Verifica se todas as dependências da tarefa foram atendidas"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            if self.completed_tasks[dep_id].status != TaskStatus.CONCLUIDA:
                return False
        return True
    
    async def _task_processing_loop(self):
        """Loop principal de processamento de tarefas"""
        while self.is_running:
            try:
                # Processa tarefas na fila
                await self._process_task_queue()
                
                # Verifica timeouts
                await self._check_task_timeouts()
                
                # Atualiza status dos workflows
                await self._update_workflow_status()
                
                # Aguarda antes da próxima iteração
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("Erro no loop de processamento", error=str(e))
                await asyncio.sleep(5)
    
    async def _process_task_queue(self):
        """Processa tarefas na fila de execução"""
        while (len(self.running_tasks) < self.max_concurrent_tasks and 
               self.task_queue and self.is_running):
            
            task = self.task_queue.pop(0)
            
            # Verifica novamente se dependências estão atendidas
            if not await self._are_dependencies_met(task):
                task.status = TaskStatus.AGUARDANDO_DEPENDENCIA
                continue
            
            # Inicia execução da tarefa
            await self._start_task_execution(task)
    
    async def _start_task_execution(self, task: Task):
        """Inicia execução de uma tarefa"""
        try:
            task.status = TaskStatus.EM_EXECUCAO
            task.started_at = datetime.now()
            self.running_tasks[task.id] = task
            
            logger.info("Iniciando execução de tarefa", 
                       task_id=task.id, 
                       task_name=task.name,
                       agent_type=task.agent_type)
            
            # Executa tarefa de forma assíncrona
            asyncio.create_task(self._execute_task(task))
            
        except Exception as e:
            logger.error("Erro ao iniciar tarefa", task_id=task.id, error=str(e))
            await self._handle_task_failure(task, str(e))
    
    async def _execute_task(self, task: Task):
        """Executa uma tarefa específica"""
        try:
            # Coleta dados de dependências
            dependency_results = {}
            for dep_id in task.dependencies:
                if dep_id in self.completed_tasks:
                    dependency_results[dep_id] = self.completed_tasks[dep_id].result
            
            # Adiciona resultados de dependências aos dados da tarefa
            task.data["dependency_results"] = dependency_results
            
            # Executa tarefa através do Master Agent
            if task.agent_type == "master":
                result = await self.master_agent._handle_master_action(
                    task.action, task.data, dependency_results
                )
            else:
                # Roteia para agente específico
                from .master_agent import AgentType
                agent_type = AgentType(task.agent_type)
                result = await self.master_agent.route_to_agent(
                    agent_type, task.action, task.data
                )
            
            # Marca tarefa como concluída
            await self._handle_task_completion(task, result)
            
        except asyncio.TimeoutError:
            logger.warning("Timeout na execução de tarefa", task_id=task.id)
            await self._handle_task_timeout(task)
            
        except Exception as e:
            logger.error("Erro na execução de tarefa", task_id=task.id, error=str(e))
            await self._handle_task_failure(task, str(e))
    
    async def _handle_task_completion(self, task: Task, result: Dict[str, Any]):
        """Trata conclusão bem-sucedida de tarefa"""
        task.status = TaskStatus.CONCLUIDA
        task.completed_at = datetime.now()
        task.result = result
        
        # Move tarefa para lista de concluídas
        if task.id in self.running_tasks:
            del self.running_tasks[task.id]
        self.completed_tasks[task.id] = task
        
        logger.info("Tarefa concluída", 
                   task_id=task.id, 
                   task_name=task.name,
                   duration=(task.completed_at - task.started_at).total_seconds())
        
        # Verifica se novas tarefas podem ser executadas
        await self._check_for_ready_tasks()
    
    async def _handle_task_failure(self, task: Task, error: str):
        """Trata falha na execução de tarefa"""
        task.error = error
        
        # Verifica se deve tentar novamente
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.PENDENTE
            
            # Adiciona de volta à fila com delay
            await asyncio.sleep(2 ** task.retry_count)  # Backoff exponencial
            self.task_queue.append(task)
            
            logger.warning("Tentando novamente tarefa", 
                          task_id=task.id, 
                          retry=task.retry_count,
                          max_retries=task.max_retries)
        else:
            # Falha definitiva
            task.status = TaskStatus.FALHOU
            task.completed_at = datetime.now()
            
            logger.error("Tarefa falhou definitivamente", 
                        task_id=task.id, 
                        error=error)
        
        # Remove da lista de execução
        if task.id in self.running_tasks:
            del self.running_tasks[task.id]
    
    async def _handle_task_timeout(self, task: Task):
        """Trata timeout de tarefa"""
        await self._handle_task_failure(task, "Timeout na execução")
    
    async def _check_task_timeouts(self):
        """Verifica timeouts de tarefas em execução"""
        current_time = datetime.now()
        
        for task_id, task in list(self.running_tasks.items()):
            if task.started_at:
                elapsed = (current_time - task.started_at).total_seconds()
                if elapsed > task.timeout_seconds:
                    await self._handle_task_timeout(task)
    
    async def _check_for_ready_tasks(self):
        """Verifica se há tarefas prontas para execução após conclusão de dependências"""
        for workflow in self.active_workflows.values():
            for task in workflow.tasks:
                if (task.status == TaskStatus.AGUARDANDO_DEPENDENCIA and 
                    await self._are_dependencies_met(task)):
                    task.status = TaskStatus.PENDENTE
                    self.task_queue.append(task)
        
        # Reordena fila por prioridade
        self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
    
    async def _update_workflow_status(self):
        """Atualiza status dos workflows baseado no status das tarefas"""
        for workflow_id, workflow in list(self.active_workflows.items()):
            if workflow.status == TaskStatus.CONCLUIDA:
                continue
            
            # Conta status das tarefas
            task_statuses = [task.status for task in workflow.tasks]
            
            if all(status == TaskStatus.CONCLUIDA for status in task_statuses):
                # Workflow concluído
                workflow.status = TaskStatus.CONCLUIDA
                workflow.completed_at = datetime.now()
                
                # Coleta resultados
                workflow.results = {
                    task.id: task.result for task in workflow.tasks 
                    if task.result is not None
                }
                
                logger.info("Workflow concluído", workflow_id=workflow_id)
                
            elif any(status == TaskStatus.FALHOU for status in task_statuses):
                # Workflow falhou
                workflow.status = TaskStatus.FALHOU
                workflow.completed_at = datetime.now()
                workflow.error = "Uma ou mais tarefas falharam"
                
                logger.error("Workflow falhou", workflow_id=workflow_id)
            
            elif any(status == TaskStatus.EM_EXECUCAO for status in task_statuses):
                # Workflow em execução
                if workflow.status == TaskStatus.PENDENTE:
                    workflow.status = TaskStatus.EM_EXECUCAO
                    workflow.started_at = datetime.now()
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Obtém status detalhado de um workflow"""
        if workflow_id not in self.active_workflows:
            return {"erro": "Workflow não encontrado"}
        
        workflow = self.active_workflows[workflow_id]
        
        # Estatísticas das tarefas
        task_stats = {
            "total": len(workflow.tasks),
            "pendentes": len([t for t in workflow.tasks if t.status == TaskStatus.PENDENTE]),
            "em_execucao": len([t for t in workflow.tasks if t.status == TaskStatus.EM_EXECUCAO]),
            "concluidas": len([t for t in workflow.tasks if t.status == TaskStatus.CONCLUIDA]),
            "falharam": len([t for t in workflow.tasks if t.status == TaskStatus.FALHOU])
        }
        
        return {
            "workflow_id": workflow_id,
            "nome": workflow.name,
            "status": workflow.status.value,
            "user_id": workflow.user_id,
            "criado_em": workflow.created_at.isoformat(),
            "iniciado_em": workflow.started_at.isoformat() if workflow.started_at else None,
            "concluido_em": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "estatisticas_tarefas": task_stats,
            "tarefas": [
                {
                    "id": task.id,
                    "nome": task.name,
                    "status": task.status.value,
                    "agent_type": task.agent_type,
                    "action": task.action,
                    "tentativas": task.retry_count,
                    "erro": task.error
                }
                for task in workflow.tasks
            ]
        }
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancela um workflow e suas tarefas"""
        if workflow_id not in self.active_workflows:
            return {"erro": "Workflow não encontrado"}
        
        workflow = self.active_workflows[workflow_id]
        
        # Cancela tarefas em execução
        for task in workflow.tasks:
            if task.status in [TaskStatus.PENDENTE, TaskStatus.EM_EXECUCAO, TaskStatus.AGUARDANDO_DEPENDENCIA]:
                task.status = TaskStatus.CANCELADA
                task.completed_at = datetime.now()
                
                # Remove da fila se estiver lá
                if task in self.task_queue:
                    self.task_queue.remove(task)
                
                # Remove das tarefas em execução
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
        
        workflow.status = TaskStatus.CANCELADA
        workflow.completed_at = datetime.now()
        
        logger.info("Workflow cancelado", workflow_id=workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "status": "cancelado",
            "message": "Workflow e suas tarefas foram cancelados"
        }
    
    async def request_user_confirmation(self, workflow_id: str, message: str, 
                                      options: List[str] = None) -> str:
        """Solicita confirmação do usuário durante execução do workflow"""
        confirmation_id = str(uuid.uuid4())
        
        self.user_confirmations[confirmation_id] = {
            "workflow_id": workflow_id,
            "message": message,
            "options": options or ["Sim", "Não"],
            "created_at": datetime.now(),
            "status": "aguardando"
        }
        
        logger.info("Confirmação do usuário solicitada", 
                   confirmation_id=confirmation_id,
                   workflow_id=workflow_id)
        
        return confirmation_id
    
    async def provide_user_confirmation(self, confirmation_id: str, 
                                      response: str) -> Dict[str, Any]:
        """Fornece resposta do usuário para confirmação"""
        if confirmation_id not in self.user_confirmations:
            return {"erro": "Confirmação não encontrada"}
        
        confirmation = self.user_confirmations[confirmation_id]
        confirmation["response"] = response
        confirmation["status"] = "respondida"
        confirmation["responded_at"] = datetime.now()
        
        logger.info("Confirmação do usuário recebida", 
                   confirmation_id=confirmation_id,
                   response=response)
        
        return {
            "confirmation_id": confirmation_id,
            "status": "recebida",
            "response": response
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do sistema de coordenação"""
        return {
            "workflows_ativos": len(self.active_workflows),
            "tarefas_na_fila": len(self.task_queue),
            "tarefas_em_execucao": len(self.running_tasks),
            "tarefas_concluidas": len(self.completed_tasks),
            "confirmacoes_pendentes": len([
                c for c in self.user_confirmations.values() 
                if c["status"] == "aguardando"
            ]),
            "max_tarefas_concorrentes": self.max_concurrent_tasks,
            "sistema_ativo": self.is_running,
            "timestamp": datetime.now().isoformat()
        }