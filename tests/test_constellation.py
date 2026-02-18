"""Tests for the Constellation View API (Phase 6).

Covers:
  - Graph data endpoint returns nodes + edges
  - Node structure includes required fields
  - Edges reflect dependency relationships
  - Ghost nodes flagged correctly
  - Dependents count calculated
"""

import pytest

from app import create_app


@pytest.fixture()
def client():
    application = create_app(start_health_loop=False)
    application.config["TESTING"] = True
    with application.test_client() as c:
        yield c


class TestConstellationAPI:
    """GET /api/constellation."""

    def test_returns_200(self, client):
        resp = client.get("/api/constellation")
        assert resp.status_code == 200

    def test_contains_nodes_and_edges(self, client):
        data = client.get("/api/constellation").get_json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_node_count_matches_registry(self, client):
        data = client.get("/api/constellation").get_json()
        services = client.get("/api/services").get_json()
        assert len(data["nodes"]) == len(services)

    def test_node_has_required_fields(self, client):
        data = client.get("/api/constellation").get_json()
        required = {
            "id", "name", "group", "port", "status",
            "ghost", "description", "favicon", "dependents",
        }
        for node in data["nodes"]:
            assert required.issubset(set(node.keys())), (
                f"Node {node.get('id')} missing fields: "
                f"{required - set(node.keys())}"
            )

    def test_ghost_nodes_flagged(self, client):
        data = client.get("/api/constellation").get_json()
        ghosts = [n for n in data["nodes"] if n["ghost"]]
        assert len(ghosts) >= 4  # sophia, amtl-tts, dhamma-mirror, after-i-go

    def test_ghost_nodes_have_eta(self, client):
        data = client.get("/api/constellation").get_json()
        ghosts = [n for n in data["nodes"] if n["ghost"]]
        for g in ghosts:
            assert g.get("ghost_eta"), f"Ghost {g['id']} has no ETA"

    def test_edges_from_dependencies(self, client):
        data = client.get("/api/constellation").get_json()
        edges = data["edges"]
        # foreperson depends on supervisor
        dep_edge = [
            e for e in edges
            if e["source"] == "supervisor" and e["target"] == "foreperson"
        ]
        assert len(dep_edge) == 1
        assert dep_edge[0]["type"] == "hard"

    def test_inspector_depends_on_foreperson(self, client):
        data = client.get("/api/constellation").get_json()
        edges = data["edges"]
        dep = [
            e for e in edges
            if e["source"] == "foreperson" and e["target"] == "inspector"
        ]
        assert len(dep) == 1

    def test_dependents_count(self, client):
        data = client.get("/api/constellation").get_json()
        # Supervisor has at least 2 dependents: foreperson, genie
        sup = next(n for n in data["nodes"] if n["id"] == "supervisor")
        assert sup["dependents"] >= 2

    def test_services_with_no_deps_have_no_incoming_edges(self, client):
        data = client.get("/api/constellation").get_json()
        targets = {e["target"] for e in data["edges"]}
        elaine = next(n for n in data["nodes"] if n["id"] == "elaine")
        assert elaine["id"] not in targets
        assert elaine["dependents"] == 0
