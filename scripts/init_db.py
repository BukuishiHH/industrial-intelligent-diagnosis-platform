# -*- coding: utf-8 -*-
"""建表：按 packages/db 下的模型在 MySQL 中创建诊断相关表。用法：python scripts/init_db.py"""
import sys

from packages.core.database import Base, engine
import packages.db  # noqa: F401  导入即注册全部模型
from packages.service.persistence import db_health

print("数据库:", engine.url.render_as_string(hide_password=True))
Base.metadata.create_all(bind=engine)
print("建表完成，现有表：")
from sqlalchemy import inspect
for name in sorted(inspect(engine).get_table_names()):
    print("  -", name)
ok, msg = db_health()
print("连通性自检:", "OK" if ok else "FAILED", msg)
sys.exit(0 if ok else 1)
