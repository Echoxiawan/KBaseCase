import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ..models import db, KnowledgeFile
from ..services.dify_service import DifyService

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')

@knowledge_bp.route('/files', methods=['GET'])
def get_knowledge_files():
    """获取知识库文件列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        keyword = request.args.get('keyword', None)
        
        # 从Dify API获取文件列表
        dify_service = DifyService()
        result = dify_service.get_knowledge_files(page=page, limit=limit, keyword=keyword)
        
        # 同步本地数据库
        if 'data' in result:
            dify_files = result['data']
            
            # 获取所有本地文件记录
            local_files = {file.dify_file_id: file for file in KnowledgeFile.query.all() if file.dify_file_id}
            
            # 更新状态或添加新文件
            for dify_file in dify_files:
                file_id = dify_file.get('id')
                if file_id in local_files:
                    # 更新状态
                    local_file = local_files[file_id]
                    local_file.status = dify_file.get('indexing_status', 'processed')
                    db.session.add(local_file)
                else:
                    # 添加新文件记录
                    new_file = KnowledgeFile(
                        file_name=dify_file.get('name', 'Unknown'),
                        file_type=os.path.splitext(dify_file.get('name', ''))[1].lower().replace('.', ''),
                        file_size=0,  # API不返回文件大小，设为0
                        dify_file_id=file_id,
                        status=dify_file.get('indexing_status', 'processed')
                    )
                    db.session.add(new_file)
                    
            db.session.commit()
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@knowledge_bp.route('/upload', methods=['POST'])
def upload_knowledge_file():
    """上传文件到知识库"""
    if 'file' not in request.files:
        return jsonify({"error": "没有文件"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
        
    # 创建上传目录
    upload_folder = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # 保存文件
    #filename = secure_filename(file.filename)
    filename = file.filename
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    try:
        # 获取索引技术和处理规则参数
        indexing_technique = request.form.get('indexing_technique', 'high_quality')
        process_rule_mode = request.form.get('process_rule_mode', 'custom')
        
        # 获取可能的embedding模型参数
        embedding_model = request.form.get('embedding_model','bge-m3')
        embedding_model_provider = request.form.get('embedding_model_provider','langgenius/huggingface_tei/huggingface_tei')
        
        # 构建处理规则
        process_rule = {
            "mode": process_rule_mode
        }
        
        # 如果是自定义模式，添加更多规则
        if process_rule_mode == 'custom':
            # 获取分段规则
            separator = request.form.get('separator', '\n\n')
            max_tokens = int(request.form.get('max_tokens', '1024'))
            
            # 获取预处理规则
            remove_extra_spaces = True
            remove_urls_emails = True
            
            # 构建完整的处理规则
            pre_processing_rules = []
            if remove_extra_spaces:
                pre_processing_rules.append({
                    "id": "remove_extra_spaces",
                    "enabled": True
                })
            if remove_urls_emails:
                pre_processing_rules.append({
                    "id": "remove_urls_emails",
                    "enabled": True
                })
                
            process_rule = {
                "mode": "custom",
                "rules": {
                    "pre_processing_rules": pre_processing_rules,
                    "segmentation": {
                        "separator": separator,
                        "max_tokens": max_tokens
                    }
                }
            }
            
        # 上传到Dify知识库
        dify_service = DifyService()
        result = dify_service.upload_file_to_knowledge_base(
            file_path, 
            filename,
            indexing_technique=indexing_technique,
            process_rule=process_rule,
            embedding_model=embedding_model,
            embedding_model_provider=embedding_model_provider
        )
        
        # 检查是否上传成功
        if 'error' in result:
            return jsonify(result), 500
            
        # 保存文件记录到数据库
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(filename)[1].lower().replace('.', '')
        
        # 从响应中获取document和batch信息
        document = result.get('document', {})
        batch = result.get('batch', '')
        
        knowledge_file = KnowledgeFile(
            file_name=filename,
            file_type=file_type,
            file_size=file_size,
            dify_file_id=document.get('id'),
            status=document.get('indexing_status', 'waiting')  # 初始状态为waiting
        )
        
        db.session.add(knowledge_file)
        db.session.commit()
        
        return jsonify({
            "message": "文件已上传到知识库",
            "file": knowledge_file.to_dict(),
            "batch": batch,  # 返回批次号，用于查询索引状态
            "dify_response": result
        }), 201
    except Exception as e:
        db.session.rollback()
        error_message = f"上传文件失败: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500
    finally:
        # 清理上传的文件
        if os.path.exists(file_path):
            os.remove(file_path)

@knowledge_bp.route('/delete/<string:file_id>', methods=['DELETE'])
def delete_knowledge_file(file_id):
    """从知识库中删除文件"""
    try:
        # 从Dify知识库删除
        dify_service = DifyService()
        result = dify_service.delete_file_from_knowledge_base(file_id)
        
        # 删除本地数据库记录
        knowledge_file = KnowledgeFile.query.filter_by(dify_file_id=file_id).first()
        if knowledge_file:
            db.session.delete(knowledge_file)
            db.session.commit()
            
        return jsonify({
            "message": "文件已从知识库中删除",
            "success": True
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
        
@knowledge_bp.route('/status/<string:batch>', methods=['GET'])
def get_indexing_status(batch):
    """获取文档索引状态"""
    try:
        dify_service = DifyService()
        result = dify_service.get_document_indexing_status(batch)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 