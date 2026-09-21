"""数据库模型包：在此导入所有模型，确保 Base.metadata.create_all 能建出全部表。"""
from packages.db.diagnosis import (  # noqa: F401
    DiagnosisEvidence,
    DiagnosisRecord,
    DiagnosisReport,
    HitlReview,
)
from packages.db.user import User  # noqa: F401
