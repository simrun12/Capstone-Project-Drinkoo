"""
Test authentication utilities.
Tests login verification and token generation.
"""

import pytest
from backend.utils.auth import verify_development_login, is_default_admin_user


class TestAuthenticationUtilities:
    """Test authentication helper functions."""
    
    @pytest.mark.auth
    def test_correct_admin_credentials(self):
        """Test that correct admin credentials are accepted."""
        result = verify_development_login('admin', 'password')
        assert result is not None
        assert isinstance(result, dict)
        assert 'username' in result
        assert result['username'] == 'admin'
    
    @pytest.mark.auth
    def test_incorrect_username(self):
        """Test that incorrect username is rejected."""
        result = verify_development_login('wronguser', 'password')
        assert result is None
    
    @pytest.mark.auth
    def test_incorrect_password(self):
        """Test that incorrect password is rejected."""
        result = verify_development_login('admin', 'wrongpassword')
        assert result is None
    
    @pytest.mark.auth
    def test_empty_credentials(self):
        """Test that empty credentials are rejected."""
        assert verify_development_login('', '') is None
        assert verify_development_login('admin', '') is None
        assert verify_development_login('', 'password') is None
    
    @pytest.mark.auth
    def test_none_credentials(self):
        """Test that None credentials are rejected."""
        assert verify_development_login(None, None) is None
        assert verify_development_login('admin', None) is None
        assert verify_development_login(None, 'password') is None
    
    @pytest.mark.auth
    def test_token_payload_structure(self):
        """Test that token payload has expected structure."""
        result = verify_development_login('admin', 'password')
        assert result is not None
        # Should have user identification
        assert 'username' in result or 'sub' in result
    
    @pytest.mark.auth
    def test_case_sensitivity(self):
        """Test that login is case-sensitive."""
        # Username should be case-sensitive
        assert verify_development_login('Admin', 'password') is None
        assert verify_development_login('ADMIN', 'password') is None
    
    @pytest.mark.auth
    def test_is_default_admin_user(self):
        """Test admin user check function."""
        assert is_default_admin_user('admin') is True
        assert is_default_admin_user('other_user') is False


class TestAuthenticationEdgeCases:
    """Test edge cases and security concerns for authentication."""
    
    @pytest.mark.auth
    def test_sql_injection_attempt(self):
        """Test that SQL injection is not possible."""
        # Should safely reject SQL injection attempts
        result = verify_development_login("admin' OR '1'='1", 'password')
        assert result is None
    
    @pytest.mark.auth
    def test_whitespace_padding(self):
        """Test that whitespace doesn't bypass authentication."""
        assert verify_development_login('admin ', 'password') is None
        assert verify_development_login(' admin', 'password') is None
    
    @pytest.mark.auth
    def test_very_long_credentials(self):
        """Test that very long strings are handled safely."""
        long_string = 'x' * 10000
        result = verify_development_login(long_string, 'password')
        assert result is None
        
        result = verify_development_login('admin', long_string)
        assert result is None
