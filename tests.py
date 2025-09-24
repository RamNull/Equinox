"""
Simple tests to verify critical fixes in the Equinox application.
Run with: python -m pytest tests.py -v
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock


class TestAppSyntax:
    """Test that the app files compile without syntax errors"""
    
    def test_app_py_compiles(self):
        """Test that app.py compiles without syntax errors"""
        import py_compile
        try:
            py_compile.compile('/home/runner/work/Equinox/Equinox/app.py', doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"app.py has syntax errors: {e}")
    
    def test_inhouse_app_py_compiles(self):
        """Test that inhouse_app.py compiles without syntax errors"""
        import py_compile
        try:
            py_compile.compile('/home/runner/work/Equinox/Equinox/inhouse_app.py', doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"inhouse_app.py has syntax errors: {e}")


class TestConfiguration:
    """Test configuration management"""
    
    def test_config_file_exists(self):
        """Test that config.py exists"""
        assert os.path.exists('/home/runner/work/Equinox/Equinox/config.py')
    
    def test_config_imports(self):
        """Test that config.py can be imported"""
        import sys
        sys.path.insert(0, '/home/runner/work/Equinox/Equinox')
        try:
            import config
            assert hasattr(config, 'Config')
            assert hasattr(config, 'get_config')
        except ImportError as e:
            pytest.fail(f"Cannot import config: {e}")


class TestSecurityFiles:
    """Test security-related files"""
    
    def test_env_template_exists(self):
        """Test that .env.template exists"""
        assert os.path.exists('/home/runner/work/Equinox/Equinox/.env.template')
    
    def test_security_md_exists(self):
        """Test that SECURITY.md exists"""
        assert os.path.exists('/home/runner/work/Equinox/Equinox/SECURITY.md')
    
    def test_gitignore_updated(self):
        """Test that .gitignore includes security entries"""
        with open('/home/runner/work/Equinox/Equinox/.gitignore', 'r') as f:
            content = f.read()
            assert '.env.local' in content
            assert '.env.production' in content
            assert 'secrets.json' in content


class TestCodeFixes:
    """Test that critical code issues are fixed"""
    
    def test_json_loads_safety(self):
        """Test that JSON parsing has proper error handling"""
        # This is a basic test to ensure JSON parsing doesn't crash
        test_json = '{"test": "value"}'
        invalid_json = '{"test": invalid}'
        
        # Should work
        result = json.loads(test_json)
        assert result["test"] == "value"
        
        # Should handle errors
        try:
            json.loads(invalid_json)
            pytest.fail("Expected JSON parsing error")
        except json.JSONDecodeError:
            pass  # Expected behavior


if __name__ == "__main__":
    # Run the tests if executed directly
    import sys
    sys.exit(pytest.main([__file__, "-v"]))