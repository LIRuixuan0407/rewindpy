import unittest

from rewindpy.serialize import SafeSerializer, SerializationConfig


class SafeSerializerTests(unittest.TestCase):
    def test_redacts_secret_names(self):
        serializer = SafeSerializer()
        result = serializer.serialize_locals({"api_key": "abc", "username": "ada"})
        self.assertEqual(result["api_key"], "<redacted>")
        self.assertEqual(result["username"], "ada")

    def test_truncates_strings(self):
        serializer = SafeSerializer(SerializationConfig(max_string_length=5))
        result = serializer.serialize("abcdefgh")
        self.assertTrue(result.startswith("abcde"))
        self.assertIn("truncated", result)

    def test_redacts_nested_dict_values(self):
        serializer = SafeSerializer()
        result = serializer.serialize({"token": "secret", "ok": 1})
        self.assertEqual(result["token"], "<redacted>")
        self.assertEqual(result["ok"], 1)


if __name__ == "__main__":
    unittest.main()
