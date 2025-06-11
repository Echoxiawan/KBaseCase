# 测试用例生成工具

基于知识库的测试用例自动生成系统，支持从文档中提取信息并结合Dify知识库生成高质量测试用例。

## 核心功能

### 文档处理
- **多格式支持**：解析PDF、DOCX、Markdown格式文档
- **OCR集成**：使用PaddleOCR提取文档图片中的文本内容
- **智能文本分析**：自动提取文档关键信息用于测试用例生成

### 知识库管理（基于Dify API）
- **文件上传**：支持向Dify知识库添加各类文档
- **文件查看**：浏览已上传的Dify知识库文件，包括处理状态和索引情况
- **文件删除**：从Dify知识库中移除不需要的文档
- **知识检索**：利用Dify API进行高效的语义检索，增强测试用例生成质量

### 测试用例生成
- **AI生成**：基于文档内容和Dify知识库信息自动生成测试用例
- **批次管理**：按批次组织和管理测试用例
- **质量评审**：支持对生成的测试用例进行人工审核（通过/拒绝）
- **导出功能**：将测试用例导出为Excel格式，方便集成到测试流程

## 技术架构

- **后端**：Flask + SQLAlchemy
- **AI集成**：OpenAI API + Dify知识库API
- **文档处理**：PyPDF2, python-docx, markdown, PaddleOCR
- **前端**：原生HTML/CSS/JavaScript，无框架依赖
- **数据存储**：MySQL数据库

## 安装指南

### 系统要求
- Python 3.11+
- MySQL 5.7+
- PaddleOCR (用于图片文本提取)
- Dify API账户（用于知识库管理）

### 步骤

1. **克隆项目**
```bash
git clone https://github.com/Echoxiawan/KBaseCase.git
cd KBaseCase
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
创建`.env`文件，参考以下配置：
```
# Flask配置
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=ai_testcase_generator

# Dify API配置（必需）
DIFY_API_KEY=your_dify_api_key
DIFY_API_BASE_URL=https://api.dify.ai/v1
DIFY_DATASET_ID=your_knowledge_base_id

# AI模型配置
AI_MODEL=gpt-3.5-turbo
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=your_openai_api_key
AI_MAX_TOKENS=4096

# OCR配置，开启此功能建议16G以上内存，最好使用gpu，否则建议关闭
OCR_ENABLED=False         # OCR总开关
OCR_LANG=ch              # OCR语言，默认中文
OCR_CONFIDENCE_THRESHOLD=0.5    # OCR识别结果的置信度阈值
OCR_MAX_RETRIES=3        # OCR处理失败时的最大重试次数

# 日志配置
LOG_LEVEL=INFO           # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=app.log         # 日志文件路径
```

4. **初始化数据库**
```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE ai_testcase_generator CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 初始化表结构
python -m app.utils.db_init
```

5. **运行应用**
```bash
python run.py
```
应用将在 http://localhost:5000 运行。

## 使用指南

### 首页（测试用例生成）

1. **上传文档**：
   - 点击"选择文件"或拖拽文件到上传区域
   - 支持的格式：PDF、DOCX、MD
   - 填写批次名称和描述（可选）
   - 设置期望生成的测试用例数量
   - 点击"上传并生成测试用例"

2. **批次管理**：
   - 查看所有测试用例批次
   - 筛选：使用顶部筛选器按日期或状态筛选批次
   - 搜索：使用搜索框查找特定批次
   - 操作：
     - 查看：进入批次详情页查看测试用例
     - 导出：将批次中的测试用例导出为Excel
     - 删除：删除整个批次及其测试用例

### 测试用例详情页

1. **批次信息**：
   - 显示批次名称、描述和统计信息（总数、已审核、已通过、已拒绝）

2. **测试用例列表**：
   - 筛选：使用筛选器查看"全部"、"待审核"、"已通过"或"已拒绝"的测试用例
   - 搜索：使用搜索框查找特定测试用例
   - 排序：按标题或状态排序

3. **测试用例操作**：
   - 审核：点击"通过"或"拒绝"按钮更改测试用例状态
   - 查看详情：点击测试步骤或预期结果展开查看详细内容
   - 批量操作：选择多个测试用例进行批量通过或拒绝

4. **导出功能**：
   - 点击"导出Excel"按钮将当前批次的测试用例导出为Excel文件

### Dify知识库管理

1. **上传文件**：
   - 点击"选择文件"或拖拽文件到上传区域
   - 支持的格式：PDF、DOCX、MD等
   - 点击"上传到知识库"

2. **文件列表**：
   - 查看所有Dify知识库文件
   - 筛选：使用筛选器按处理状态查看文件
   - 搜索：使用搜索框查找特定文件
   - 排序：按日期、名称或大小排序

3. **文件操作**：
   - 删除：从Dify知识库中删除文件

## 最佳实践

1. **文档准备**：
   - 确保文档内容清晰、结构化，以获得更好的测试用例

2. **Dify知识库管理**：
   - 上传相关领域的文档到Dify知识库，以增强测试用例生成质量
   - 定期更新知识库内容，保持信息的时效性
   - 确保Dify API密钥和知识库ID配置正确

3. **测试用例审核**：
   - 审核生成的测试用例，确保其质量和适用性
   - 对不符合要求的测试用例进行拒绝，系统会记录这些反馈

4. **系统优化**：
   - 调整OCR参数以提高图片文本识别质量
   - 根据需要调整生成的测试用例数量

## 故障排除

1. **OCR问题**：
   - 如遇OCR识别问题，可尝试调整OCR_CONFIDENCE_THRESHOLD参数
   - 如不需要OCR功能，可设置OCR_ENABLED=False

2. **API限制**：
   - 如遇到AI模型API或Dify API限制，可适当降低生成的测试用例数量
   - 确保API密钥配置正确且有足够的额度

3. **文件处理错误**：
   - 确保上传的文件格式正确且未损坏
   - 检查文件大小是否超过系统或Dify API限制

4. **数据库问题**：
   - 确保数据库连接配置正确
   - 检查数据库服务是否正常运行

5. **Dify知识库问题**：
   - 检查Dify API连接状态
   - 确认知识库ID是否正确
   - 验证上传的文件是否符合Dify知识库要求

## 系统限制

1. **文件大小**：建议单个文件不超过20MB
2. **文件格式**：仅支持PDF、DOCX和MD格式
3. **API依赖**：需要有效的OpenAI API和Dify API密钥
4. **OCR支持**：主要针对中文文本优化，其他语言可能需要额外配置
5. **Dify知识库限制**：受Dify平台本身的文件大小、数量和API调用频率限制

## WeChat Contact

<img src="contact.jpg" alt="Contact QR Code" style="width: 30%; height: auto;">

## 许可证

[MIT](LICENSE) 
