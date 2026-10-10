"""
PathWise — Backend API Test Suite (pytest + httpx)

Tests every API endpoint: status codes, response schemas, parameter forwarding,
error handling, data consistency, and directional ML correctness.

Run (backend must be reachable):
    pytest backend/tests/test_api.py -v

Override the base URL:
    BASE_URL=http://127.0.0.1:8000 pytest backend/tests/test_api.py -v

Run inside Docker:
    docker exec pathwise_backend pytest /app/tests/test_api.py -v
"""

import os
import pytest
import httpx

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "pathwise123")

ROLES = ["admin", "student", "moe", "mol", "university"]


# ── Shared fixtures ────────────────────────────────────────────────────────────

def _login(username: str) -> str:
    """Return a bearer token for one of the seeded demo accounts."""
    r = httpx.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": username, "password": DEMO_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"login failed for {username}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def tokens():
    """One token per role, fetched once for the whole session."""
    return {u: _login(u) for u in ROLES}


@pytest.fixture(scope="session")
def client(tokens):
    """Admin-authenticated client.

    Every /api/* route now requires a role. ADMIN satisfies all of them, so the
    existing endpoint tests below use this and keep asserting behaviour rather
    than authorisation. Authorisation itself is covered by TestRoleMatrix.
    """
    with httpx.Client(
        base_url=BASE_URL,
        timeout=30,
        headers={"Authorization": f"Bearer {tokens['admin']}"},
    ) as c:
        yield c


@pytest.fixture(scope="session")
def anon():
    """Unauthenticated client, for asserting endpoints are actually closed."""
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope="session")
def role_clients(tokens):
    """A client per role, keyed by username."""
    clients = {}
    for user, token in tokens.items():
        clients[user] = httpx.Client(
            base_url=BASE_URL, timeout=30,
            headers={"Authorization": f"Bearer {token}"},
        )
    yield clients
    for c in clients.values():
        c.close()


STRONG_STUDENT = {
    "gpa": 3.9,
    "internships": 4,
    "projects": 5,
    "communication_score": 9,
    "program": "MS Data Science",
}

WEAK_STUDENT = {
    "gpa": 2.3,
    "internships": 0,
    "projects": 1,
    "communication_score": 3,
    "program": "Certificate Data Analytics",
}

KNOWN_PROGRAMS = {
    "BS Computer Science", "BS Data Science", "Certificate Data Analytics",
    "MBA Product Management", "MS Artificial Intelligence", "MS Business Analytics",
    "MS Cloud Computing", "MS Computer Science", "MS Cybersecurity",
    "MS Data Science", "MS Human-Computer Interaction", "MS Information Technology",
}


# =============================================================================
# Health
# =============================================================================

