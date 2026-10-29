import pytest
@pytest.fixture
def app(tmp_path,monkeypatch):
    import config
    monkeypatch.setattr(config.Config,'DATABASE',str(tmp_path/'test.db'))
    monkeypatch.setattr(config.Config,'INSTANCE_DIR',str(tmp_path))
    monkeypatch.setattr(config.Config,'EXPORT_DIR',str(tmp_path/'exports'))
    monkeypatch.setattr(config.Config,'MODEL_DIR',str(tmp_path/'models'))
    from database.db import init_db
    init_db()
    import app as module
    module.app.config.update(TESTING=True,SECRET_KEY='test')
    return module.app
@pytest.fixture
def client(app): return app.test_client()
