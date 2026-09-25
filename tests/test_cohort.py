import unittest

from uscis_cohort.cohort import build_cohort, mask_receipt, normalize_receipt


class CohortTests(unittest.TestCase):
    def test_normalizes_common_formatting(self):
        self.assertEqual(normalize_receipt("ioe-123 456 7890"), "IOE1234567890")

    def test_rejects_invalid_receipt(self):
        with self.assertRaises(ValueError):
            normalize_receipt("IOE123")

    def test_builds_centered_cohort(self):
        self.assertEqual(
            build_cohort("IOE0000000010", 2, 1),
            ["IOE0000000008", "IOE0000000009", "IOE0000000010", "IOE0000000011"],
        )

    def test_masks_receipt(self):
        self.assertEqual(mask_receipt("IOE1234567890"), "IOE******7890")


if __name__ == "__main__":
    unittest.main()

