from datetime import datetime
from . import db

class KnowledgeFile(db.Model):
    """知识库文件模型，用于跟踪上传到Dify知识库的文件"""
    __tablename__ = 'knowledge_files'
    
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, docx, md等
    file_size = db.Column(db.Integer, nullable=False)  # 文件大小（字节）
    dify_file_id = db.Column(db.String(100), nullable=True)  # Dify API返回的文件ID
    status = db.Column(db.String(20), default='pending')  # pending, processed, failed
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<KnowledgeFile {self.file_name}>'
        
    def to_dict(self):
        """转换为字典，用于API返回"""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'dify_file_id': self.dify_file_id,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } 