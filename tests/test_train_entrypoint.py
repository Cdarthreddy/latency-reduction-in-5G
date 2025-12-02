from train_rl import ensure_dirs

def test_ensure_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ensure_dirs()
    assert (tmp_path/"data").exists()
