import os
import requests
import json
import logging
from app.config import get_config

class DifyService:
    """Dify API服务，负责与Dify知识库交互"""
    
    def __init__(self):
        config = get_config()
        self.api_key = config.DIFY_API_KEY
        self.base_url = config.DIFY_API_BASE_URL
        self.dataset_id = config.DIFY_KNOWLEDGE_BASE_ID
        
        if not self.api_key:
            raise ValueError("Dify API密钥未配置")
        if not self.dataset_id:
            raise ValueError("Dify知识库ID未配置")
            
    def _handle_api_error(self, response, operation_name):
        """处理API错误，记录详细信息
        
        Args:
            response: requests响应对象
            operation_name: 操作名称，用于日志记录
            
        Returns:
            包含错误信息的字典
        """
        error_message = f"{operation_name}失败: HTTP {response.status_code}"
        
        # 尝试解析错误详情
        try:
            error_detail = response.json()
            # 提取Dify API的错误代码和消息
            if 'code' in error_detail and 'message' in error_detail:
                error_code = error_detail.get('code')
                error_text = error_detail.get('message')
                error_message += f", 错误代码: {error_code}, 错误信息: {error_text}"
            else:
                error_message += f", 错误详情: {json.dumps(error_detail)}"
        except:
            # 如果无法解析为JSON，记录原始响应文本
            error_message += f", 响应内容: {response.text}"
        
        # 记录错误信息
        logging.error(error_message)
        print(error_message)
        
        return {"error": error_message}
            
    def query_knowledge_base(self, query, top_k=10, search_method="hybrid_search", reranking_enable=True):
        """查询知识库并返回结果
        
        Args:
            query: 查询内容
            top_k: 返回结果数量，默认为3
            search_method: 检索方法，可选值为"semantic_search"、"keyword_search"、"full_text_search"、"hybrid_search"
            reranking_enable: 是否启用重排序
            
        Returns:
            包含查询结果的字典
        """
        url = f"{self.base_url}/datasets/{self.dataset_id}/retrieve"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建检索模型参数
        retrieval_model = {
            "search_method": search_method,
            "reranking_enable": reranking_enable,
            "top_k": top_k,
            "score_threshold_enabled": True,
            "score_threshold": 0.05

        }
        
        data = {
            "query": query,
            "retrieval_model": retrieval_model
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            # 如果请求失败，使用辅助方法处理错误
            if response.status_code != 200:
                return self._handle_api_error(response, "查询知识库")
                
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = f"查询知识库失败: {str(e)}"
            logging.error(error_message)
            print(error_message)
            return {"error": error_message}
            
    def get_knowledge_files(self, page=1, limit=20, keyword=None):
        """获取知识库中的文件列表
        
        Args:
            page: 页码，默认为1
            limit: 每页数量，默认为20
            keyword: 搜索关键词，可选
            
        Returns:
            包含文件列表的字典
        """
        url = f"{self.base_url}/datasets/{self.dataset_id}/documents"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "page": page,
            "limit": limit
        }
        
        if keyword:
            params["keyword"] = keyword
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # 如果请求失败，使用辅助方法处理错误
            if response.status_code != 200:
                return self._handle_api_error(response, "获取知识库文件列表")
                
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = f"获取知识库文件列表失败: {str(e)}"
            logging.error(error_message)
            print(error_message)
            return {"error": error_message}
            
    def upload_file_to_knowledge_base(self, file_path, file_name=None, indexing_technique="high_quality", process_rule=None, embedding_model=None, embedding_model_provider=None):
        """上传文件到知识库
        
        Args:
            file_path: 文件路径
            file_name: 文件名，如果不提供则使用文件路径中的文件名
            indexing_technique: 索引方式，可选值为"high_quality"或"economy"，默认为"high_quality"
            process_rule: 处理规则，默认为自动模式
            embedding_model: Embedding模型名称（首次上传时可能需要）
            embedding_model_provider: Embedding模型供应商（首次上传时可能需要）
            
        Returns:
            上传结果的字典
        """
        url = f"{self.base_url}/datasets/{self.dataset_id}/document/create-by-file"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
            # 不设置Content-Type，让requests自动处理multipart/form-data
        }
        
        if not file_name:
            file_name = os.path.basename(file_path)
            
        # 默认处理规则为自动模式
        if process_rule is None:
            process_rule = {
                "mode": "automatic"
            }
            
        # 构建data参数，添加data_source_type字段
        data_dict = {
            "indexing_technique": indexing_technique,
            "process_rule": process_rule,
            "data_source": {
                "info_list": {
                    "data_source_type": "upload_file"
                }
            }
        }
        
        # 如果提供了embedding模型信息，添加到data中
        if embedding_model and embedding_model_provider:
            data_dict["embedding_model"] = embedding_model
            data_dict["embedding_model_provider"] = embedding_model_provider
            
        # 构建检索模型参数（如果是首次上传可能需要）
        retrieval_model = {
            "search_method": "semantic_search",
            "reranking_enable": False,
            "top_k": 3,
            "score_threshold_enabled": False
        }
        data_dict["retrieval_model"] = retrieval_model
        
        # 记录请求信息（调试用）
        logging.debug(f"上传文件到知识库，URL: {url}")
        logging.debug(f"上传文件: {file_name}")
        logging.debug(f"请求参数: {json.dumps(data_dict)}")
            
        try:
            with open(file_path, 'rb') as f:
                # 将data_dict转换为JSON字符串
                data_json = json.dumps(data_dict)
                
                # 构建multipart/form-data请求
                files = {
                    'file': (file_name, f),
                    'data': (None, data_json, 'text/plain')
                }
                
                # 发送请求
                response = requests.post(url, headers=headers, files=files)
                
                # 详细记录请求和响应信息（调试用）
                logging.debug(f"请求头: {headers}")
                logging.debug(f"响应状态码: {response.status_code}")
                logging.debug(f"响应内容: {response.text}")
                
                # 如果请求失败，使用辅助方法处理错误
                if response.status_code != 200:
                    return self._handle_api_error(response, "上传文件到知识库")
                
                # 请求成功，返回JSON响应
                return response.json()
        except requests.exceptions.RequestException as e:
            error_message = f"上传文件到知识库失败: {str(e)}"
            logging.error(error_message)
            print(error_message)
            return {"error": error_message}
        except Exception as e:
            error_message = f"处理文件上传时发生错误: {str(e)}"
            logging.error(error_message)
            print(error_message)
            return {"error": error_message}
            
    def delete_file_from_knowledge_base(self, document_id):
        """从知识库中删除文件
        
        Args:
            document_id: 文档ID
            
        Returns:
            成功时返回空字典，失败时返回包含错误信息的字典
        """
        url = f"{self.base_url}/datasets/{self.dataset_id}/documents/{document_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.delete(url, headers=headers)
            
            # API返回204 No Content表示成功
            if response.status_code == 204:
                return {"success": True, "message": "文件已成功删除"}
                
            # 如果不是204，可能有错误
            if response.status_code != 200:
                return self._handle_api_error(response, "删除知识库文件")
                
            # 如果有返回内容，则解析JSON
            if response.content:
                return response.json()
            else:
                return {"success": True}
        except requests.exceptions.RequestException as e:
            error_message = f"从知识库中删除文件失败: {str(e)}"
            logging.error(error_message)
            print(error_message)
            return {"error": error_message}
            
    def get_document_indexing_status(self, batch):
        """获取文档嵌入状态（进度）
        
        Args:
            batch: 上传文档的批次号，从上传文件响应中获取
            
        Returns:
            包含文档处理状态的字典
        """
        url = f"{self.base_url}/datasets/{self.dataset_id}/documents/{batch}/indexing-status"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            # 如果请求失败，使用辅助方法处理错误
            if response.status_code != 200:
                return self._handle_api_error(response, "获取文档嵌入状态")
                
            return response.json()
        except requests.exceptions.RequestException as e:
            error_message = f"获取文档嵌入状态失败: {str(e)}"
            logging.error(error_message)
            print(error_message)
            return {"error": error_message}
            
    def chat_with_knowledge_base_using_retrieve(self, message, conversation_id=None, top_k=3, search_method="semantic_search"):
        """使用知识库检索接口实现对话功能
        
        Args:
            message: 用户消息
            conversation_id: 对话ID（可选，用于前端跟踪对话）
            top_k: 返回结果数量，默认为3
            search_method: 检索方法，默认为"semantic_search"
            
        Returns:
            包含对话响应的字典
        """
        # 使用检索接口获取相关文档片段
        retrieve_result = self.query_knowledge_base(
            query=message, 
            top_k=top_k, 
            search_method=search_method
        )
        
        # 检查是否有错误
        if 'error' in retrieve_result:
            return retrieve_result
            
        # 提取检索结果
        records = retrieve_result.get('records', [])
        
        if not records:
            return {
                "query": message,
                "conversation_id": conversation_id,
                "response": "抱歉，我没有找到相关信息。",
                "sources": []
            }
            
        # 构建响应
        sources = []
        context_text = ""
        
        for i, record in enumerate(records):
            segment = record.get('segment', {})
            content = segment.get('content', '')
            document = segment.get('document', {})
            document_name = document.get('name', '未知文档')
            score = record.get('score', 0)
            
            # 添加到上下文
            context_text += f"{content}\n\n"
            
            # 添加到来源列表
            sources.append({
                "document_name": document_name,
                "content": content,
                "score": score
            })
        
        # 根据检索到的内容构建简单响应
        response = f"根据知识库检索，以下是相关信息：\n\n{context_text}"
        
        return {
            "query": message,
            "conversation_id": conversation_id or "new_conversation",
            "response": response,
            "sources": sources
        }


if __name__ == "__main__":
    # 初始化 DifyService 实例
    dify_service = DifyService()

    # 测试 query_knowledge_base 方法
    test_query = """该文档描述了WEB端资产模块的需求设计，核心内容包括：  
1. **功能范围**：支持用户查看账户资产、持仓及资金号信息，与APP共用接口，涵盖资产、持仓、账户（资金号）三大组件。  
2. **关键场景**：  
   - 按选中资金号展示资产数据，区分现金/融资账户，支持市场切换与资金号动态匹配。  
   - 提供首设密码、补开市场（美股）及开户流程入口。  
3. **交互规则**："""
    result = dify_service.query_knowledge_base(
        query=test_query,

    )

    # 输出结果
    print("查询结果：")
    print(json.dumps(result, indent=4, ensure_ascii=False))
