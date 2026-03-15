"""Simple test to verify the testing framework works."""

import json
import tempfile
from pathlib import Path


def test_create_temp_file() -> None:
    """Test creating a temporary file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        assert Path(temp_path).exists()
        content = Path(temp_path).read_text()
        assert content == "test content"
    finally:
        Path(temp_path).unlink()


def test_json_operations() -> None:
    """Test basic JSON operations."""
    data = {"name": "Test", "value": 123}
    json_str = json.dumps(data)
    parsed = json.loads(json_str)
    
    assert parsed["name"] == "Test"
    assert parsed["value"] == 123


def test_path_operations() -> None:
    """Test basic path operations."""
    path = Path("/tmp/test/file.txt")
    
    assert path.name == "file.txt"
    assert path.suffix == ".txt"
    assert path.parent.name == "test"


if __name__ == "__main__":
    test_create_temp_file()
    test_json_operations()
    test_path_operations()
    print("All simple tests passed!")