class TestHealth:

    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_models_loaded(self, client):
        body = client.get("/health").json()
        assert body.get("models_loaded") is True or all(body.get("models", {}).values()), \
            f"Not all models loaded: {body}"

    def test_health_status_ok(self, client):
        body = client.get("/health").json()
        assert body.get("status") == "ok", f"Got status={body.get('status')}"

    def test_root_liveness(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "PathWise" in r.json().get("message", "")

    def test_health_is_public(self, anon):
        """/health must stay unauthenticated — docker-compose probes it."""
        assert anon.get("/health").status_code == 200
        assert anon.get("/").status_code == 200

    def test_health_reload_is_idempotent(self, client):
        """Reloading a fully-warm API must be a no-op, not a regression."""
        r = client.post("/health/reload")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert all(body["models"].values())
        assert body["recovered"] == []   # nothing was broken, so nothing recovered


# =============================================================================
# Authentication
# =============================================================================

class TestAuth:

    @pytest.mark.parametrize("username", ROLES)
    def test_login_succeeds_for_every_demo_account(self, username):
        r = httpx.post(f"{BASE_URL}/api/auth/login",
                       data={"username": username, "password": DEMO_PASSWORD}, timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["user"]["username"] == username
        assert body["user"]["home"].startswith("/")

    def test_login_wrong_password_401(self, anon):
        r = anon.post("/api/auth/login",
                      data={"username": "student", "password": "definitely-wrong"})
        assert r.status_code == 401

    def test_login_unknown_user_401(self, anon):
        r = anon.post("/api/auth/login",
                      data={"username": "no-such-user", "password": DEMO_PASSWORD})
        assert r.status_code == 401

    def test_login_does_not_leak_which_accounts_exist(self, anon):
        """Unknown user and wrong password must be indistinguishable, or the
        endpoint becomes a username oracle."""
        unknown = anon.post("/api/auth/login",
                            data={"username": "no-such-user", "password": "x"})
        wrong = anon.post("/api/auth/login",
                          data={"username": "student", "password": "x"})
        assert unknown.status_code == wrong.status_code == 401
        assert unknown.json()["detail"] == wrong.json()["detail"]

    def test_me_requires_token(self, anon):
        assert anon.get("/api/auth/me").status_code == 401

    def test_me_rejects_garbage_token(self, anon):
        r = anon.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code == 401

    def test_me_rejects_tampered_token(self, tokens, anon):
        """Flipping a character in the signature must invalidate the token."""
        good = tokens["student"]
        tampered = good[:-4] + ("aaaa" if not good.endswith("aaaa") else "bbbb")
        r = anon.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered}"})
        assert r.status_code == 401

    def test_me_returns_role_and_home(self, role_clients):
        body = role_clients["mol"].get("/api/auth/me").json()
        assert body["role"] == "MOL"
        assert body["role_label"] == "Ministry of Labour"
        assert body["home"] == "/mol/overview"

    def test_university_token_carries_institution(self, role_clients):
        body = role_clients["university"].get("/api/auth/me").json()
        assert body["role"] == "UNIVERSITY"
        assert body["institution"] == "Addis Ababa University"

    def test_non_university_roles_have_no_institution(self, role_clients):
        for user in ("admin", "student", "moe", "mol"):
            assert role_clients[user].get("/api/auth/me").json()["institution"] is None

    def test_signup_creates_student_account(self, anon):
        """Self-registration creates a STUDENT account and signs them in."""
        r = anon.post("/api/auth/signup", json={
            "username": "newsignup1",
            "password": "password123",
            "display_name": "New User",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["user"]["username"] == "newsignup1"
        assert body["user"]["role"] == "STUDENT"
        assert body["user"]["display_name"] == "New User"
        assert body["user"]["home"] == "/student/profile"

        # Cleanup
        admin_token = _login("admin")
        httpx.delete(f"{BASE_URL}/api/users/newsignup1/permanent",
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)

    def test_signup_rejects_duplicate_username(self, anon):
        anon.post("/api/auth/signup", json={
            "username": "newsignup2", "password": "password123", "display_name": "First"
        })
        r = anon.post("/api/auth/signup", json={
            "username": "newsignup2", "password": "different", "display_name": "Second"
        })
        assert r.status_code == 409
        assert "already taken" in r.json()["detail"].lower()

        # Cleanup
        admin_token = _login("admin")
        httpx.delete(f"{BASE_URL}/api/users/newsignup2/permanent",
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)

    def test_signup_rejects_short_password(self, anon):
        r = anon.post("/api/auth/signup", json={
            "username": "newsignup3", "password": "short", "display_name": "Test"
        })
        assert r.status_code == 422

    def test_signup_rejects_invalid_username(self, anon):
        r = anon.post("/api/auth/signup", json={
            "username": "Invalid Username!", "password": "password123", "display_name": "Test"
        })
        assert r.status_code == 422

    def test_signup_token_is_valid(self, anon):
        """The token returned by sign-up must authenticate API calls."""
        signup = anon.post("/api/auth/signup", json={
            "username": "newsignup4", "password": "password123", "display_name": "Test User"
        })
        token = signup.json()["access_token"]

        # Use the token to call /api/auth/me
        r = anon.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["username"] == "newsignup4"

        # Cleanup
        admin_token = _login("admin")
        httpx.delete(f"{BASE_URL}/api/users/newsignup4/permanent",
                     headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)


# =============================================================================
# Role-based access control
# =============================================================================

# endpoint -> the roles that must be allowed. Every other role must get 403,
# and an unauthenticated caller must get 401.
_MATRIX = {
    "/api/careers/jobs":            {"admin", "student"},
    "/api/labour/overview":         {"admin", "moe", "mol"},
    "/api/labour/supply-demand":    {"admin", "moe", "mol"},
    "/api/labour/mismatch":         {"admin", "moe", "mol"},
    "/api/education/overview":      {"admin", "moe"},
    "/api/education/investment-quadrant": {"admin", "moe"},
    "/api/institution/me":          {"admin", "university"},
    "/api/institution/expansion":   {"admin", "university"},
    "/api/monitoring/drift":        {"admin"},
    "/api/market/overview":         {"admin", "student", "moe", "mol", "university"},
    "/api/enrollment/summary":      {"admin", "student", "moe", "university"},
}


class TestRoleMatrix:

    @pytest.mark.parametrize("endpoint,allowed", sorted((k, tuple(sorted(v))) for k, v in _MATRIX.items()))
    def test_allowed_roles_get_200(self, role_clients, endpoint, allowed):
        for user in allowed:
            r = role_clients[user].get(endpoint)
            assert r.status_code == 200, f"{user} should reach {endpoint}, got {r.status_code}"

    @pytest.mark.parametrize("endpoint,allowed", sorted((k, tuple(sorted(v))) for k, v in _MATRIX.items()))
    def test_disallowed_roles_get_403(self, role_clients, endpoint, allowed):
        for user in set(ROLES) - set(allowed):
            r = role_clients[user].get(endpoint)
            assert r.status_code == 403, f"{user} must NOT reach {endpoint}, got {r.status_code}"

    @pytest.mark.parametrize("endpoint", sorted(_MATRIX))
    def test_unauthenticated_gets_401(self, anon, endpoint):
        assert anon.get(endpoint).status_code == 401

    def test_admin_reaches_every_protected_endpoint(self, role_clients):
        for endpoint in _MATRIX:
            assert role_clients["admin"].get(endpoint).status_code == 200, endpoint


# =============================================================================
# User management (ADMIN)
# =============================================================================

# Accounts these tests create. Torn down after the module so the suite can be
# re-run against the same live database without colliding with itself.
_SCRATCH = ["t_create", "t_edit", "t_deact", "t_pw", "t_self", "t_uni", "t_admin2"]


def _purge(admin_client):
    """Remove scratch accounts so the suite can run repeatedly.

    Uses the permanent-delete route rather than deactivation: a deactivated
    leftover would still occupy its username and fail the next run's create.
    404s are expected and ignored — the account may not exist yet.
    """
    for name in _SCRATCH:
        admin_client.delete(f"/api/users/{name}/permanent")


@pytest.fixture(scope="class")
def scratch(role_clients):
    """Clean before and after, so a previous failed run cannot poison this one."""
    admin = role_clients["admin"]
    _purge(admin)
    yield admin
    _purge(admin)


def _new_user(client, username, **over):
    body = {
        "username":     username,
        "password":     "scratchpass123",
        "role":         "STUDENT",
        "display_name": f"Scratch {username}",
        **over,
    }
    return client.post("/api/users", json=body)


def _user_rows(body):
    if isinstance(body, dict):
        return body.get("rows") or []
    return body


class TestUserManagement:

    # ── Access ────────────────────────────────────────────────────────────

    def test_only_admin_can_list(self, role_clients, anon):
        assert role_clients["admin"].get("/api/users").status_code == 200
        for user in ("student", "moe", "mol", "university"):
            assert role_clients[user].get("/api/users").status_code == 403, user
        assert anon.get("/api/users").status_code == 401

    @pytest.mark.parametrize("method,path", [
        ("post",   "/api/users"),
        ("patch",  "/api/users/student"),
        ("delete", "/api/users/student"),
        ("post",   "/api/users/student/password"),
        ("delete", "/api/users/student/permanent"),
        ("get",    "/api/users/meta/institutions"),
    ])
    def test_every_route_is_admin_only(self, role_clients, method, path):
        for user in ("student", "moe", "mol", "university"):
            client = role_clients[user]
            # httpx's get/delete take no json= kwarg, so only send a body where
            # the verb accepts one.
            if method in ("post", "patch"):
                r = getattr(client, method)(path, json={})
            else:
                r = getattr(client, method)(path)
            assert r.status_code == 403, f"{user} reached {method.upper()} {path}"

    def test_list_never_returns_password_hashes(self, role_clients):
        body = role_clients["admin"].get("/api/users").json()
        assert body
        for u in _user_rows(body):
            assert "password_hash" not in u
        # And not under any other spelling either.
        assert "$2b$" not in str(body), "a bcrypt hash leaked into the response"

    def test_list_includes_the_seeded_accounts(self, role_clients):
        names = {u["username"] for u in _user_rows(role_clients["admin"].get("/api/users").json())}
        assert {"admin", "student", "moe", "mol", "university"} <= names

    # ── Create ────────────────────────────────────────────────────────────

    def test_create_then_login(self, scratch):
        r = _new_user(scratch, "t_create")
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["username"] == "t_create"
        assert body["is_active"] is True

        # The account must actually work, not merely have been written.
        login = httpx.post(f"{BASE_URL}/api/auth/login",
                           data={"username": "t_create", "password": "scratchpass123"},
                           timeout=30)
        assert login.status_code == 200

    def test_create_duplicate_username_409(self, scratch):
        _new_user(scratch, "t_create")
        assert _new_user(scratch, "t_create").status_code == 409

    @pytest.mark.parametrize("field,value", [
        ("password", "short"),          # under the 8-char minimum
        ("username", "AB"),             # too short, and uppercase
        ("username", "has spaces"),
        ("username", "Uppercase"),
        ("role",     "WIZARD"),
        ("display_name", ""),
    ])
    def test_create_rejects_invalid_input(self, scratch, field, value):
        body = {
            "username":     "t_bad",
            "password":     "scratchpass123",
            "role":         "STUDENT",
            "display_name": "Bad Input",
            field:          value,      # overrides the key under test
        }
        assert scratch.post("/api/users", json=body).status_code == 422

    def test_university_account_requires_a_valid_institution(self, scratch):
        # No institution at all.
        assert _new_user(scratch, "t_uni", role="UNIVERSITY").status_code == 422
        # An institution that is not in the dataset — it would authenticate and
        # then show empty dashboards, which reads as a bug.
        assert _new_user(scratch, "t_uni", role="UNIVERSITY",
                         institution_name="Hogwarts").status_code == 422
        # A real one succeeds.
        r = _new_user(scratch, "t_uni", role="UNIVERSITY",
                      institution_name="Addis Ababa University")
        assert r.status_code == 201
        assert r.json()["institution_name"] == "Addis Ababa University"

    def test_institution_options_are_available(self, scratch):
        body = scratch.get("/api/users/meta/institutions").json()
        assert len(body) == 8
        assert {"name", "type", "state"} <= set(body[0])

    # ── Update ────────────────────────────────────────────────────────────

    def test_update_fields(self, scratch):
        _new_user(scratch, "t_edit")
        r = scratch.patch("/api/users/t_edit",
                          json={"display_name": "Renamed", "role": "MOL"})
        assert r.status_code == 200
        assert r.json()["display_name"] == "Renamed"
        assert r.json()["role"] == "MOL"

    def test_username_cannot_be_changed(self, scratch):
        _new_user(scratch, "t_edit")
        # Extra keys are ignored by the schema rather than renaming the account,
        # because the username is the JWT subject.
        scratch.patch("/api/users/t_edit", json={"username": "t_renamed"})
        assert scratch.get("/api/users").json()
        names = {u["username"] for u in _user_rows(scratch.get("/api/users").json())}
        assert "t_edit" in names
        assert "t_renamed" not in names

    def test_update_unknown_user_404(self, scratch):
        assert scratch.patch("/api/users/nobody_here",
                             json={"display_name": "X"}).status_code == 404

    def test_promoting_to_university_requires_institution(self, scratch):
        _new_user(scratch, "t_edit")
        # Changing role alone must not leave a UNIVERSITY account unscoped.
        r = scratch.patch("/api/users/t_edit", json={"role": "UNIVERSITY"})
        assert r.status_code == 422

    # ── Guard rails ───────────────────────────────────────────────────────

    def test_admin_cannot_deactivate_self(self, scratch):
        r = scratch.delete("/api/users/admin")
        assert r.status_code == 400
        assert "your own" in r.json()["detail"].lower()
        # And is still able to work.
        assert scratch.get("/api/users").status_code == 200

    def test_admin_cannot_demote_self(self, scratch):
        r = scratch.patch("/api/users/admin", json={"role": "STUDENT"})
        assert r.status_code == 400
        assert scratch.get("/api/users").json()  # still an admin

    def test_cannot_remove_the_last_active_admin(self, scratch):
        """With a second admin present the guard must allow it; with none, refuse."""
        _new_user(scratch, "t_admin2", role="ADMIN")

        # Two admins exist, so deactivating the spare is allowed.
        assert scratch.delete("/api/users/t_admin2").status_code == 200

        # admin is now the only active one, and cannot be removed even by
        # another route (it is also self, so both guards apply).
        assert scratch.delete("/api/users/admin").status_code == 400

    # ── Deactivate / reactivate ───────────────────────────────────────────

    def test_deactivate_blocks_login_and_revokes_token(self, scratch):
        _new_user(scratch, "t_deact")

        token = httpx.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "t_deact", "password": "scratchpass123"},
            timeout=30,
        ).json()["access_token"]

        live = httpx.Client(base_url=BASE_URL, timeout=30,
                            headers={"Authorization": f"Bearer {token}"})
        assert live.get("/api/careers/jobs").status_code == 200

        r = scratch.delete("/api/users/t_deact")
        assert r.status_code == 200
        assert r.json()["is_active"] is False

        # Cannot get a new token ...
        assert httpx.post(f"{BASE_URL}/api/auth/login",
                          data={"username": "t_deact", "password": "scratchpass123"},
                          timeout=30).status_code == 401

        # ... and the one they already hold stops working. This is the whole
        # point of the feature: without the status check a deactivated user
        # would keep full access until their token expired.
        assert live.get("/api/careers/jobs").status_code == 401
        live.close()

    def test_reactivate_restores_access(self, scratch):
        _new_user(scratch, "t_deact")
        scratch.delete("/api/users/t_deact")

        r = scratch.patch("/api/users/t_deact", json={"is_active": True})
        assert r.status_code == 200
        assert r.json()["is_active"] is True

        assert httpx.post(f"{BASE_URL}/api/auth/login",
                          data={"username": "t_deact", "password": "scratchpass123"},
                          timeout=30).status_code == 200

    def test_deactivated_account_is_not_disclosed_at_login(self, scratch):
        """A disabled account and a wrong password must be indistinguishable,
        or login becomes an oracle for which accounts exist and are disabled."""
        _new_user(scratch, "t_deact")
        scratch.delete("/api/users/t_deact")

        disabled = httpx.post(f"{BASE_URL}/api/auth/login",
                              data={"username": "t_deact", "password": "scratchpass123"},
                              timeout=30)
        wrong = httpx.post(f"{BASE_URL}/api/auth/login",
                           data={"username": "t_deact", "password": "wrong-entirely"},
                           timeout=30)
        assert disabled.status_code == wrong.status_code == 401
        assert disabled.json()["detail"] == wrong.json()["detail"]

    # ── Passwords ─────────────────────────────────────────────────────────

    def test_admin_reset_replaces_the_password(self, scratch):
        _new_user(scratch, "t_pw")

        assert scratch.post("/api/users/t_pw/password",
                            json={"new_password": "brandnew456"}).status_code == 200

        # The old one must stop working and the new one must start —
        # asserting only 200 would pass even if nothing had been written.
        assert httpx.post(f"{BASE_URL}/api/auth/login",
                          data={"username": "t_pw", "password": "scratchpass123"},
                          timeout=30).status_code == 401
        assert httpx.post(f"{BASE_URL}/api/auth/login",
                          data={"username": "t_pw", "password": "brandnew456"},
                          timeout=30).status_code == 200

    def test_admin_reset_rejects_short_password(self, scratch):
        _new_user(scratch, "t_pw")
        assert scratch.post("/api/users/t_pw/password",
                            json={"new_password": "abc"}).status_code == 422


class TestChangeOwnPassword:
    """Self-service — every role, including those that never see the console."""

    def test_requires_authentication(self, anon):
        r = anon.post("/api/auth/change-password",
                      json={"current_password": "x", "new_password": "yyyyyyyy"})
        assert r.status_code == 401

    def test_full_change_cycle(self, role_clients):
        admin = role_clients["admin"]
        _purge(admin)
        try:
            assert _new_user(admin, "t_self").status_code == 201

            token = httpx.post(f"{BASE_URL}/api/auth/login",
                               data={"username": "t_self", "password": "scratchpass123"},
                               timeout=30).json()["access_token"]
            me = httpx.Client(base_url=BASE_URL, timeout=30,
                              headers={"Authorization": f"Bearer {token}"})

            # Wrong current password is refused.
            assert me.post("/api/auth/change-password",
                           json={"current_password": "not-it",
                                 "new_password": "changed12345"}).status_code == 401

            # Reusing the same password is refused — it is almost always a
            # mistake, and silently accepting it implies something happened.
            assert me.post("/api/auth/change-password",
                           json={"current_password": "scratchpass123",
                                 "new_password": "scratchpass123"}).status_code == 422

            # Too short is refused by validation.
            assert me.post("/api/auth/change-password",
                           json={"current_password": "scratchpass123",
                                 "new_password": "abc"}).status_code == 422

            # The real change succeeds ...
            assert me.post("/api/auth/change-password",
                           json={"current_password": "scratchpass123",
                                 "new_password": "changed12345"}).status_code == 204
            me.close()

            # ... and takes effect both ways.
            assert httpx.post(f"{BASE_URL}/api/auth/login",
                              data={"username": "t_self", "password": "scratchpass123"},
                              timeout=30).status_code == 401
            assert httpx.post(f"{BASE_URL}/api/auth/login",
                              data={"username": "t_self", "password": "changed12345"},
                              timeout=30).status_code == 200
        finally:
            _purge(admin)


# =============================================================================
# Careers — the student job -> department recommender
# =============================================================================

class TestCareers:

    def test_jobs_catalogue(self, role_clients):
        body = role_clients["student"].get("/api/careers/jobs").json()
        assert len(body) == 33
        assert {"job_title", "job_family"} <= set(body[0])

    def test_search_prefix_ranks_first(self, role_clients):
        body = role_clients["student"].get("/api/careers/search", params={"q": "data"}).json()
        assert body, "expected matches for 'data'"
        assert body[0]["job_title"].lower().startswith("data")

    def test_search_empty_query_rejected(self, role_clients):
        assert role_clients["student"].get("/api/careers/search", params={"q": ""}).status_code == 422

    def test_recommend_returns_ranked_programs(self, role_clients):
        r = role_clients["student"].post("/api/careers/recommend",
                                         json={"job_title": "Data Scientist", "top_n": 5})
        assert r.status_code == 200
        body = r.json()
        assert body["job_family"] == "Data & Analytics"
        assert len(body["recommendations"]) == 5
        ranks = [x["rank"] for x in body["recommendations"]]
        assert ranks == sorted(ranks) == list(range(1, 6))
        scores = [x["score"] for x in body["recommendations"]]
        assert scores == sorted(scores, reverse=True), "recommendations must be ordered by score"

    def test_recommend_top_result_is_a_direct_route(self, role_clients):
        """A data-science target must surface a data programme first, or the
        field-match weighting is not working."""
        body = role_clients["student"].post(
            "/api/careers/recommend", json={"job_title": "Data Scientist"}).json()
        assert body["recommendations"][0]["is_direct_route"] is True

    def test_recommend_is_personalised_only_with_full_profile(self, role_clients):
        full = role_clients["student"].post("/api/careers/recommend", json={
            "job_title": "ML Engineer", "gpa": 3.4, "internships": 1,
            "projects": 3, "communication_score": 7,
        }).json()
        assert full["personalised"] is True

        partial = role_clients["student"].post("/api/careers/recommend", json={
            "job_title": "ML Engineer", "gpa": 3.4,
        }).json()
        assert partial["personalised"] is False, \
            "a partial profile must not be treated as a full one"

    def test_recommend_factors_sum_to_score(self, role_clients):
        body = role_clients["student"].post(
            "/api/careers/recommend", json={"job_title": "Cloud Architect"}).json()
        top = body["recommendations"][0]
        assert abs(sum(f["contribution"] for f in top["factors"]) - top["score"]) < 0.5

    def test_recommend_weights_sum_to_one(self, role_clients):
        body = role_clients["student"].post(
            "/api/careers/recommend", json={"job_title": "Data Scientist"}).json()
        assert abs(sum(body["weights"].values()) - 1.0) < 1e-9

    def test_recommend_unknown_job_404(self, role_clients):
        r = role_clients["student"].post("/api/careers/recommend",
                                         json={"job_title": "Chief Vibes Officer"})
        assert r.status_code == 404

    def test_recommend_rejects_out_of_range_gpa(self, role_clients):
        r = role_clients["student"].post("/api/careers/recommend", json={
            "job_title": "Data Scientist", "gpa": 9.9, "internships": 1,
            "projects": 3, "communication_score": 7,
        })
        assert r.status_code == 422


# =============================================================================
# Labour market (MoL)
# =============================================================================

class TestLabour:

    def test_overview_schema(self, role_clients):
        b = role_clients["mol"].get("/api/labour/overview").json()
        assert b["occupations_tracked"] == 33
        assert b["fields_tracked"] == 9
        assert b["total_openings"] > 0

    def test_emerging_sorted_by_growth(self, role_clients):
        b = role_clients["mol"].get("/api/labour/emerging", params={"level": "family"}).json()
        growths = [r["openings_cagr_pct"] for r in b]
        assert growths == sorted(growths, reverse=True)
        assert b[0]["series"], "each row must carry its yearly series for sparklines"

    def test_emerging_title_level(self, role_clients):
        b = role_clients["mol"].get("/api/labour/emerging",
                                    params={"level": "title", "top_n": 5}).json()
        assert len(b) == 5
        assert "job_title" in b[0]

    def test_emerging_rejects_bad_level(self, role_clients):
        assert role_clients["mol"].get("/api/labour/emerging",
                                       params={"level": "nonsense"}).status_code == 422

    def test_supply_demand_gap(self, role_clients):
        b = role_clients["mol"].get("/api/labour/supply-demand").json()
        assert len(b["fields"]) == 9
        gaps = [f["gap"] for f in b["fields"]]
        assert gaps == sorted(gaps, reverse=True)
        assert b["largest_gap_field"] == b["fields"][0]["field"]
        for f in b["fields"]:
            assert f["supply_total"] == f["supply_graduates"] + f["supply_bootcamp"]
            assert f["severity"] in {"critical", "high", "moderate", "low"}

    def test_mismatch_is_flagged_non_comparable(self, role_clients):
        """The fit distribution is near-uniform in this dataset. Every response
        must say so, or the figures read as a ranking they cannot support."""
        for by in ("overview", "field", "program"):
            b = role_clients["mol"].get("/api/labour/mismatch", params={"by": by}).json()
            assert b["comparable"] is False
            assert "caveat" in b and b["caveat"]

    def test_mismatch_overview_totals(self, role_clients):
        b = role_clients["mol"].get("/api/labour/mismatch").json()
        assert sum(x["count"] for x in b["breakdown"]) == b["total_placed"]
        assert abs(b["match_rate_pct"] + b["mismatch_rate_pct"] - 100) < 0.2

    def test_regional_unknown_field_404(self, role_clients):
        assert role_clients["mol"].get("/api/labour/regional",
                                       params={"field": "Underwater Basket Weaving"}).status_code == 404

    def test_occupation_detail(self, role_clients):
        b = role_clients["mol"].get("/api/labour/occupation/Data Scientist").json()
        assert b["job_family"] == "Data & Analytics"
        assert len(b["series"]) == 6      # 2020-2025


# =============================================================================
# Education supply (MoE)
# =============================================================================

class TestEducation:

    def test_overview_counts(self, role_clients):
        b = role_clients["moe"].get("/api/education/overview").json()
        assert b["institutions"] == 8
        assert b["programs"] == 12
        assert b["fields"] == 9

    def test_investment_quadrant_partitions_all_fields(self, role_clients):
        b = role_clients["moe"].get("/api/education/investment-quadrant").json()
        assert len(b["points"]) == 9
        valid = {"Invest", "Sustain", "Oversupply risk", "Review"}
        for p in b["points"]:
            assert p["quadrant"] in valid
            assert p["action"]

    def test_investment_quadrant_split_is_at_the_median(self, role_clients):
        b = role_clients["moe"].get("/api/education/investment-quadrant").json()
        for p in b["points"]:
            high_d = p["demand_growth_pct"] >= b["demand_median"]
            high_s = p["supply_growth_pct"] >= b["supply_median"]
            expected = {
                (True, False):  "Invest",
                (True, True):   "Sustain",
                (False, True):  "Oversupply risk",
                (False, False): "Review",
            }[(high_d, high_s)]
            assert p["quadrant"] == expected, p["field"]

    def test_investment_priority_ranked_and_auditable(self, role_clients):
        b = role_clients["moe"].get("/api/education/investment-priority").json()
        assert abs(sum(b["weights"].values()) - 1.0) < 1e-9
        scores = [f["score"] for f in b["fields"]]
        assert scores == sorted(scores, reverse=True)
        assert [f["rank"] for f in b["fields"]] == list(range(1, len(b["fields"]) + 1))
        top = b["fields"][0]
        assert abs(sum(f["contribution"] for f in top["factors"]) - top["score"]) < 0.5

    def test_field_detail(self, role_clients):
        b = role_clients["moe"].get("/api/education/field/Cybersecurity").json()
        assert b["field"] == "Cybersecurity"
        assert b["programs"]

    def test_field_detail_unknown_404(self, role_clients):
        assert role_clients["moe"].get("/api/education/field/Nonsense").status_code == 404

    def test_field_detail_handles_slash_in_name(self, role_clients):
        """"AI/ML Engineering" contains a forward slash. The client encodes it
        as %2F but the server decodes it back before routing, so a plain path
        segment never matches — the route needs the :path converter."""
        r = role_clients["moe"].get("/api/education/field/AI/ML Engineering")
        assert r.status_code == 200, f"slash-containing field 404s: {r.status_code}"
        assert r.json()["field"] == "AI/ML Engineering"

    def test_every_field_detail_resolves(self, role_clients):
        """Whatever the quadrant lists must be openable in the field explorer."""
        fields = [p["field"] for p in
                  role_clients["moe"].get("/api/education/investment-quadrant").json()["points"]]
        for field in fields:
            r = role_clients["moe"].get(f"/api/education/field/{field}")
            assert r.status_code == 200, f"{field} → {r.status_code}"


# =============================================================================
# Institution (University) — including row scoping
# =============================================================================

class TestInstitution:

    def test_me_returns_own_institution(self, role_clients):
        b = role_clients["university"].get("/api/institution/me").json()
        assert b["institution"] == "Addis Ababa University"

    def test_cannot_read_another_institution_via_query_param(self, role_clients):
        """Row scoping comes from the signed token, so a crafted parameter must
        be ignored rather than honoured."""
        b = role_clients["university"].get(
            "/api/institution/me", params={"institution": "Southern State"}).json()
        assert b["institution"] == "Addis Ababa University"

        for path in ("/api/institution/portfolio", "/api/institution/expansion",
                     "/api/institution/resources", "/api/institution/benchmark"):
            body = role_clients["university"].get(
                path, params={"institution": "Southern State"}).json()
            assert body["institution"] == "Addis Ababa University", path

    def test_portfolio_has_eight_programs(self, role_clients):
        b = role_clients["university"].get("/api/institution/portfolio").json()
        assert len(b["programs"]) == 8

    def test_expansion_recommendations_valid(self, role_clients):
        b = role_clients["university"].get("/api/institution/expansion").json()
        assert abs(sum(b["weights"].values()) - 1.0) < 1e-9
        scores = [p["score"] for p in b["programs"]]
        assert scores == sorted(scores, reverse=True)
        for p in b["programs"]:
            assert p["recommendation"] in {"Expand", "Hold", "Consolidate"}
            assert p["price_position"] in {"premium", "parity", "discount", "unknown"}
            assert p["rationale"]

    def test_resource_funnel_is_monotonic(self, role_clients):
        """Inquiries >= applications >= enrolments, or the funnel is wrong."""
        b = role_clients["university"].get("/api/institution/resources").json()
        counts = [s["count"] for s in b["funnel"]]
        assert counts == sorted(counts, reverse=True), counts

    def test_benchmark_anonymises_peers(self, role_clients):
        b = role_clients["university"].get("/api/institution/benchmark").json()
        assert b["peer_count"] == 7
        labels = [p["label"] for p in b["peers"]]
        assert all(l.startswith("Peer ") for l in labels)
        # No real institution name may appear anywhere in the peer records.
        blob = str(b["peers"])
        for name in ("Southern State", "Midwest College", "Pacific University",
                     "Mountain Tech", "Northeast Institute", "Coastal University",
                     "State University"):
            assert name not in blob, f"peer data leaked {name}"

    def test_benchmark_declares_metric_direction(self, role_clients):
        b = role_clients["university"].get("/api/institution/benchmark").json()
        assert b["direction"]["acceptance_rate_pct"] == "lower"
        assert b["direction"]["avg_tuition"] == "neutral"
        # A neutral metric must not be given a percentile.
        assert "avg_tuition" not in b["percentile"]


# =============================================================================
# Cross-entity search
# =============================================================================

class TestSearch:

    def test_search_requires_auth(self, anon):
        assert anon.get("/api/search", params={"q": "data"}).status_code == 401

    def test_student_never_sees_institutions(self, role_clients):
        b = role_clients["student"].get("/api/search", params={"q": "tech"}).json()
        assert all(r["kind"] != "institution" for r in b["results"])

    def test_admin_can_see_institutions(self, role_clients):
        b = role_clients["admin"].get("/api/search", params={"q": "tech institute"}).json()
        assert any(r["kind"] == "institution" for r in b["results"])

    def test_mol_sees_occupations_not_programs(self, role_clients):
        b = role_clients["mol"].get("/api/search", params={"q": "data"}).json()
        kinds = {r["kind"] for r in b["results"]}
        assert "occupation" in kinds
        assert "program" not in kinds

    def test_results_carry_a_route(self, role_clients):
        b = role_clients["student"].get("/api/search", params={"q": "data"}).json()
        assert all(r["route"] for r in b["results"])

    def test_empty_query_rejected(self, role_clients):
        assert role_clients["student"].get("/api/search", params={"q": ""}).status_code == 422


# =============================================================================
# Market Demand
# =============================================================================

class TestMarketOverview:

    def test_overview_200(self, client):
        r = client.get("/api/market/overview")
        assert r.status_code == 200

    def test_overview_schema(self, client):
        body = client.get("/api/market/overview").json()
        assert isinstance(body["total_companies"],  int)
        assert isinstance(body["total_placements"], int)
        assert isinstance(body["avg_salary"],       (int, float))
        assert isinstance(body["avg_time_to_hire"], (int, float))
        assert isinstance(body["top_role"],         str)

    def test_overview_realistic_values(self, client):
        body = client.get("/api/market/overview").json()
        assert body["total_companies"]  > 0
        assert body["total_placements"] > 0
        assert body["avg_salary"]       > 0


class TestTopCompanies:

    def test_top_companies_200(self, client):
        r = client.get("/api/market/top-companies")
        assert r.status_code == 200

    def test_top_companies_returns_at_least_5(self, client):
        body = client.get("/api/market/top-companies").json()
        assert isinstance(body, list) and len(body) >= 5

    def test_top_companies_item_schema(self, client):
        body = client.get("/api/market/top-companies").json()
        item = body[0]
        assert isinstance(item["company"], str)
        assert isinstance(item["count"],   int)

    def test_top_companies_n_param(self, client):
        r3  = client.get("/api/market/top-companies", params={"n": 3}).json()
        r10 = client.get("/api/market/top-companies", params={"n": 10}).json()
        assert len(r3)  <= 3
        assert len(r10) <= 10
        assert len(r10) > len(r3)


class TestMarketOther:

    def test_regional_hiring_200(self, client):
        assert client.get("/api/market/regional-hiring").status_code == 200

    def test_job_internship_ratio_schema(self, client):
        body = client.get("/api/market/job-internship-ratio").json()
        assert isinstance(body["job_count"],        int)
        assert isinstance(body["internship_count"], int)
        assert isinstance(body["ratio"],            (int, float))

    def test_skill_gap_top_field(self, client):
        body = client.get("/api/market/skill-gap").json()
        assert isinstance(body["top_gap_skill"], str)
        assert len(body["skills"]) > 0

    def test_hiring_sources_list(self, client):
        body = client.get("/api/market/hiring-sources").json()
        assert isinstance(body, list) and len(body) > 0


class TestDemandForecast:

    def test_forecast_200(self, client):
        assert client.get("/api/market/demand-forecast").status_code == 200

    def test_forecast_returns_12_points(self, client):
        body = client.get("/api/market/demand-forecast").json()
        assert len(body) == 12

    def test_forecast_months_param(self, client):
        for months in (3, 6, 9, 12):
            body = client.get("/api/market/demand-forecast", params={"months": months}).json()
            assert len(body) == months, f"Expected {months} points, got {len(body)}"

    def test_forecast_bounds_order(self, client):
        body = client.get("/api/market/demand-forecast").json()
        for pt in body:
            assert pt["lower_bound"] <= pt["predicted_postings"] <= pt["upper_bound"], \
                f"Bounds violated: {pt}"

    def test_forecast_non_negative(self, client):
        body = client.get("/api/market/demand-forecast").json()
        for pt in body:
            assert pt["lower_bound"] >= 0
            assert pt["predicted_postings"] > 0


# =============================================================================
# Enrollment Intelligence
# =============================================================================

class TestEnrollmentSummary:

    def test_summary_200(self, client):
        assert client.get("/api/enrollment/summary").status_code == 200

    def test_summary_schema(self, client):
        body = client.get("/api/enrollment/summary").json()
        assert isinstance(body["total_students"],     int)
        assert isinstance(body["total_programs"],     int)
        assert isinstance(body["avg_placement_rate"], (int, float))
        assert isinstance(body["top_program"],        str)
        assert isinstance(body["enrollment_by_year"], dict)

    def test_summary_total_programs_12(self, client):
        body = client.get("/api/enrollment/summary").json()
        assert body["total_programs"] == 12

    def test_summary_placement_rate_realistic(self, client):
        body = client.get("/api/enrollment/summary").json()
        rate = body["avg_placement_rate"]
        assert 50 <= rate <= 100, f"Unrealistic placement rate: {rate}"


class TestEnrollmentForecast:

    def test_forecast_200(self, client):
        r = client.get("/api/enrollment/forecast", params={"program": "MS Data Science"})
        assert r.status_code == 200

    def test_forecast_schema(self, client):
        body = client.get("/api/enrollment/forecast",
                          params={"program": "MS Data Science", "years": 3}).json()
        assert isinstance(body["program"],    str)
        assert isinstance(body["historical"], list)
        assert isinstance(body["forecast"],   list)
        assert len(body["forecast"]) == 3

    def test_forecast_years_param(self, client):
        for years in (2, 3, 5):
            body = client.get("/api/enrollment/forecast",
                              params={"program": "MS Data Science", "years": years}).json()
            assert len(body["forecast"]) == years

    def test_forecast_all_12_programs(self, client):
        for prog in KNOWN_PROGRAMS:
            r = client.get("/api/enrollment/forecast", params={"program": prog})
            assert r.status_code == 200, f"Failed for program: {prog}"


class TestAdmissionRisk:

    def test_admission_risk_200(self, client):
        assert client.get("/api/enrollment/admission-risk").status_code == 200

    def test_admission_risk_schema(self, client):
        body = client.get("/api/enrollment/admission-risk").json()
        assert isinstance(body, list) and len(body) > 0
        item = body[0]
        assert isinstance(item["program"],            str)
        assert isinstance(item["risk_score"],         (int, float))
        assert isinstance(item["trend"],              str)
        assert isinstance(item["recommended_intake"], int)

    def test_admission_risk_scores_non_negative(self, client):
        body = client.get("/api/enrollment/admission-risk").json()
        for item in body:
            assert item["risk_score"] >= 0

    def test_admission_risk_trend_valid(self, client):
        body = client.get("/api/enrollment/admission-risk").json()
        valid = {"up", "down", "stable"}
        for item in body:
            assert item["trend"] in valid, f"Invalid trend: {item['trend']}"

    def test_admission_risk_limit_param(self, client):
        r5  = client.get("/api/enrollment/admission-risk", params={"limit": 5}).json()
        r12 = client.get("/api/enrollment/admission-risk", params={"limit": 12}).json()
        assert len(r5)  <= 5
        assert len(r12) <= 12
        assert len(r12) > len(r5)


class TestPlacementByStream:

    def test_placement_by_stream_200(self, client):
        assert client.get("/api/enrollment/placement-by-stream").status_code == 200

    def test_placement_by_stream_12_programs(self, client):
        body = client.get("/api/enrollment/placement-by-stream").json()
        assert len(body) == 12

    def test_placement_by_stream_program_names(self, client):
        body = client.get("/api/enrollment/placement-by-stream").json()
        names = {item["program"] for item in body}
        assert names.issubset(KNOWN_PROGRAMS), f"Unexpected programs: {names - KNOWN_PROGRAMS}"

    def test_placement_by_stream_schema(self, client):
        body = client.get("/api/enrollment/placement-by-stream").json()
        item = body[0]
        assert isinstance(item["placement_rate"], (int, float))
        assert isinstance(item["avg_salary"],     (int, float))
        assert isinstance(item["student_count"],  int)


# =============================================================================
# Placement Prediction (XGBoost + SHAP)
# =============================================================================

class TestPredictPlacement:

    def test_predict_placement_200(self, client):
        r = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT)
        assert r.status_code == 200

    def test_predict_placement_probability_0_to_1(self, client):
        body = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        prob = body["placement_probability"]
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0, f"Probability out of range: {prob}"

    def test_predict_placement_schema(self, client):
        body = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        assert isinstance(body["prediction"],  str)
        assert isinstance(body["base_value"],  (int, float))
        assert isinstance(body["shap_values"], list)
        assert len(body["shap_values"]) > 0

    def test_predict_placement_shap_schema(self, client):
        body = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        sv = body["shap_values"][0]
        assert isinstance(sv["feature"], str)
        assert isinstance(sv["value"],   (int, float))
        assert isinstance(sv["shap"],    (int, float))

    def test_strong_student_placed(self, client):
        body = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        assert body["prediction"] == "Placed"
        assert body["placement_probability"] > 0.5

    def test_directional_ordering(self, client):
        strong = client.post("/api/enrollment/predict-placement", json=STRONG_STUDENT).json()
        weak   = client.post("/api/enrollment/predict-placement", json=WEAK_STUDENT).json()
        assert weak["placement_probability"] < strong["placement_probability"], \
            f"weak {weak['placement_probability']:.3f} should be < strong {strong['placement_probability']:.3f}"

    def test_predict_missing_program_422(self, client):
        body = {k: v for k, v in STRONG_STUDENT.items() if k != "program"}
        r = client.post("/api/enrollment/predict-placement", json=body)
        assert r.status_code == 422

    def test_predict_invalid_gpa_422(self, client):
        body = {**STRONG_STUDENT, "gpa": 9.9}
        r = client.post("/api/enrollment/predict-placement", json=body)
        assert r.status_code == 422


