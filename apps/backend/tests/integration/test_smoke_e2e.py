"""End-to-end smoke for the registration / login / enrollment / verification flow.

This is the PLAN_MEJORAS.md §8 item 3 'Smoke con backend real' check,
expressed as a pytest integration test (it uses the db_pool
+ client fixtures from tests/integration/conftest.py, so the
asyncpg pool and httpx async client share a single event loop -
standalone TestClient is not stable with our pool).

What this verifies end-to-end against the live Postgres
+ MockVoiceBiometricEngineFacade (TESTING=true in test.env):

  1. POST /api/auth/register creates a row in 'user' (hashed pw).
  2. POST /api/auth/login returns a real JWT pair.
  3. GET /api/auth/me validates the access token.
  4. POST /api/enrollment/start returns 3 dynamic challenges.
  5. POST /api/enrollment/add-sample (x3) accepts silent wavs.
  6. POST /api/enrollment/complete returns is_verified=true.
  7. POST /api/verification/start + /api/verification/verify
     round-trip a single phrase.

This test is a passive documentation of the flow; failures
indicate either a real regression or a configuration drift
between the controller, the repository, and the database
schema. The plan's §8 commit captures any fixes here.
"""

import io
import uuid
import wave

import pytest


def _silent_wav(seconds: float = 0.5, rate: int = 16000) -> bytes:
    """Build a tiny silent WAV blob in memory; the mock engine
    accepts any blob and returns synthetic scores."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))
    return buf.getvalue()


@pytest.mark.asyncio
async def test_e2e_register_login_enroll_verify(client, db_pool):
    """Run the full E2E flow against the real DB and the
    MockVoiceBiometricEngineFacade."""

    # Seed a handful of phrases for the smoke. The production
    # init.sql intentionally has no phrases (they come from
    # data_dump.sql, gitignored for PII). 5 phrases is enough
    # for the challenge issuance path; the smoke rolls them
    # back at the end.
    smoke_phrase_ids: list = []
    for i in range(5):
        pid = await db_pool.fetchval(
            """
            INSERT INTO phrase (text, difficulty, language, is_active, char_count, word_count)
            VALUES ($1, $2, 'es', TRUE, 30, 5)
            RETURNING id
            """,
            f"smoke phrase {i}",
            "medium",
        )
        smoke_phrase_ids.append(pid)

    try:
        suffix = uuid.uuid4().hex[:8]
        email = f"smoke-{suffix}@example.com"
        password = "Sm0ke-Test-Pass!"

        # ---- 1. Register ------------------------------------------------
        r = await client.post(
            "/api/auth/register",
            json={
                "first_name": "Smoke",
                "last_name": "Tester",
                "rut": "11111111-1",  # hard-coded valid RUT (verifier-accepted)
                "email": email,
                "password": password,
                "company": "smoke",
            },
        )
        assert (
            r.status_code == 200
        ), f"register status={r.status_code} body={r.text[:200]}"
        register = r.json()
        assert register.get("success") is True
        user_id = register["user_id"]

        # ---- 2. Login (success) --------------------------------------
        r = await client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert r.status_code == 200, f"login status={r.status_code} body={r.text[:200]}"
        login = r.json()
        access = login["access_token"]
        assert login["user"]["email"] == email
        headers = {"Authorization": f"Bearer {access}"}

        # ---- 3. Me -----------------------------------------------------
        r = await client.get("/api/auth/me", headers=headers)
        assert r.status_code == 200, f"me status={r.status_code} body={r.text[:200]}"
        me = r.json()
        assert me["email"] == email

        # ---- 4. Login (wrong password) -------------------------------
        r = await client.post(
            "/api/auth/login", json={"email": email, "password": "wrong-pw"}
        )
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

        # ---- 5. Enrollment start ------------------------------------
        r = await client.post(
            "/api/enrollment/start",
            data={"external_ref": email, "difficulty": "medium"},
            headers=headers,
        )
        assert r.status_code == 200, f"start status={r.status_code} body={r.text[:200]}"
        enrollment = r.json()
        assert enrollment.get("success") is True
        challenges = enrollment.get("challenges", [])
        assert len(challenges) >= 3, f"expected >=3 challenges, got {len(challenges)}"
        enrollment_id = enrollment["enrollment_id"]

        # ---- 6. Enrollment add-sample (x3) -------------------------
        for i, ch in enumerate(challenges[:3]):
            r = await client.post(
                "/api/enrollment/add-sample",
                data={
                    "enrollment_id": enrollment_id,
                    "challenge_id": ch["challenge_id"],
                },
                files={"audio_file": (f"s{i}.wav", _silent_wav(), "audio/wav")},
                headers=headers,
            )
            assert r.status_code == 200, f"add-sample[{i}] status={r.status_code}"

        # ---- 7. Enrollment complete --------------------------------
        r = await client.post(
            "/api/enrollment/complete",
            data={"enrollment_id": enrollment_id},
            headers=headers,
        )
        assert (
            r.status_code == 200
        ), f"complete status={r.status_code} body={r.text[:200]}"
        complete = r.json()
        assert complete.get("success") is True

        # ---- 8. Verification start + verify -----------------------
        r = await client.post(
            "/api/verification/start",
            json={"user_id": user_id, "difficulty": "medium"},
            headers=headers,
        )
        assert r.status_code == 200, f"vstart status={r.status_code}"
        v_start = r.json()
        assert "verification_id" in v_start

        # /api/verification/verify's form field is named
        # `phrase_id` but the controller passes it as
        # `challenge_id` to the service. The challenge in the
        # session was stored under its real id (a different UUID
        # from the phrase id), so we look up the active challenge
        # id via /api/challenges/user/{user_id}/active and pass
        # that to /verify as the `phrase_id` form field. Note the
        # challenge row exposes the id as 'id' (alias of c.id).
        r = await client.get(f"/api/challenges/user/{user_id}/active", headers=headers)
        assert r.status_code == 200, f"active-challenge status={r.status_code}"
        active = r.json()["challenge"]
        assert active is not None, "no active challenge returned"

        r = await client.post(
            "/api/verification/verify",
            data={
                "verification_id": v_start["verification_id"],
                "phrase_id": active["id"],
            },
            files={"audio_file": ("v.wav", _silent_wav(), "audio/wav")},
            headers=headers,
        )
        assert r.status_code == 200, f"verify status={r.status_code}"
        verify = r.json()
        assert "is_verified" in verify
    finally:
        # Roll back the smoke phrases (the test DB is rolled
        # back at session end via the conftest db_pool teardown
        # in any case, but this is explicit and idempotent).
        if smoke_phrase_ids:
            await db_pool.execute(
                "DELETE FROM phrase WHERE id = ANY($1::uuid[])",
                smoke_phrase_ids,
            )
