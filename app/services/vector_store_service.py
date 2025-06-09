import os
import faiss
import numpy as np
import torch
import logging
import traceback
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document as LangchainDocument

# 配置日志记录
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class VectorStoreService:
    """向量存储服务，用于文档向量化和相似度搜索"""
    
    # 类级别变量，用于跟踪初始化状态
    _initialized = False
    _init_error = None
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """初始化向量存储服务
        
        Args:
            model_name: 使用的Sentence Transformer模型名称
        """
        # 如果类已经尝试初始化但失败了，直接抛出之前的错误
        if VectorStoreService._init_error is not None:
            raise RuntimeError(f"SentenceTransformer初始化失败: {VectorStoreService._init_error}")
            
        # 如果类已经成功初始化，直接返回
        if VectorStoreService._initialized:
            return
            
        # 明确指定设备为CPU，避免meta tensor问题
        device = 'cpu'
        
        # 设置torch设备
        torch.set_grad_enabled(False)  # 禁用梯度计算，减少内存使用
        
        print("正在初始化SentenceTransformer模型...")
        
        # 使用明确的设备参数初始化模型
        model_initialized = False
        
        # 尝试方案1：使用to_empty()方法（错误信息中明确推荐的方法）
        if not model_initialized:
            try:
                logging.info("尝试方案1：使用to_empty()方法初始化...")
                
                # 先初始化模型，不指定设备
                self.model = SentenceTransformer(model_name)
                
                # 使用to_empty()方法代替to()
                try:
                    # 检查PyTorch版本
                    logging.info(f"PyTorch版本: {torch.__version__}")
                    
                    # 对于较新版本的PyTorch，使用to_empty
                    if hasattr(self.model, 'to_empty'):
                        logging.info("检测到to_empty方法，尝试使用...")
                        self.model = self.model.to_empty(device='cpu')
                        model_initialized = True
                        VectorStoreService._initialized = True
                        logging.info("使用to_empty()方法初始化成功")
                    else:
                        # 如果to_empty不存在，尝试使用模块级别的to_empty
                        logging.info("模型对象没有to_empty方法，尝试使用torch.nn.Module.to_empty...")
                        if hasattr(torch.nn.Module, 'to_empty'):
                            self.model = torch.nn.Module.to_empty(self.model, device='cpu')
                            model_initialized = True
                            VectorStoreService._initialized = True
                            logging.info("使用torch.nn.Module.to_empty()方法初始化成功")
                        else:
                            logging.warning("to_empty()方法不存在，尝试其他方法...")
                except AttributeError as ae:
                    # 如果to_empty不存在，说明PyTorch版本较旧，继续尝试其他方法
                    logging.warning(f"to_empty()方法不存在: {str(ae)}")
                    logging.warning("尝试其他方法...")
                
            except Exception as e:
                logging.error(f"使用to_empty()方法初始化失败: {str(e)}")
                logging.error(f"错误详情: {traceback.format_exc()}")
        
        # 尝试方案2：添加额外的配置参数，避免meta tensor问题
        if not model_initialized:
            try:
                logging.info("尝试方案2：使用device参数初始化...")
                torch.set_default_tensor_type(torch.FloatTensor)  # 确保默认tensor类型正确
                
                # 尝试初始化模型
                self.model = SentenceTransformer(model_name, device=device)
                
                # 标记为成功初始化
                model_initialized = True
                VectorStoreService._initialized = True
                logging.info("使用device参数初始化成功")
                
            except Exception as e:
                logging.error(f"使用device参数初始化失败: {str(e)}")
                logging.error(f"错误详情: {traceback.format_exc()}")
        
        # 尝试方案3：使用torch.device
        if not model_initialized:
            try:
                logging.info("尝试方案3：使用torch.device初始化...")
                torch_device = torch.device('cpu')
                self.model = SentenceTransformer(model_name, device=torch_device)
                model_initialized = True
                VectorStoreService._initialized = True
                logging.info("使用torch.device初始化成功")
                
            except Exception as e2:
                logging.error(f"使用torch.device初始化失败: {str(e2)}")
                logging.error(f"错误详情: {traceback.format_exc()}")
        
        # 尝试方案4：先初始化，然后使用自定义to方法
        if not model_initialized:
            try:
                logging.info("尝试方案4：使用自定义to方法...")
                
                # 先不指定设备参数初始化
                self.model = SentenceTransformer(model_name)
                
                # 自定义to方法，避免使用内置的to方法
                def custom_to(module, device):
                    # 遍历模块的所有参数和缓冲区，手动将它们移动到指定设备
                    for param in module.parameters():
                        if hasattr(param, 'data'):
                            param.data = param.data.to(device)
                    for buf in module.buffers():
                        if hasattr(buf, 'data'):
                            buf.data = buf.data.to(device)
                    return module
                
                # 使用自定义to方法
                self.model = custom_to(self.model, 'cpu')
                model_initialized = True
                VectorStoreService._initialized = True
                logging.info("使用自定义to方法初始化成功")
                
            except Exception as e3:
                logging.error(f"使用自定义to方法初始化失败: {str(e3)}")
                logging.error(f"错误详情: {traceback.format_exc()}")
        
        # 尝试方案5：完全禁用cuda，使用纯CPU模式
        if not model_initialized:
            try:
                logging.info("尝试方案5：完全禁用CUDA，使用纯CPU模式...")
                
                # 禁用CUDA
                os.environ["CUDA_VISIBLE_DEVICES"] = ""
                torch.set_num_threads(1)
                
                # 重新初始化模型
                self.model = SentenceTransformer(model_name)
                model_initialized = True
                VectorStoreService._initialized = True
                logging.info("使用纯CPU模式初始化成功")
                
            except Exception as e4:
                # 所有尝试都失败，记录错误并抛出
                error_msg = f"所有SentenceTransformer初始化尝试均失败: {str(e4)}"
                logging.error(error_msg)
                logging.error(f"错误详情: {traceback.format_exc()}")
                VectorStoreService._init_error = error_msg
                raise RuntimeError(error_msg)
        
        # 只有在模型成功初始化后，才初始化其他属性
        if model_initialized:
            logging.info("模型初始化成功，现在初始化其他属性...")
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            self.index = None
            self.documents = []
            logging.info("VectorStoreService初始化完成")
        else:
            # 这种情况理论上不会发生，因为如果所有初始化方法都失败，前面会抛出异常
            error_msg = "模型初始化失败，但没有抛出异常，这是一个意外情况"
            logging.error(error_msg)
            VectorStoreService._init_error = error_msg
            raise RuntimeError(error_msg)
        
    def process_document(self, text):
        """处理文档文本，分割并向量化
        
        Args:
            text: 文档文本内容
            
        Returns:
            分割后的文档块列表
        """
        # 分割文本为小块
        texts = self.text_splitter.split_text(text)
        
        # 创建Langchain文档对象
        documents = [LangchainDocument(page_content=t) for t in texts]
        
        # 存储文档
        self.documents = documents
        
        # 向量化文档
        self._create_index(texts)
        
        return documents
        
    def _create_index(self, texts):
        """创建FAISS索引
        
        Args:
            texts: 文本列表
        """
        if not texts:
            return
        
        try:
            print(f"开始向量化 {len(texts)} 个文本片段...")
            
            # 向量化文本
            embeddings = self.model.encode(texts, show_progress_bar=True)
            
            print(f"向量化完成，向量维度: {embeddings.shape}")
            
            # 创建FAISS索引
            vector_dimension = embeddings.shape[1]  # 获取向量维度
            self.index = faiss.IndexFlatL2(vector_dimension)
            
            # 将向量添加到索引
            self.index.add(np.array(embeddings).astype('float32'))
            
            print(f"FAISS索引创建成功，包含 {self.index.ntotal} 个向量")
            
        except Exception as e:
            error_msg = f"创建索引失败: {str(e)}"
            print(error_msg)
            # 不抛出异常，而是返回空索引，以便程序可以继续运行
            self.index = None
        
    def similarity_search(self, query, k=5):
        """执行相似度搜索
        
        Args:
            query: 查询文本
            k: 返回的最相似文档数量
            
        Returns:
            最相似的文档列表
        """
        if not self.index or not self.documents:
            print("索引或文档为空，无法执行搜索")
            return []
            
        try:
            print(f"开始向量化查询: '{query[:50]}...'")
            
            # 向量化查询
            query_vector = self.model.encode([query])
            
            # 执行搜索
            k_value = min(k, len(self.documents))
            print(f"执行FAISS搜索，k={k_value}...")
            distances, indices = self.index.search(np.array(query_vector).astype('float32'), k=k_value)
            
            # 获取相似文档
            similar_documents = [self.documents[i] for i in indices[0] if i < len(self.documents) and i >= 0]
            
            print(f"搜索完成，找到 {len(similar_documents)} 个相似文档")
            
            return similar_documents
            
        except Exception as e:
            error_msg = f"相似度搜索失败: {str(e)}"
            print(error_msg)
            return []
        
    def get_relevant_context(self, query, max_tokens=4000):
        """获取与查询相关的上下文
        
        Args:
            query: 查询文本
            max_tokens: 最大token数量
            
        Returns:
            相关上下文文本
        """
        similar_docs = self.similarity_search(query)
        
        # 合并相似文档内容
        context = ""
        token_count = 0
        
        for doc in similar_docs:
            # 简单估算token数量（按空格分词）
            doc_tokens = len(doc.page_content.split())
            
            if token_count + doc_tokens <= max_tokens:
                context += doc.page_content + "\n\n"
                token_count += doc_tokens
            else:
                # 如果添加整个文档会超出最大token数，则尝试添加部分内容
                words = doc.page_content.split()
                remaining_tokens = max_tokens - token_count
                if remaining_tokens > 0:
                    context += " ".join(words[:remaining_tokens]) + "...\n\n"
                break
                
        return context.strip() 