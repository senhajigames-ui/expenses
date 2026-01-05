import unittest
import re

def validate_email(email):
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Validate password strength:
    - Min 8 chars
    - 1 uppercase
    - 1 number
    - 1 special char
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=]", password):
        return False
    return True

class TestAuthValidation(unittest.TestCase):
    
    def test_email_validation(self):
        # Valid
        self.assertTrue(validate_email("test@example.com"))
        self.assertTrue(validate_email("user.name@domain.co.uk"))
        self.assertTrue(validate_email("user+tag@example.com"))
        
        # Invalid
        self.assertFalse(validate_email("invalid"))
        self.assertFalse(validate_email("user@"))
        self.assertFalse(validate_email("user@domain"))
        self.assertFalse(validate_email("@domain.com"))
        
    def test_password_validation(self):
        # Valid
        self.assertTrue(validate_password("StrongPass1!"))
        self.assertTrue(validate_password("Correct-Horse-Battery-Staple-1"))
        
        # Invalid
        self.assertFalse(validate_password("weak")) # Too short
        self.assertFalse(validate_password("alllowercase1!")) # No upper
        self.assertFalse(validate_password("ALLUPPERCASE1!")) # No lower (actually regex allows this, let's check)
        # Wait, my regex doesn't enforce lowercase. Let's fix that in actual implementation or test.
        # My plan said: "At least one uppercase letter", "At least one number", "At least one special character".
        # It didn't explicitly say "At least one lowercase", but that's standard. I'll add it.
        
        self.assertFalse(validate_password("NoNumber!")) # No number
        self.assertFalse(validate_password("NoSpecialChar1")) # No special
        
    def test_password_lowercase_check(self):
        # Let's see if I should enforce lowercase. Yes, standard.
        # I'll update the validate function in the test to match what I WILL implement.
        pass

if __name__ == '__main__':
    unittest.main()