class TestSkillRoadmapValidation:
    """skill-roadmap takes the same profile as predict-placement and feeds it to
    the same model, so it must reject the same out-of-range values."""

    def test_roadmap_valid_profile_200(self, client):
        r = client.post("/api/enrollment/skill-roadmap", json=STRONG_STUDENT)
        assert r.status_code == 200

    @pytest.mark.parametrize("field,bad_value", [
        ("gpa",                  9.9),   # above the 4.0 scale
        ("gpa",                 -1.0),   # negative
        ("internships",          -3),
        ("projects",             -1),
        ("communication_score",  99),    # scale is 1-10
        ("communication_score",   0),
    ])
    def test_roadmap_rejects_out_of_range(self, client, field, bad_value):
        body = {**STRONG_STUDENT, field: bad_value}
        r = client.post("/api/enrollment/skill-roadmap", json=body)
        assert r.status_code == 422, f"{field}={bad_value} was accepted"

    @pytest.mark.parametrize("field,bad_value", [
        ("gpa",                 -1.0),
        ("internships",          -3),
        ("communication_score",   0),
    ])
    def test_predict_placement_rejects_out_of_range(self, client, field, bad_value):
        body = {**STRONG_STUDENT, field: bad_value}
        r = client.post("/api/enrollment/predict-placement", json=body)
        assert r.status_code == 422, f"{field}={bad_value} was accepted"


