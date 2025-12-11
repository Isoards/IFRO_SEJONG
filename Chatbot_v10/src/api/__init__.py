"""API routers module"""
from .documents import router as documents_router
from .ontology import router as ontology_router
from .query import router as query_router
from .actions import router as actions_router

__all__ = [
    "documents_router",
    "ontology_router",
    "query_router",
    "actions_router",
]
