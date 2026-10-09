import os
import sys
import pytest
from pathlib import Path

# Add the project root to python path to import modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import BASE_DIR
from launcher.main import get_free_port, check_ollama, check_vision_model, setup_logging

def test_base_dir_resolution():
    """Test that BASE_DIR resolves to a Path and exists."""
    assert isinstance(BASE_DIR, Path)
    assert BASE_DIR.exists()

def test_frontend_assets_exist():
    """Verify frontend assets are present in BASE_DIR."""
    frontend_dir = BASE_DIR / "frontend"
    assert frontend_dir.exists()
    assert (frontend_dir / "index.html").exists()

def test_avatar_dictionary_exists():
    """Verify avatar dictionary assets are present in BASE_DIR."""
    avatar_dir = BASE_DIR / "avatar" / "dictionary"
    assert avatar_dir.exists()
    assert (avatar_dir / "asl_signs.json").exists()

def test_get_free_port():
    """Test that the port conflict resolver returns an available port."""
    port = get_free_port(start_port=18000, max_port=18100)
    assert 18000 <= port <= 18100

def test_check_ollama():
    """Test that the Ollama check returns a boolean and string status."""
    ok, status = check_ollama(timeout=0.1)
    assert isinstance(ok, bool)
    assert isinstance(status, str)

def test_check_vision_model():
    """Test that the vision model check returns a boolean and string status."""
    ok, status = check_vision_model(timeout=0.1)
    assert isinstance(ok, bool)
    assert isinstance(status, str)

def test_setup_logging(tmp_path):
    """Test that the launcher logging mechanism creates the correct files."""
    os.environ["APPDATA"] = str(tmp_path)
    log_file = setup_logging()
    assert log_file.parent.exists()
    assert log_file.name == "startup.log"
    
def test_models_exist():
    """Verify models directory exists."""
    models_dir = BASE_DIR / "models"
    assert models_dir.exists()
