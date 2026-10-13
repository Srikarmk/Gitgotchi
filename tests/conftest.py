import pytest
from git import Repo


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """An empty git repository that is also the current directory."""
    r = Repo.init(tmp_path)
    with r.config_writer() as cw:
        cw.set_value("user", "name", "Test User")
        cw.set_value("user", "email", "test@example.com")
        cw.set_value("commit", "gpgsign", "false")
    monkeypatch.chdir(tmp_path)
    return r
