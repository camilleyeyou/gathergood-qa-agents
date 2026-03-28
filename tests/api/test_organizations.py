"""Organization API tests — TORG-01 through TORG-04.

Covers:
  TORG-01: Create org auto-assigns OWNER role
  TORG-02: List orgs returns all memberships with role field
  TORG-03: OWNER can update org details via PATCH (slug-based URL)
  TORG-04: Org slug is auto-generated with dedup suffix on name collision
"""
import pytest

from factories.common import org_name
from helpers.api import assert_status


@pytest.mark.req("TORG-01")
def test_create_org_assigns_owner_role(auth_client, teardown_registry):
    """POST /organizations/ returns 201 with role=OWNER, slug, and id."""
    resp = auth_client.post(
        "/organizations/",
        json={"name": org_name(), "description": "Test org"},
    )
    assert_status(resp, 201, "POST /organizations/")
    data = resp.json()

    assert data["role"] == "OWNER", f"Expected role OWNER, got {data.get('role')}"
    assert "slug" in data, "Response missing 'slug' field"
    assert "id" in data, "Response missing 'id' field"

    teardown_registry["org_ids"].append({"slug": data["slug"]})


@pytest.mark.req("TORG-02")
def test_list_orgs_for_member(auth_client, org):
    """GET /organizations/ returns a list of orgs the user belongs to, each with a role field."""
    # `org` fixture ensures at least one org exists for this user
    resp = auth_client.get("/organizations/")
    assert_status(resp, 200, "GET /organizations/")
    data = resp.json()

    assert isinstance(data, list), f"Expected list, got {type(data).__name__}"
    assert len(data) >= 1, "Expected at least one org in list"

    for item in data:
        assert "role" in item, f"Org item missing 'role' field: {item}"

    owner_orgs = [o for o in data if o.get("role") == "OWNER"]
    assert len(owner_orgs) >= 1, "Expected at least one org where user is OWNER"


@pytest.mark.req("TORG-03")
def test_update_org_as_owner(auth_client, org):
    """PATCH /organizations/{slug}/ updates org details; URL uses slug not UUID."""
    resp = auth_client.patch(
        f"/organizations/{org['slug']}/",
        json={"description": "Updated by test"},
    )
    assert_status(resp, 200, f"PATCH /organizations/{org['slug']}/")
    data = resp.json()

    assert data["description"] == "Updated by test", (
        f"Expected description 'Updated by test', got {data.get('description')}"
    )


@pytest.mark.req("TORG-04")
def test_org_slug_auto_generated_with_dedup(auth_client, teardown_registry):
    """Creating two orgs with the same name produces different slugs (second gets a suffix)."""
    name = org_name()

    resp1 = auth_client.post("/organizations/", json={"name": name})
    assert_status(resp1, 201, "POST /organizations/ (first org)")
    data1 = resp1.json()
    slug1 = data1["slug"]
    teardown_registry["org_ids"].append({"slug": slug1})

    resp2 = auth_client.post("/organizations/", json={"name": name})
    assert_status(resp2, 201, "POST /organizations/ (second org, same name)")
    data2 = resp2.json()
    slug2 = data2["slug"]
    teardown_registry["org_ids"].append({"slug": slug2})

    assert slug1 != slug2, (
        f"Expected unique slugs for duplicate org names, got {slug1!r} and {slug2!r}"
    )
    assert slug2.startswith(slug1), (
        f"Expected second slug to start with first slug (dedup suffix), "
        f"got {slug1!r} and {slug2!r}"
    )
