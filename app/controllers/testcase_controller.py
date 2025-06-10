import os
import json
import pandas as pd
import shutil
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from ..models import db, TestCase, TestCaseBatch
from ..services import document_service  # 导入全局实例
from ..services.dify_service import DifyService
from ..services.ai_service import AIService
from ..utils.logger import get_logger

# 获取日志器
logger = get_logger('testcase_controller')

testcase_bp = Blueprint('testcase', __name__, url_prefix='/api/testcase')

def _extract_knowledge_base_content(kb_results):
    """
    从Dify知识库返回的结果中提取内容
    
    Args:
        kb_results: Dify知识库查询返回的结果
        
    Returns:
        包含内容的列表，每个元素是一个字典，包含content字段
    """
    # 初始化结果列表
    content_list = []
    
    # 检查kb_results是否为字典类型
    if not isinstance(kb_results, dict):
        logger.warning("知识库返回结果格式错误：不是字典类型")
        return content_list
    
    # 从records字段中提取内容
    records = kb_results.get('records', [])
    if not records:
        logger.warning("知识库返回结果中没有records字段或records为空")
        return content_list
    
    # 遍历records，提取segment.content
    for record in records:
        segment = record.get('segment', {})
        content = segment.get('content')
        if content:
            # 创建与AIService._create_test_case_prompt方法兼容的格式
            content_list.append({'content': content})
    
    return content_list

