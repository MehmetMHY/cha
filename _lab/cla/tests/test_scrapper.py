import unittest
from cla import colors, config, scrapper
import json


class TestScrapperGetModels(unittest.TestCase):
    try:
        model_list = scrapper.get_models()
    except:
        model_list = None

    def test_loaded_model_list(self):
        self.assertIsNotNone(self.model_list)

    def test_model_list_format(self):
        self.assertIsInstance(self.model_list, list)
        for item in self.model_list:
            self.assertIsInstance(item, dict)
            self.assertIn("name", item)
            self.assertIn("model", item)
            self.assertIsInstance(item["name"], str)
            self.assertIsInstance(item["model"], str)
            self.assertTrue(len(item["name"]) > 0)
            self.assertTrue(len(item["model"]) > 0)


if __name__ == "__main__":
    unittest.main()
