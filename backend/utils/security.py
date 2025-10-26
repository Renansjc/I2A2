"""
Input sanitization and security validation utilities
Utilitários de sanitização de entrada e validação de segurança
"""

import re
import html
import bleach
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import base64
import hashlib
import secrets
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

class SanitizadorEntrada:
    """Sanitizador de entrada para prevenir ataques de segurança"""
    
    # Padrões perigosos para SQL Injection
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|#|/\*|\*/)",
        r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR)\b)",
        r"(<script[^>]*>.*?</script>)",
        r"(javascript:)",
        r"(data:text/html)",
        r"(\beval\s*\()",
        r"(\bexec\s*\()"
    ]
    
    # Padrões perigosos para XSS
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"javascript:",
        r"vbscript:",
        r"data:text/html",
        r"on\w+\s*=",
        r"expression\s*\(",
        r"url\s*\(",
        r"@import"
    ]
    
    # Tags HTML permitidas para campos de texto rico
    ALLOWED_HTML_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]
    
    # Atributos HTML permitidos
    ALLOWED_HTML_ATTRIBUTES = {
        '*': ['class'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    @classmethod
    def sanitizar_string(cls, texto: str, permitir_html: bool = False) -> str:
        """Sanitizar string removendo conteúdo perigoso"""
        if not isinstance(texto, str):
            return str(texto)
        
        # Remover caracteres de controle
        texto = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', texto)
        
        # Escapar HTML se não permitido
        if not permitir_html:
            texto = html.escape(texto)
        else:
            # Usar bleach para limpar HTML perigoso
            texto = bleach.clean(
                texto,
                tags=cls.ALLOWED_HTML_TAGS,
                attributes=cls.ALLOWED_HTML_ATTRIBUTES,
                strip=True
            )
        
        # Verificar padrões de SQL Injection
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, texto, re.IGNORECASE):
                logger.warning("Tentativa de SQL Injection detectada", texto=texto[:100])
                # Remover o padrão perigoso
                texto = re.sub(pattern, '', texto, flags=re.IGNORECASE)
        
        # Verificar padrões de XSS
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, texto, re.IGNORECASE):
                logger.warning("Tentativa de XSS detectada", texto=texto[:100])
                # Remover o padrão perigoso
                texto = re.sub(pattern, '', texto, flags=re.IGNORECASE)
        
        return texto.strip()
    
    @classmethod
    def sanitizar_nome_arquivo(cls, nome_arquivo: str) -> str:
        """Sanitizar nome de arquivo"""
        if not nome_arquivo:
            return "arquivo_sem_nome"
        
        # Remover caracteres perigosos
        nome_limpo = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', nome_arquivo)
        
        # Remover múltiplos pontos consecutivos
        nome_limpo = re.sub(r'\.{2,}', '.', nome_limpo)
        
        # Limitar tamanho
        if len(nome_limpo) > 255:
            nome_base, extensao = nome_limpo.rsplit('.', 1) if '.' in nome_limpo else (nome_limpo, '')
            nome_limpo = nome_base[:250] + ('.' + extensao if extensao else '')
        
        # Evitar nomes reservados do Windows
        nomes_reservados = [
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
            'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
            'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        nome_sem_ext = nome_limpo.rsplit('.', 1)[0] if '.' in nome_limpo else nome_limpo
        if nome_sem_ext.upper() in nomes_reservados:
            nome_limpo = f"arquivo_{nome_limpo}"
        
        return nome_limpo or "arquivo_sanitizado"
    
    @classmethod
    def validar_url(cls, url: str) -> bool:
        """Validar URL para prevenir ataques"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # Verificar esquema permitido
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Verificar se não é localhost ou IP privado
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # Bloquear IPs privados e localhost
            ips_bloqueados = [
                '127.0.0.1', 'localhost', '0.0.0.0',
                '10.', '172.16.', '172.17.', '172.18.', '172.19.',
                '172.20.', '172.21.', '172.22.', '172.23.',
                '172.24.', '172.25.', '172.26.', '172.27.',
                '172.28.', '172.29.', '172.30.', '172.31.',
                '192.168.'
            ]
            
            for ip_bloqueado in ips_bloqueados:
                if hostname.startswith(ip_bloqueado):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def sanitizar_base64(cls, conteudo_base64: str) -> Optional[str]:
        """Sanitizar e validar conteúdo base64"""
        if not conteudo_base64:
            return None
        
        try:
            # Remover caracteres não base64
            conteudo_limpo = re.sub(r'[^A-Za-z0-9+/=]', '', conteudo_base64)
            
            # Verificar se é base64 válido
            decoded = base64.b64decode(conteudo_limpo, validate=True)
            
            # Verificar tamanho (máximo 50MB)
            if len(decoded) > 50 * 1024 * 1024:
                logger.warning("Arquivo base64 muito grande", tamanho=len(decoded))
                return None
            
            # Verificar se não contém conteúdo executável
            conteudo_str = decoded.decode('utf-8', errors='ignore')[:1000]  # Primeiros 1000 chars
            
            padroes_perigosos = [
                b'<script', b'javascript:', b'vbscript:', b'data:text/html',
                b'<?php', b'<%', b'#!/bin/', b'#!/usr/bin/'
            ]
            
            for padrao in padroes_perigosos:
                if padrao in decoded[:1000]:
                    logger.warning("Conteúdo perigoso detectado em base64")
                    return None
            
            return conteudo_limpo
            
        except Exception as e:
            logger.warning("Erro ao validar base64", erro=str(e))
            return None

class ValidadorSeguranca:
    """Validador de segurança para requisições"""
    
    def __init__(self):
        self.tentativas_login = {}
        self.ips_bloqueados = set()
        self.tokens_usados = set()
    
    def validar_rate_limiting(self, identificador: str, limite: int = 100, janela_minutos: int = 1) -> bool:
        """Validar rate limiting por identificador"""
        agora = datetime.now()
        chave = f"{identificador}_{agora.strftime('%Y%m%d%H%M')}"
        
        # Limpar entradas antigas
        self._limpar_rate_limiting()
        
        # Contar tentativas na janela atual
        tentativas = self.tentativas_login.get(chave, 0)
        
        if tentativas >= limite:
            logger.warning("Rate limit excedido", identificador=identificador, tentativas=tentativas)
            return False
        
        # Incrementar contador
        self.tentativas_login[chave] = tentativas + 1
        return True
    
    def _limpar_rate_limiting(self):
        """Limpar entradas antigas de rate limiting"""
        agora = datetime.now()
        chaves_antigas = []
        
        for chave in self.tentativas_login.keys():
            try:
                # Extrair timestamp da chave
                timestamp_str = chave.split('_')[-1]
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M')
                
                # Remover se mais antigo que 5 minutos
                if agora - timestamp > timedelta(minutes=5):
                    chaves_antigas.append(chave)
            except (ValueError, IndexError):
                chaves_antigas.append(chave)
        
        for chave in chaves_antigas:
            del self.tentativas_login[chave]
    
    def validar_token_unico(self, token: str) -> bool:
        """Validar se token não foi usado antes (prevenir replay attacks)"""
        if token in self.tokens_usados:
            logger.warning("Token reutilizado detectado", token_hash=hashlib.sha256(token.encode()).hexdigest()[:8])
            return False
        
        # Adicionar token à lista (com limite de tamanho)
        self.tokens_usados.add(token)
        
        # Manter apenas os últimos 10000 tokens
        if len(self.tokens_usados) > 10000:
            # Remover tokens mais antigos (simplificado)
            tokens_lista = list(self.tokens_usados)
            self.tokens_usados = set(tokens_lista[-5000:])
        
        return True
    
    def gerar_token_seguro(self, tamanho: int = 32) -> str:
        """Gerar token seguro"""
        return secrets.token_urlsafe(tamanho)
    
    def validar_integridade_dados(self, dados: Dict[str, Any], hash_esperado: Optional[str] = None) -> bool:
        """Validar integridade dos dados"""
        if not hash_esperado:
            return True
        
        try:
            # Serializar dados de forma consistente
            dados_str = str(sorted(dados.items()))
            hash_calculado = hashlib.sha256(dados_str.encode()).hexdigest()
            
            return hash_calculado == hash_esperado
            
        except Exception as e:
            logger.error("Erro ao validar integridade", erro=str(e))
            return False

class SanitizadorCompleto:
    """Sanitizador completo que combina todas as validações de segurança"""
    
    def __init__(self):
        self.sanitizador = SanitizadorEntrada()
        self.validador = ValidadorSeguranca()
    
    def sanitizar_requisicao_completa(self, dados: Dict[str, Any], ip_cliente: str) -> Dict[str, Any]:
        """Sanitizar requisição completa"""
        
        # Validar rate limiting por IP
        if not self.validador.validar_rate_limiting(ip_cliente, limite=1000, janela_minutos=1):
            raise ValueError("Rate limit excedido para este IP")
        
        dados_sanitizados = {}
        
        for chave, valor in dados.items():
            # Sanitizar chave
            chave_limpa = self.sanitizador.sanitizar_string(str(chave))
            
            # Sanitizar valor baseado no tipo
            if isinstance(valor, str):
                if chave_limpa in ['conteudo_base64', 'arquivo_base64']:
                    valor_limpo = self.sanitizador.sanitizar_base64(valor)
                elif chave_limpa in ['url_arquivo', 'url_callback']:
                    if self.sanitizador.validar_url(valor):
                        valor_limpo = valor
                    else:
                        raise ValueError(f"URL inválida ou insegura: {chave_limpa}")
                elif 'nome_arquivo' in chave_limpa:
                    valor_limpo = self.sanitizador.sanitizar_nome_arquivo(valor)
                else:
                    valor_limpo = self.sanitizador.sanitizar_string(valor)
            
            elif isinstance(valor, dict):
                valor_limpo = self.sanitizar_requisicao_completa(valor, ip_cliente)
            
            elif isinstance(valor, list):
                valor_limpo = [
                    self.sanitizar_requisicao_completa(item, ip_cliente) if isinstance(item, dict)
                    else self.sanitizador.sanitizar_string(str(item)) if isinstance(item, str)
                    else item
                    for item in valor
                ]
            
            else:
                valor_limpo = valor
            
            dados_sanitizados[chave_limpa] = valor_limpo
        
        return dados_sanitizados
    
    def validar_seguranca_arquivo(self, nome_arquivo: str, conteudo: bytes) -> bool:
        """Validar segurança de arquivo"""
        
        # Validar extensão
        extensoes_permitidas = ['.xml', '.pdf', '.xlsx', '.docx', '.txt', '.json']
        extensao = '.' + nome_arquivo.split('.')[-1].lower() if '.' in nome_arquivo else ''
        
        if extensao not in extensoes_permitidas:
            logger.warning("Extensão de arquivo não permitida", arquivo=nome_arquivo, extensao=extensao)
            return False
        
        # Validar tamanho (máximo 100MB)
        if len(conteudo) > 100 * 1024 * 1024:
            logger.warning("Arquivo muito grande", arquivo=nome_arquivo, tamanho=len(conteudo))
            return False
        
        # Verificar assinatura de arquivo (magic numbers)
        assinaturas_validas = {
            '.xml': [b'<?xml', b'<'],
            '.pdf': [b'%PDF'],
            '.xlsx': [b'PK\x03\x04'],
            '.docx': [b'PK\x03\x04'],
            '.txt': [],  # Qualquer conteúdo texto
            '.json': [b'{', b'[']
        }
        
        assinaturas = assinaturas_validas.get(extensao, [])
        if assinaturas:
            inicio_arquivo = conteudo[:10]
            if not any(inicio_arquivo.startswith(assinatura) for assinatura in assinaturas):
                logger.warning("Assinatura de arquivo inválida", arquivo=nome_arquivo, extensao=extensao)
                return False
        
        # Verificar conteúdo perigoso
        conteudo_str = conteudo.decode('utf-8', errors='ignore')[:5000]  # Primeiros 5000 chars
        
        padroes_perigosos = [
            '<script', 'javascript:', 'vbscript:', 'data:text/html',
            '<?php', '<%', '#!/bin/', '#!/usr/bin/', '<iframe', '<object', '<embed'
        ]
        
        for padrao in padroes_perigosos:
            if padrao in conteudo_str.lower():
                logger.warning("Conteúdo perigoso detectado em arquivo", arquivo=nome_arquivo)
                return False
        
        return True

# Instâncias globais
sanitizador = SanitizadorCompleto()
validador_seguranca = ValidadorSeguranca()