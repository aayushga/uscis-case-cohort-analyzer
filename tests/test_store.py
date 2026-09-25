import tempfile
import unittest

from uscis_cohort.store import CaseStore


class StoreTests(unittest.TestCase):
    def test_summarizes_latest_status_by_form(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CaseStore(f"{directory}/cases.sqlite3")
            store.save({"case_status": {
                "receiptNumber": "IOE0000000001", "formType": "I-765",
                "current_case_status_text_en": "Case Was Received"
            }})
            self.assertEqual(list(store.summary("I-765")), [("Case Was Received", 1)])
            store.close()


if __name__ == "__main__":
    unittest.main()