@testcase_bp.route('/upload', methods=['POST'])
def upload_document():
    """上传文档并生成测试用例，同时将文档添加到知识库"""
    if 'file' not in request.files:
        return jsonify({"error": "没有文件"}), 400
        
    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        return jsonify({"error": "没有选择文件"}), 400
        
    # 获取批次名称、描述和期望的测试用例数量
    batch_name = request.form.get('batch_name', '未命名批次')
    batch_description = request.form.get('batch_description', '')
    case_count = request.form.get('case_count', '100')
    
    # 转换case_count为整数
    try:
        case_count = int(case_count)
        if case_count < 1:
            case_count = 100  # 如果小于1，使用默认值100
    except (ValueError, TypeError):
        case_count = 100  # 如果不是有效的整数，使用默认值100
    
    # 创建临时上传目录
    upload_folder = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # 创建文档存储目录
    documents_folder = os.path.join(current_app.root_path, 'documents')
    os.makedirs(documents_folder, exist_ok=True)
    
    # 保存所有文件到临时上传目录
    file_paths = []
    filenames = []
    combined_document_text = ""
    
    for file in files:
        filename = file.filename
        filenames.append(filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # 获取文件类型
        file_ext = os.path.splitext(filename)[1].lower().replace('.', '')
        if file_ext not in ['pdf', 'docx', 'md']:
            # 删除已上传的文件
            for path in file_paths:
                if os.path.exists(path):
                    os.remove(path)
            os.remove(file_path)  # 删除不支持的文件
            return jsonify({"error": f"不支持的文件类型: {filename}，仅支持PDF、DOCX和MD文件"}), 400
        
        file_paths.append(file_path)
    
    try:
        # 处理所有文档，合并文本内容
        for i, file_path in enumerate(file_paths):
            file_ext = os.path.splitext(filenames[i])[1].lower().replace('.', '')
            # 处理文档，使用全局document_service实例
            document_text = document_service.process_document(file_path, file_ext)
            # 添加文件分隔符和文件名
            combined_document_text += f"\n\n--- 文件: {filenames[i]} ---\n\n{document_text}"
        
        # 使用AI生成文档摘要
        ai_service = AIService()
        document_summary = ai_service.summarize_text(combined_document_text, max_length=200)
        
        # 查询Dify知识库，使用摘要而非原始文本
        dify_service = DifyService()
        kb_results = dify_service.query_knowledge_base(document_summary)
        
        # 处理知识库返回的数据，提取内容
        kb_content = _extract_knowledge_base_content(kb_results)
        
        # 生成测试用例，传递处理后的知识库内容
        test_cases = ai_service.generate_test_cases(combined_document_text, kb_content, case_count)
        
        # 检查是否有错误
        if isinstance(test_cases, dict) and 'error' in test_cases:
            return jsonify(test_cases), 500
            
        # 对初步生成的测试用例进行评审
        reviewed_test_cases = ai_service.review_test_cases(test_cases, combined_document_text, kb_content, case_count)
        
        # 创建批次
        source_document = ", ".join(filenames) if len(filenames) > 1 else filenames[0]
        batch = TestCaseBatch(name=batch_name, description=batch_description)
        db.session.add(batch)
        db.session.flush()  # 获取批次ID
        
        # 保存测试用例（使用评审后的测试用例）
        saved_test_cases = []
        for tc in reviewed_test_cases:
            test_case = TestCase(
                title=tc.get('title', '未命名测试用例'),
                description=tc.get('description', ''),
                preconditions=tc.get('preconditions', ''),
                steps=tc.get('steps', ''),
                expected_results=tc.get('expected_results', ''),
                source_document=source_document,
                batch_id=batch.id
            )
            db.session.add(test_case)
            saved_test_cases.append(test_case)
            
        # 将文件从临时上传目录移动到文档存储目录
        for i, file_path in enumerate(file_paths):
            document_path = os.path.join(documents_folder, filenames[i])
            shutil.copy2(file_path, document_path)
            
        db.session.commit()
        
        # 构建处理规则
        process_rule = {
            "mode": "custom",
            "rules": {
                "pre_processing_rules": [
                    {
                        "id": "remove_extra_spaces",
                        "enabled": True
                    },
                    {
                        "id": "remove_urls_emails",
                        "enabled": True
                    }
                ],
                "segmentation": {
                    "separator": "\n\n",
                    "max_tokens": 1024
                }
            }
        }
        
        # 分别将每个文档上传到知识库
        for i, file_path in enumerate(file_paths):
            filename = filenames[i]
            logger.info(f"正在将文档 {filename} 上传到知识库")
            
            # 上传文档到知识库
            kb_upload_result = dify_service.upload_file_to_knowledge_base(
                file_path, 
                filename,
                indexing_technique="high_quality",
                process_rule=process_rule
            )
            
            # 检查知识库上传结果
            if 'error' in kb_upload_result:
                logger.warning(f"文档 {filename} 上传到知识库失败: {kb_upload_result['error']}")
            else:
                logger.info(f"文档 {filename} 已成功上传到知识库，文档ID: {kb_upload_result.get('document', {}).get('id')}")
        
        # 返回生成的测试用例
        result = {
            "batch_id": batch.id,
            "batch_name": batch.name,
            "test_cases": [tc.to_dict() for tc in saved_test_cases]
        }
        
        return jsonify(result), 201
    except Exception as e:
        logger.error(f"生成测试用例失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        # 清理临时上传的文件
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

@testcase_bp.route('/batch/<int:batch_id>', methods=['GET'])
def get_batch_test_cases(batch_id):
    """获取指定批次的测试用例"""
    batch = TestCaseBatch.query.get_or_404(batch_id)
    test_cases = TestCase.query.filter_by(batch_id=batch_id).all()
    
    result = {
        "batch": {
            "id": batch.id,
            "name": batch.name,
            "description": batch.description,
            "created_at": batch.created_at.strftime('%Y-%m-%d %H:%M:%S')
        },
        "test_cases": [tc.to_dict() for tc in test_cases]
    }
    
    return jsonify(result)

@testcase_bp.route('/batches', methods=['GET'])
def get_all_batches():
    """获取所有批次"""
    batches = TestCaseBatch.query.order_by(TestCaseBatch.created_at.desc()).all()
    
    result = []
    for batch in batches:
        test_case_count = TestCase.query.filter_by(batch_id=batch.id).count()
        result.append({
            "id": batch.id,
            "name": batch.name,
            "description": batch.description,
            "test_case_count": test_case_count,
            "created_at": batch.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    return jsonify(result)

@testcase_bp.route('/batch/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    """删除批次及其测试用例"""
    batch = TestCaseBatch.query.get_or_404(batch_id)
    
    # 删除关联的测试用例
    TestCase.query.filter_by(batch_id=batch_id).delete()
    
    # 删除批次
    db.session.delete(batch)
    db.session.commit()
    
    return jsonify({"message": "批次及其测试用例已删除"})

@testcase_bp.route('/batch/<int:batch_id>/export', methods=['GET'])
def export_batch(batch_id):
    """导出批次测试用例为Excel"""
    batch = TestCaseBatch.query.get_or_404(batch_id)
    test_cases = TestCase.query.filter_by(batch_id=batch_id).all()
    
    if not test_cases:
        return jsonify({"error": "批次中没有测试用例"}), 400
        
    # 创建DataFrame
    data = []
    for tc in test_cases:
        data.append({
            'ID': tc.id,
            '标题': tc.title,
            '描述': tc.description,
            '前置条件': tc.preconditions,
            '测试步骤': tc.steps,
            '预期结果': tc.expected_results,
            '状态': tc.status,
            '源文档': tc.source_document,
            '创建时间': tc.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    export_folder = os.path.join(current_app.root_path, 'exports')
    os.makedirs(export_folder, exist_ok=True)
    
    file_path = os.path.join(export_folder, f'测试用例批次_{batch.id}_{batch.name}.xlsx')
    
    # 写入Excel
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='测试用例')
        
    return send_file(file_path, as_attachment=True)

@testcase_bp.route('/<int:test_case_id>/approve', methods=['PUT'])
def approve_test_case(test_case_id):
    """审核测试用例"""
    test_case = TestCase.query.get_or_404(test_case_id)
    test_case.status = 'approved'
    db.session.commit()
    
    return jsonify({"message": "测试用例已审核通过", "test_case": test_case.to_dict()})

@testcase_bp.route('/<int:test_case_id>/reject', methods=['PUT'])
def reject_test_case(test_case_id):
    """拒绝测试用例"""
    test_case = TestCase.query.get_or_404(test_case_id)
    test_case.status = 'rejected'
    db.session.commit()
    
    return jsonify({"message": "测试用例已拒绝", "test_case": test_case.to_dict()}) 