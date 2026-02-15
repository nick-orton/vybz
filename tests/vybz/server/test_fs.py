import pytest
from pathlib import Path
from vybz.server.tools.fs import FileSystemTools

class TestFileSystemTools:
    """
    Unit tests for the FileSystemTools Agentic RAG component.
    Ensures secure and gitignore-aware filesystem access for agents.
    """

    @pytest.fixture
    def workspace(self, tmp_path: Path):
        """
        Creates a dummy project structure:
        /root
          .gitignore (ignores *.log)
          src/
            main.py
          docs/
            readme.md
          app.log (ignored)
          data.bin (binary)
        """
        root = tmp_path / "project"
        root.mkdir()
        
        # 1. Setup gitignore
        (root / ".gitignore").write_text("*.log", encoding="utf-8")
        
        # 2. Setup directories
        src = root / "src"
        src.mkdir()
        docs = root / "docs"
        docs.mkdir()
        
        # 3. Setup files
        (src / "main.py").write_text("print('hello')", encoding="utf-8")
        (docs / "readme.md").write_text("# Readme", encoding="utf-8")
        (root / "app.log").write_text("secret logs", encoding="utf-8")
        
        # 4. Setup binary file (contains null byte)
        (root / "data.bin").write_bytes(b"\x00\x01\x02\x03")
        
        return root

    @pytest.fixture
    def tools(self, workspace):
        """Returns an initialized FileSystemTools instance."""
        return FileSystemTools(workspace)

    # -------------------------------------------------------------------------
    # list_files Tests
    # -------------------------------------------------------------------------

    def test_list_files_root(self, tools):
        """Happy Path: List the root directory."""
        output = tools.list_files(".")
        
        assert "src" in output
        assert "main.py" in output
        assert "docs" in output
        # Verify gitignore compliance: .log should NOT be in the listing
        assert "app.log" not in output

    def test_list_files_subdir(self, tools):
        """Happy Path: List a specific subdirectory."""
        output = tools.list_files("src")
        
        assert "main.py" in output
        assert "docs" not in output

    def test_list_files_traversal_denied(self, tools, tmp_path):
        """Security Path: Ensure traversal outside root is blocked."""
        # Create a file outside the workspace
        outside_file = tmp_path / "outside.txt"
        outside_file.touch()
        
        # Attempt to list using relative parents
        output = tools.list_files("../")
        
        assert "Error: Access denied" in output
        assert "outside.txt" not in output

    def test_list_files_non_existent(self, tools):
        """Sad Path: Handle non-existent directories gracefully."""
        output = tools.list_files("ghost_folder")
        assert "Error: Path ghost_folder does not exist" in output

    # -------------------------------------------------------------------------
    # read_file Tests
    # -------------------------------------------------------------------------

    def test_read_file_success(self, tools):
        """Happy Path: Read a valid text file."""
        output = tools.read_file("src/main.py")
        
        assert "### src/main.py" in output
        assert "```py" in output
        assert "print('hello')" in output

    def test_read_file_binary_denied(self, tools):
        """Sad Path: Verify binary files are detected and rejected."""
        output = tools.read_file("data.bin")
        
        assert "Error" in output
        assert "binary file" in output
        assert "cannot be read" in output

    def test_read_file_traversal_denied(self, tools):
        """Security Path: Ensure traversal in read_file is blocked."""
        # Note: Even if the file exists, the startswith check should catch it
        output = tools.read_file("../../../etc/passwd")
        assert "Error: Access denied" in output

    def test_read_file_not_found(self, tools):
        """Sad Path: Handle missing files."""
        output = tools.read_file("missing.txt")
        assert "Error: missing.txt is not a file or does not exist" in output

    @pytest.mark.parametrize("rel_path", [
        "src/main.py",
        "docs/readme.md",
        ".gitignore"
    ])
    def test_read_file_formatting(self, tools, rel_path):
        """Verify markdown structure for different extensions."""
        output = tools.read_file(rel_path)
        assert output.startswith(f"### {rel_path}")
        assert "```" in output
        assert output.endswith("```")

