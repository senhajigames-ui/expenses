
import unittest
import re

class TestAuthValidation(unittest.TestCase):
    
    def test_email_validation(self):
        """Test explicit email regex pattern used in auth_handler.py"""
        # Using the exact same regex from the implementation
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        
        valid_emails = [
            "test@example.com",
            "first.last@domain.co.uk",
            "user123@sub.domain.org",
            "a@b.ca"
        ]
        
        invalid_emails = [
            "plainaddress",
            "#@%^%#$@#$@#.com",
            "@example.com",
            "Joe Smith <email@example.com>",
            "email.example.com",
            "email@example@example.com",
            "email@example", # Missing TLD
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertIsNotNone(re.match(email_regex, email))
                
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertIsNone(re.match(email_regex, email))

    def test_password_strength(self):
        """Test password complexity regex."""
        # Using exact regex from implementation
        pw_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>\-_+=]).{8,}$"
        
        strong_passwords = [
            "Password123!",
            "Complex-Pass-99",
            "A1@bcdef",
            "My#1Password"
        ]
        
        weak_passwords = [
            "password123", # No upper, no special
            "PASSWORD123", # No lower, no special
            "Pass123", # Too short
            "Password!", # No number
            "Password123", # No special
            "short1!", # Too short
        ]
        
        for pw in strong_passwords:
            with self.subTest(pw=pw):
                self.assertIsNotNone(re.match(pw_regex, pw))
                
        for pw in weak_passwords:
            with self.subTest(pw=pw):
                self.assertIsNone(re.match(pw_regex, pw))

if __name__ == '__main__':
    unittest.main()
