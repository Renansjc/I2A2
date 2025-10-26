"""
Schemas package for API request/response validation
"""

from .api_schemas import *
from .fiscal_schemas import *

__all__ = [
    # API Schemas
    "ConsultaNaturalRequest",
    "ConsultaNaturalResponse", 
    "RelatorioExecutivoRequest",
    "RelatorioExecutivoResponse",
    "ProcessarXMLRequest",
    "ProcessarXMLResponse",
    "ErrorResponse",
    
    # Fiscal Schemas
    "FornecedorSchema",
    "ProdutoSchema",
    "ServicoSchema",
    "NFESchema",
    "NFSESchema",
]