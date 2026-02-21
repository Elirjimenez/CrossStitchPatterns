import pytest
from abc import ABC

from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.pattern_result_repository import PatternResultRepository


def test_project_repository_is_abstract():
    assert issubclass(ProjectRepository, ABC)
    with pytest.raises(TypeError):
        ProjectRepository()


def test_pattern_result_repository_is_abstract():
    assert issubclass(PatternResultRepository, ABC)
    with pytest.raises(TypeError):
        PatternResultRepository()


def test_project_repository_has_required_methods():
    methods = {"add", "get", "list_all", "update_status", "delete"}
    abstract_methods = ProjectRepository.__abstractmethods__
    assert methods.issubset(abstract_methods)


def test_pattern_result_repository_has_required_methods():
    methods = {"add", "list_by_project", "get_latest_by_project", "delete_by_project"}
    abstract_methods = PatternResultRepository.__abstractmethods__
    assert methods.issubset(abstract_methods)