class TestSkillRecommendations:

    def test_skill_recommendations_200(self, client):
        assert client.get("/api/enrollment/skill-recommendations").status_code == 200

    def test_skill_recommendations_schema(self, client):
        body = client.get("/api/enrollment/skill-recommendations").json()
        assert isinstance(body["recommendations"],      list)
        assert isinstance(body["alternative_pathways"], list)
        assert len(body["recommendations"]) > 0

    def test_skill_priority_valid(self, client):
        body = client.get("/api/enrollment/skill-recommendations").json()
        valid = {"High", "Medium", "Low"}
        for rec in body["recommendations"]:
            assert rec["priority"] in valid, f"Invalid priority: {rec['priority']}"


# =============================================================================
# Monitoring
# =============================================================================

class TestMonitoring:

    def test_drift_200(self, client):
        assert client.get("/api/monitoring/drift").status_code == 200

    def test_drift_schema(self, client):
        body = client.get("/api/monitoring/drift").json()
        assert isinstance(body["total_logged"],     int)
        assert isinstance(body["baseline"],         (int, float))
        assert isinstance(body["drift"],            (int, float))
        assert isinstance(body["alert"],            bool)
        assert isinstance(body["recommendation"],   str)

    def test_predictions_log_200(self, client):
        assert client.get("/api/monitoring/predictions").status_code == 200

    def test_predictions_log_list(self, client):
        body = client.get("/api/monitoring/predictions").json()
        assert isinstance(body, list)

    def test_predictions_n_param(self, client):
        r1  = client.get("/api/monitoring/predictions", params={"n": 1}).json()
        r10 = client.get("/api/monitoring/predictions", params={"n": 10}).json()
        assert len(r1) <= 1
        assert len(r10) <= 10


# =============================================================================
# Cross-Endpoint Consistency
# =============================================================================

class TestDataConsistency:

    def test_student_count_matches_streams(self, client):
        summary = client.get("/api/enrollment/summary").json()
        streams = client.get("/api/enrollment/placement-by-stream").json()
        stream_total = sum(s["student_count"] for s in streams)
        assert summary["total_students"] == stream_total, \
            f"summary total {summary['total_students']} != stream total {stream_total}"

    def test_top_program_in_known_list(self, client):
        body = client.get("/api/enrollment/summary").json()
        assert body["top_program"] in KNOWN_PROGRAMS
