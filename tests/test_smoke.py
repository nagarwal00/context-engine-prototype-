import os
import tempfile
import unittest
from backend.db import Database
from backend.seed_data import populate_seed_data


class TestSmoke(unittest.TestCase):
    def test_database_init_and_seed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_db_path = os.path.join(tmp_dir, "test_smoke.db")
            db = Database(db_path=temp_db_path)
            populate_seed_data(db)

            with db.get_connection() as conn:
                row = conn.execute("SELECT COUNT(*) AS count FROM decisions").fetchone()
                decision_count = row["count"] if row else 0

            self.assertGreater(decision_count, 0, "Expected decisions to be populated")


if __name__ == "__main__":
    unittest.main()
