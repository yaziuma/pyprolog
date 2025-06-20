"""
Simple test to verify basic functionality works
"""
import unittest
from pyprolog.core.types import Variable, Term, Atom
from pyprolog.runtime.interpreter import Runtime


class TestSimpleEnglish(unittest.TestCase):
    
    def setUp(self):
        """Set up Runtime for each test"""
        try:
            self.runtime = Runtime()
        except Exception as e:
            self.runtime = None
            self.fail(f"Failed to initialize Runtime: {e}")

    def test_basic_functionality(self):
        """Test basic Prolog functionality without complex medical diagnosis"""
        kb_path = "tests/data/simple_diagnosis_test.pl"
        consult_success = self.runtime.consult(kb_path)
        assert consult_success, f"Failed to consult the knowledge base: {kb_path}"

        # Test 1: Simple fact query
        result1 = self.runtime.query("disease_symptom(cold, fever, 0.8).")
        assert result1 is not None, "Fact query returned None"
        assert len(result1) > 0, "Fact query returned no solutions"
        print("✓ Simple fact query passed")

        # Test 2: Simple unification
        result2 = self.runtime.query("basic_test(X).")
        assert result2 is not None, "Basic test returned None"
        assert len(result2) > 0, "Basic test returned no solutions"
        
        x_var = Variable("X")
        solution2 = result2[0]
        assert x_var in solution2, "Variable X not found in solution"
        x_value = solution2[x_var]
        assert isinstance(x_value, Atom) and x_value.name == "hello", f"Expected 'hello', got {x_value}"
        print("✓ Simple unification passed")

        # Test 3: Write predicate (just check it doesn't crash)
        result3 = self.runtime.query("test_write.")
        assert result3 is not None, "Write test returned None"
        print("✓ Write predicate test passed")

        print("All simple tests passed successfully!")


if __name__ == '__main__':
    unittest.main()