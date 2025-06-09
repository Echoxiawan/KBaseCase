"""
服务模块初始化文件，包含全局服务实例
"""
from .document_service import DocumentService
from .dify_service import DifyService
from .ai_service import AIService
from .vector_store_service import VectorStoreService

# 创建全局服务实例
document_service = DocumentService()

# 注意：以下服务不需要全局实例，因为它们每次创建的成本不高，且没有共享状态
# dify_service = DifyService()
# ai_service = AIService()

__all__ = ['DocumentService', 'DifyService', 'AIService', 'VectorStoreService'] 