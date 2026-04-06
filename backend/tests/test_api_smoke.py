"""Smoke tests for the unified IPL prediction API."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.web.app import app


class UnifiedApiSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.predict_payload = {
            "team1": "Chennai Super Kings",
            "team2": "Mumbai Indians",
            "toss_winner": "Mumbai Indians",
            "user_predicted_score_team1": 180,
            "user_predicted_score_team2": 170,
            "key_player_team1": "MS Dhoni",
            "key_player_team2": "Jasprit Bumrah",
        }

    def test_health(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_legacy_alias(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_metadata(self) -> None:
        response = self.client.get("/api/metadata")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("teams", payload)
        self.assertIn("key_players_by_team", payload)
        self.assertTrue(payload["teams"])

    def test_metadata_legacy_alias(self) -> None:
        response = self.client.get("/metadata")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("teams", payload)
        self.assertIn("key_players_by_team", payload)
        self.assertTrue(payload["teams"])

    def test_prediction(self) -> None:
        response = self.client.post("/api/predict", json=self.predict_payload)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("winner_name", payload)
        self.assertIn("ai_predicted_scorecard_team1", payload)
        self.assertIn("ai_predicted_scorecard_team2", payload)

    def test_prediction_legacy_alias(self) -> None:
        response = self.client.post("/predict", json=self.predict_payload)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("winner_name", payload)
        self.assertIn("ai_predicted_scorecard_team1", payload)
        self.assertIn("ai_predicted_scorecard_team2", payload)


if __name__ == "__main__":
    unittest.main()
