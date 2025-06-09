import requests
import json
from ..config import get_config
from .vector_store_service import VectorStoreService
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage
from typing import List, Optional

class AIService:
    """AI服务，负责生成测试用例"""
    
    def __init__(self):
        config = get_config()
        self.api_key = config.AI_API_KEY
        self.base_url = config.AI_BASE_URL
        self.model = config.AI_MODEL
        self.max_tokens = config.AI_MAX_TOKENS
        
        if not self.api_key:
            raise ValueError("AI API密钥未配置")
            
        # 初始化LangChain的ChatOpenAI客户端
        self.chat_model = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            max_tokens=self.max_tokens,
            temperature=0.7,
            request_timeout=60
        )
        
    def summarize_text(self, document_text, max_length=200):
        """
        生成文档摘要，限制在指定字数以内
        
        Args:
            document_text: 需要总结的文档文本
            max_length: 摘要最大字数，默认200字
            
        Returns:
            生成的摘要文本，如果失败则返回文档前200个字符
        """
        # 创建摘要生成的提示
        prompt = f"""
        请对以下文档内容生成一个简洁的摘要，不超过{max_length}字。摘要应该包含文档的核心内容和关键信息。
        
        文档内容：
        {document_text[:5000]}  # 限制输入长度，避免超出token限制
        """
        
        try:
            # 创建一个临时的ChatOpenAI实例，使用较低的temperature
            summarizer = ChatOpenAI(
                model=self.model,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                max_tokens=300,  # 为摘要分配足够的token
                temperature=0.5  # 使用较低的temperature以获得更确定性的摘要
            )
            
            # 创建人类消息
            human_message = HumanMessage(content=prompt)
            
            # 使用LangChain的ChatOpenAI调用API
            response = summarizer.invoke([human_message])
            
            # 提取生成的摘要
            summary = response.content.strip()
            
            # 确保摘要不超过指定长度
            if len(summary) > max_length:
                summary = summary[:max_length]
                
            return summary
            
        except Exception as e:
            print(f"生成摘要失败: {str(e)}")
            # 失败时返回文档前200个字符
            return document_text[:max_length]
            
    def generate_test_cases(self, document_text, knowledge_base_results=None, case_count=100):
        """
        生成测试用例
        
        Args:
            document_text: 文档文本
            knowledge_base_results: 知识库查询结果，默认为None
            case_count: 期望生成的测试用例数量，默认为100
            
        Returns:
            生成的测试用例（JSON格式）
        """
        # 使用向量存储处理文档
        vector_store = VectorStoreService()
        vector_store.process_document(document_text)
        
        # 创建提示，使用文档的摘要作为查询
        summary_query = self._create_summary_query(document_text)
        relevant_context = vector_store.get_relevant_context(summary_query, max_tokens=int(self.max_tokens * 0.7))
        
        # 创建完整的提示
        prompt = self._create_test_case_prompt(relevant_context, knowledge_base_results, case_count)
        
        # 检查提示长度，如果太长则进一步处理
        if len(prompt.split()) > self.max_tokens * 0.75:  # 留出空间给响应
            return self._handle_long_context(relevant_context, knowledge_base_results, case_count)
            
        return self._call_ai_api(prompt)
        
    def _create_summary_query(self, document_text):
        """从文档中创建摘要查询"""
        # 使用文档的前300个字符作为摘要查询
        # 这是一个简单的方法，可以根据需要改进
        summary = document_text[:300].replace('\n', ' ')
        return f"需求文档摘要: {summary}"
        
    def _create_test_case_prompt(self, document_text, knowledge_base_results=None, case_count=100):
        """
        创建测试用例生成的提示
        
        Args:
            document_text: 文档文本
            knowledge_base_results: 知识库查询结果，默认为None
            case_count: 期望生成的测试用例数量，默认为100
            
        Returns:
            生成提示字符串
        """
        prompt = f"""
        你是一个专业的测试工程师，负责根据需求文档生成高质量的测试用例。
        请根据以下需求文档内容，生成全面的测试用例。每个测试用例应包括：
        1. 标题（简洁明了）
        2. 描述（测试的目的）
        3. 前置条件（测试执行前需要满足的条件）
        4. 测试步骤（详细的操作步骤，每步一行，以数字编号）
        5. 预期结果（每个步骤对应的预期结果）
        
        请生成大约{case_count}个测试用例，确保覆盖需求文档中的所有重要功能和场景。测试用例数量应尽可能不少于{case_count}个，除非需求文档内容确实无法支持这么多测试用例。
        
        需求文档内容：
        """
        prompt += document_text
        
        if knowledge_base_results:
            prompt += "\n\n参考知识库信息：\n"
            for result in knowledge_base_results:
                if 'content' in result:
                    prompt += result['content'] + "\n\n"
                    
        prompt += """
        请以JSON格式输出测试用例，格式如下：
        [
            {
                "title": "测试用例标题",
                "description": "测试用例描述",
                "preconditions": "前置条件",
                "steps": "1. 步骤1\\n2. 步骤2\\n3. 步骤3",
                "expected_results": "1. 预期结果1\\n2. 预期结果2\\n3. 预期结果3"
            },
            ...
        ]
        """
        
        return prompt
        
    def _handle_long_context(self, document_text, knowledge_base_results=None, case_count=100):
        """
        处理超长上下文的情况
        
        Args:
            document_text: 文档文本
            knowledge_base_results: 知识库查询结果，默认为None
            case_count: 期望生成的测试用例数量，默认为100
            
        Returns:
            生成的测试用例（JSON格式）
        """
        # 计算可用的token预算
        max_available_tokens = int(self.max_tokens * 0.7)  # 留出30%给响应
        
        # 1. 动态生成查询关键词
        queries = self._generate_dynamic_queries(document_text)
        
        # 2. 提取文档关键部分
        extracted_context = self._extract_key_sections(document_text, queries, max_available_tokens)
        
        # 3. 处理知识库结果
        # 如果有知识库结果，根据剩余token预算决定使用多少
        processed_kb_results = None
        if knowledge_base_results:
            # 估算已使用的token数
            context_tokens = len(extracted_context.split())
            remaining_tokens = max_available_tokens - context_tokens
            
            # 如果剩余token足够，处理知识库结果
            if remaining_tokens > 500:  # 确保至少有一些token用于知识库结果
                # 估算每个知识库结果的平均token数
                kb_tokens = 0
                for result in knowledge_base_results:
                    if 'content' in result:
                        kb_tokens += len(result['content'].split())
                
                if kb_tokens > 0 and len(knowledge_base_results) > 0:
                    avg_tokens_per_result = kb_tokens / len(knowledge_base_results)
                    # 计算可以包含多少知识库结果
                    num_results = min(len(knowledge_base_results), int(remaining_tokens / avg_tokens_per_result))
                    processed_kb_results = knowledge_base_results[:num_results]
                else:
                    processed_kb_results = knowledge_base_results
            else:
                # 如果剩余token不足，只使用第一个知识库结果
                processed_kb_results = knowledge_base_results[:1] if knowledge_base_results else None
        
        # 4. 创建提示并调用AI API
        prompt = self._create_test_case_prompt(extracted_context, processed_kb_results, case_count)
        return self._call_ai_api(prompt)
        
    def _call_ai_api(self, prompt):
        """调用AI API，使用LangChain"""
        try:
            # 创建人类消息
            human_message = HumanMessage(content=prompt)
            
            # 使用LangChain的ChatOpenAI调用API
            response = self.chat_model.invoke([human_message])
            
            # 提取生成的内容
            content = response.content
            
            # 尝试解析JSON
            try:
                # 查找JSON部分
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    test_cases = json.loads(json_str)
                    return test_cases
                else:
                    return {"error": "无法在AI响应中找到JSON格式的测试用例"}
            except json.JSONDecodeError:
                return {"error": "无法解析AI生成的测试用例JSON", "raw_content": content}
        
        except Exception as e:
            print(f"调用AI API失败: {str(e)}")
            return {"error": str(e)}

    def _generate_dynamic_queries(self, document_text, base_queries=None):
        """
        根据文档内容动态生成查询关键词
        
        Args:
            document_text: 文档文本
            base_queries: 基础查询关键词列表，默认为None
            
        Returns:
            查询关键词列表
        """
        # 如果提供了基础查询关键词，使用它们作为起点
        queries = base_queries or [
            "系统功能需求",
            "用户界面要求",
            "数据处理流程",
            "系统交互",
            "错误处理",
            "性能要求"
        ]
        
        # 尝试从文档中提取可能的关键词
        try:
            # 使用简单的启发式方法从文档中提取可能的关键词
            # 1. 查找标题样式的文本（全大写、以数字开头的行等）
            lines = document_text.split('\n')
            for line in lines:
                line = line.strip()
                # 跳过空行和太长的行
                if not line or len(line) > 100:
                    continue
                    
                # 检查是否可能是标题
                if (line.isupper() or  # 全大写
                    (line[0].isdigit() and '.' in line[:5]) or  # 数字编号开头 (如 "1. 标题")
                    line.startswith('#') or  # Markdown 风格标题
                    line.endswith(':') or  # 冒号结尾的可能是标题
                    (len(line) < 50 and (line.endswith('要求') or line.endswith('功能') or line.endswith('规范')))):  # 短行以特定词结尾
                    
                    # 清理并添加到查询列表
                    clean_line = line.strip('#.:-*[] \t')
                    if clean_line and len(clean_line) > 3 and clean_line not in queries:
                        queries.append(clean_line)
            
            # 2. 限制查询数量，避免过多
            if len(queries) > 15:
                # 保留原始的基础查询和一些提取的查询
                original_count = len(base_queries) if base_queries else 6
                queries = queries[:original_count] + queries[original_count:15]
                
        except Exception as e:
            print(f"动态生成查询关键词时出错: {str(e)}")
            # 出错时返回基础查询关键词
            
        return queries 

    def _extract_key_sections(self, document_text, queries, max_tokens):
        """
        从文档中提取关键部分
        
        Args:
            document_text: 文档文本
            queries: 查询关键词列表
            max_tokens: 最大token数
            
        Returns:
            提取的关键部分文本
        """
        # 使用LangChain的RecursiveCharacterTextSplitter进行文本分块
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=lambda x: len(x.split())  # 简单估算token数量
        )
        
        # 分割文档
        chunks = text_splitter.split_text(document_text)
        
        # 如果文档太短，不需要进一步处理
        if len(chunks) <= 3:
            # 确保不超过最大token数
            total_tokens = sum(len(chunk.split()) for chunk in chunks)
            if total_tokens <= max_tokens:
                return document_text
            
        # 创建向量存储
        vector_store = VectorStoreService()
        
        # 处理每个文档块
        for chunk in chunks:
            vector_store.process_document(chunk)
            
        # 使用查询关键词检索相关内容
        combined_context = ""
        tokens_used = 0
        max_tokens_per_query = max(int(max_tokens / len(queries)), 500)  # 确保每个查询至少有一些token
        
        for query in queries:
            # 为每个查询分配token预算
            context = vector_store.get_relevant_context(query, max_tokens=max_tokens_per_query)
            if context:
                # 添加标题和内容
                section = f"--- {query} 相关内容 ---\n{context}\n\n"
                section_tokens = len(section.split())
                
                # 检查是否超出总token预算
                if tokens_used + section_tokens > max_tokens:
                    # 如果添加整个部分会超出预算，尝试添加部分内容
                    words = section.split()
                    remaining_tokens = max_tokens - tokens_used
                    if remaining_tokens > 50:  # 确保至少添加一些有意义的内容
                        combined_context += " ".join(words[:remaining_tokens]) + "...\n\n"
                    break
                
                combined_context += section
                tokens_used += section_tokens
                
                # 如果已经使用了足够多的token，停止添加
                if tokens_used >= max_tokens:
                    break
        
        # 如果没有提取到足够的内容，添加文档的开头和结尾
        if tokens_used < max_tokens * 0.5:
            remaining_tokens = max_tokens - tokens_used
            
            # 计算开头和结尾各分配多少token
            head_tokens = min(int(remaining_tokens * 0.7), 2000)  # 开头分配更多
            tail_tokens = min(int(remaining_tokens * 0.3), 1000)  # 结尾分配较少
            
            # 提取文档开头
            head_text = " ".join(document_text.split()[:head_tokens])
            
            # 提取文档结尾
            all_words = document_text.split()
            if len(all_words) > head_tokens + tail_tokens:
                tail_text = " ".join(all_words[-tail_tokens:])
                combined_context += f"\n\n--- 文档开头 ---\n{head_text}\n\n--- 文档结尾 ---\n{tail_text}"
            else:
                # 如果文档不够长，只添加未包含的部分
                remaining_text = " ".join(all_words[head_tokens:])
                combined_context += f"\n\n--- 文档其余部分 ---\n{remaining_text}"
        
        return combined_context.strip() 

    def review_test_cases(self, test_cases, document_text, knowledge_base_results=None, case_count=100):
        """
        对初步生成的测试用例进行评审，查缺补漏，生成最终测试用例
        
        Args:
            test_cases: 初步生成的测试用例（JSON格式）
            document_text: 原始需求文档
            knowledge_base_results: 知识库查询结果，默认为None
            case_count: 期望生成的测试用例数量，默认为100
            
        Returns:
            评审后的测试用例（JSON格式）
        """
        # 将测试用例转换为字符串
        test_cases_str = json.dumps(test_cases, ensure_ascii=False, indent=2)
        
        # 检查文档长度，估算token数量
        doc_tokens = len(document_text.split())
        max_available_tokens = int(self.max_tokens * 0.7)  # 留出30%给响应
        
        # 如果文档太长，需要进行处理
        if doc_tokens > max_available_tokens * 0.6:  # 如果文档占用超过可用token的60%，则处理
            print(f"文档太长 ({doc_tokens} tokens)，进行长文档处理")
            
            # 1. 动态生成查询关键词
            queries = self._generate_dynamic_queries(document_text)
            
            # 2. 提取文档关键部分
            # 为测试用例和提示保留一些token
            test_cases_tokens = len(test_cases_str.split())
            prompt_overhead_tokens = 500  # 评审提示的固定部分大约需要的token数
            
            # 计算文档可用的token预算
            doc_token_budget = max_available_tokens - test_cases_tokens - prompt_overhead_tokens
            doc_token_budget = max(doc_token_budget, int(max_available_tokens * 0.3))  # 确保至少有一些token用于文档
            
            # 提取文档关键部分
            extracted_document = self._extract_key_sections(document_text, queries, doc_token_budget)
            
            # 3. 处理知识库结果
            processed_kb_results = self._process_knowledge_base_for_review(extracted_document, knowledge_base_results, max_available_tokens)
            
            # 4. 创建评审提示并调用API
            prompt = self._create_review_prompt(test_cases_str, extracted_document, processed_kb_results, case_count)
        else:
            # 文档不长，使用完整文档
            prompt = self._create_review_prompt(test_cases_str, document_text, knowledge_base_results, case_count)
        
        # 调用API获取评审结果
        try:
            # 创建一个专门用于评审的ChatOpenAI实例
            reviewer = ChatOpenAI(
                model=self.model,
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                max_tokens=self.max_tokens,
                temperature=0.5  # 使用较低的temperature以获得更确定性的结果
            )
            
            # 创建人类消息
            human_message = HumanMessage(content=prompt)
            
            # 调用API
            response = reviewer.invoke([human_message])
            
            # 提取生成的内容
            content = response.content
            
            # 尝试解析JSON
            try:
                # 查找JSON部分
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    reviewed_test_cases = json.loads(json_str)
                    return reviewed_test_cases
                else:
                    print("无法在评审响应中找到JSON格式的测试用例，返回原始测试用例")
                    return test_cases
            except json.JSONDecodeError:
                print(f"无法解析评审生成的测试用例JSON，返回原始测试用例")
                return test_cases
                
        except Exception as e:
            print(f"测试用例评审失败: {str(e)}")
            # 评审失败时返回原始测试用例
            return test_cases
            
    def _process_knowledge_base_for_review(self, extracted_document, knowledge_base_results, max_tokens):
        """
        为评审处理知识库结果，考虑token预算
        
        Args:
            extracted_document: 已提取的文档内容
            knowledge_base_results: 原始知识库结果
            max_tokens: 最大可用token数
            
        Returns:
            处理后的知识库结果
        """
        if not knowledge_base_results:
            return None
            
        # 估算已使用的token数
        doc_tokens = len(extracted_document.split())
        remaining_tokens = max_tokens - doc_tokens - 500  # 减去提示的固定部分
        
        # 如果剩余token不足，返回有限的知识库结果
        if remaining_tokens < 500:
            return knowledge_base_results[:1] if knowledge_base_results else None
            
        # 估算每个知识库结果的平均token数
        kb_tokens = 0
        for result in knowledge_base_results:
            if 'content' in result:
                kb_tokens += len(result['content'].split())
        
        # 计算可以包含多少知识库结果
        if kb_tokens > 0 and len(knowledge_base_results) > 0:
            avg_tokens_per_result = kb_tokens / len(knowledge_base_results)
            num_results = min(len(knowledge_base_results), int(remaining_tokens / avg_tokens_per_result))
            return knowledge_base_results[:num_results]
        
        return knowledge_base_results
        
    def _create_review_prompt(self, test_cases_str, document_text, knowledge_base_results=None, case_count=10):
        """
        创建测试用例评审的提示
        
        Args:
            test_cases_str: 测试用例JSON字符串
            document_text: 处理后的文档文本
            knowledge_base_results: 处理后的知识库结果
            case_count: 期望生成的测试用例数量，默认为10
            
        Returns:
            评审提示字符串
        """
        prompt = f"""
        你是一个资深的测试专家和软件评审员，负责对测试用例进行严格评审。
        我已经基于需求文档生成了一组初步的测试用例，现在需要你对这些测试用例进行全面评审，查缺补漏，确保测试覆盖了所有重要场景。
        
        请特别关注以下方面：
        1. 功能完整性：是否测试了所有功能点和业务流程
        2. 边界条件：是否考虑了各种边界情况和异常情况
        3. 数据验证：是否验证了各种数据输入和输出
        4. 用户场景：是否覆盖了所有可能的用户交互场景
        5. 安全性考虑：是否包含必要的安全测试
        6. 测试步骤的清晰度和可执行性
        7. 预期结果的明确性和可验证性
        
        请确保最终测试用例的数量尽可能不少于{case_count}个，除非需求文档确实无法支持这么多测试用例。
        如果初步生成的测试用例数量不足{case_count}个，请尝试添加新的测试用例以达到预期数量。
        
        初步生成的测试用例：
        {test_cases_str}
        
        原始需求文档：
        {document_text}
        """
        
        # 添加知识库内容
        if knowledge_base_results:
            prompt += "\n\n参考知识库信息：\n"
            for result in knowledge_base_results:
                if 'content' in result:
                    content_text = result['content']
                    # 如果单个知识库条目太长，进行截断
                    if len(content_text.split()) > 500:
                        content_text = " ".join(content_text.split()[:500]) + "..."
                    prompt += content_text + "\n\n"
        
        prompt += """
        请对初步测试用例进行评审，并返回改进后的完整测试用例集。你可以：
        1. 保留原有的好的测试用例
        2. 改进现有的不完善测试用例
        3. 添加新的测试用例以覆盖遗漏的场景
        4. 删除不必要或重复的测试用例
        
        请以JSON格式返回评审后的完整测试用例集，格式与初步测试用例相同：
        [
            {
                "title": "测试用例标题",
                "description": "测试用例描述",
                "preconditions": "前置条件",
                "steps": "1. 步骤1\\n2. 步骤2\\n3. 步骤3",
                "expected_results": "1. 预期结果1\\n2. 预期结果2\\n3. 预期结果3"
            },
            ...
        ]
        
        只返回JSON格式的测试用例集，不要添加任何额外的说明或解释。
        """
        
        return prompt 