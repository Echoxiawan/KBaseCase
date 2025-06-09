from datetime import datetime
from . import db

class TestCaseBatch(db.Model):
    """测试用例批次模型"""
    __tablename__ = 'test_case_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联的测试用例
    test_cases = db.relationship('TestCase', backref='batch', lazy=True)
    
    def __repr__(self):
        return f'<TestCaseBatch {self.name}>'

class TestCase(db.Model):
    """测试用例模型"""
    __tablename__ = 'test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    preconditions = db.Column(db.Text, nullable=True)
    steps = db.Column(db.Text, nullable=False)
    expected_results = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    source_document = db.Column(db.String(255), nullable=True)  # 源文档名称
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 外键关联批次
    batch_id = db.Column(db.Integer, db.ForeignKey('test_case_batches.id'), nullable=False)
    
    def __repr__(self):
        return f'<TestCase {self.title}>'
        
    def to_dict(self):
        """转换为字典，用于API返回和Excel导出"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'preconditions': self.preconditions,
            'steps': self.steps,
            'expected_results': self.expected_results,
            'status': self.status,
            'source_document': self.source_document,
            'batch_id': self.batch_id,
            'batch_name': self.batch.name if self.batch else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } 