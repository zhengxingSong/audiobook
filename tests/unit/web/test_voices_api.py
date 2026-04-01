"""Tests for voice-management web APIs."""

from fastapi.testclient import TestClient

from audiobook.web import create_app


class TestVoicesApi:
    """HTTP tests for voice CRUD operations."""

    def test_create_list_get_and_delete_voice(self, temp_dir) -> None:
        client = TestClient(
            create_app(
                output_root=temp_dir / "output",
                voice_library_path=temp_dir / "voices",
                run_jobs_inline=True,
            )
        )

        created = client.post(
            "/api/voices",
            files={"audio_file": ("voice.wav", b"RIFF0000", "audio/wav")},
            data={
                "name": "Narrator",
                "gender": "neutral",
                "age_range": "adult",
                "tags": "narrator, calm",
                "description": "Reference narrator",
            },
        )

        assert created.status_code == 201
        voice_id = created.json()["voice_id"]

        listed = client.get("/api/voices")
        fetched = client.get(f"/api/voices/{voice_id}")
        deleted = client.delete(f"/api/voices/{voice_id}")
        listed_after = client.get("/api/voices")

        assert listed.status_code == 200
        assert listed.json()["count"] == 1
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Narrator"
        assert deleted.status_code == 200
        assert listed_after.json()["count"] == 0
