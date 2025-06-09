from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .testcase import TestCase, TestCaseBatch
from .knowledge_file import KnowledgeFile

__all__ = ['db', 'TestCase', 'TestCaseBatch', 'KnowledgeFile'] 