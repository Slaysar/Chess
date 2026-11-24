import pytest
from fastapi.testclient import TestClient

from tools.color import Color
from web.app import app, games, clocks


@pytest.fixture
def client():
    games.clear()
    return TestClient(app)


def create(client, **body):
    return client.post("/api/games", json=body).json()


def join(client, game_id):
    return client.post(f"/api/games/{game_id}/join")


def move(client, game_id, source, destination, token=None):
    headers = {"X-Player-Token": token} if token else {}
    return client.post(f"/api/games/{game_id}/move",
                       json={"source": source, "destination": destination}, headers=headers)


# ---------- токены ----------

def test_create_game_returns_token_and_color(client):
    data = create(client, opponent="human")
    assert data["token"]
    assert data["color"] == "white"
    assert data["waiting_for_opponent"] is True


def test_move_without_token_is_rejected(client):
    data = create(client)
    assert move(client, data["id"], "e2", "e4").status_code == 401


def test_move_with_wrong_token_is_rejected(client):
    data = create(client)
    assert move(client, data["id"], "e2", "e4", token="nope").status_code == 401
    assert client.get(f"/api/games/{data['id']}").json()["history"] == []


def test_cannot_move_for_the_opponent(client):
    data = create(client)
    black = join(client, data["id"]).json()
    assert black["color"] == "black"
    assert black["token"] != data["token"]

    assert move(client, data["id"], "e2", "e4", token=black["token"]).status_code == 403   # ход белых
    assert move(client, data["id"], "e2", "e4", token=data["token"]).status_code == 200
    assert move(client, data["id"], "e7", "e5", token=data["token"]).status_code == 403    # теперь ход чёрных
    assert move(client, data["id"], "e7", "e5", token=black["token"]).status_code == 200


def test_token_of_another_game_does_not_work(client):
    first, second = create(client), create(client)
    assert move(client, second["id"], "e2", "e4", token=first["token"]).status_code == 401


def test_join_works_only_once(client):
    data = create(client)
    assert join(client, data["id"]).status_code == 200
    assert join(client, data["id"]).status_code == 409
    assert client.get(f"/api/games/{data['id']}").json()["waiting_for_opponent"] is False


def test_cannot_join_game_with_bot(client):
    data = create(client, opponent="greedy")
    assert join(client, data["id"]).status_code == 409


def test_join_unknown_game_returns_404(client):
    assert join(client, "nope").status_code == 404


# ---------- несколько партий ----------

def test_many_games_have_own_tokens_and_state(client):
    games_data = [create(client) for _ in range(5)]
    assert len({g["token"] for g in games_data}) == 5
    move(client, games_data[0]["id"], "e2", "e4", token=games_data[0]["token"])
    assert client.get(f"/api/games/{games_data[0]['id']}").json()["turn"] == "black"
    assert client.get(f"/api/games/{games_data[1]['id']}").json()["turn"] == "white"


# ---------- часы ----------

def test_clock_has_chosen_minutes(client):
    assert create(client, minutes=5)["clock"]["white"] == 300
    assert create(client, minutes=10)["clock"]["black"] == 600


def test_unknown_time_control_returns_400(client):
    assert client.post("/api/games", json={"minutes": 3}).status_code == 400


def test_clock_starts_after_first_move(client):
    data = create(client)
    assert data["clock"]["running"] is None
    state = move(client, data["id"], "e2", "e4", token=data["token"]).json()
    assert state["clock"]["running"] == "black"


def test_timeout_ends_game_and_blocks_moves(client):
    data = create(client)
    black = join(client, data["id"]).json()
    move(client, data["id"], "e2", "e4", token=data["token"])

    clocks[data["id"]].left[Color.BLACK] = 0.0       # у чёрных (часы идут) время вышло
    state = client.get(f"/api/games/{data['id']}").json()
    assert state["status"] == "timeout"
    assert state["game_over"] is True
    assert state["winner"] == "white"

    assert move(client, data["id"], "e7", "e5", token=black["token"]).status_code == 400


def test_clock_stops_after_checkmate(client):
    data = create(client)
    black = join(client, data["id"]).json()
    white_token, black_token = data["token"], black["token"]
    for source, destination, token in [("f2", "f3", white_token), ("e7", "e5", black_token),
                                       ("g2", "g4", white_token), ("d8", "h4", black_token)]:
        assert move(client, data["id"], source, destination, token=token).status_code == 200
    state = client.get(f"/api/games/{data['id']}").json()
    assert state["status"] == "checkmate"
    assert state["clock"]["running"] is None