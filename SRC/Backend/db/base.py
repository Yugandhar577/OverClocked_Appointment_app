"""
Backend documentation for `db/base.py`.

This backend module participates in the appointment platform and is documented to make future changes safer.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from sqlalchemy.orm import DeclarativeBase


# Backend note: Base class shared by related backend objects.
class Base(DeclarativeBase):
    pass


# Explanation:
# `Base` is the declarative base for SQLAlchemy models in this project.
# Centralizing it ensures all models share a common metadata and mapping
# configuration used by Alembic and the ORM.
#
# Alternative (commented): use the older `declarative_base()` factory or
# a registry pattern when needing multiple model registries.
#
# from sqlalchemy.orm import declarative_base
# Base = declarative_base()
