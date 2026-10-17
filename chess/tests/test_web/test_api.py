import pytest
from fastapi.testclient import TestClient

from bots.minimax import MinimaxBot
from tools.color import Color
from pieces.king import King
from pieces.pawn import Pawn
from tests.helpers import pos
from web.app import app, games
from web.app import BOTS


@pytest.fixture
def client():
    games.clear()  # партии лежат в глобальном словаре
    return TestClient(app)


def new_game(client) -> str:
    return client.post("/api/games").json()["id"]


def move(client, game_id, source, destination, promotion=None):
    return client.post(f"/api/games/{game_id}/move",
                       json={"source": source, "destination": destination, "promotion": promotion})


def squares(state) -> dict:
    return {p["square"]: p for p in state["pieces"]}


# ---------- страница и статика ----------

def test_index_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Шахматы" in response.text


@pytest.mark.parametrize("path", ["/static/style.css", "/static/app.js"])
def test_static_files_are_served(client, path):
    assert client.get(path).status_code == 200


# ---------- создание партии и состояние ----------

def test_create_game_returns_start_position(client):
    data = client.post("/api/games").json()
    assert data["id"]
    assert len(data["pieces"]) == 32
    assert data["turn"] == "white"
    assert data["status"] == "playing"
    assert data["game_over"] is False
    assert data["history"] == []
    assert data["last_move"] is None
    assert data["check_square"] is None


def test_pieces_are_serialized_with_square_type_and_color(client):
    pieces = squares(client.post("/api/games").json())
    assert pieces["e1"] == {"square": "e1", "type": "K", "color": "white"}
    assert pieces["d8"] == {"square": "d8", "type": "Q", "color": "black"}
    assert pieces["a2"]["type"] == "P"


def test_get_state_matches_created_game(client):
    created = client.post("/api/games").json()
    state = client.get(f"/api/games/{created['id']}").json()
    assert state["pieces"] == created["pieces"]
    assert state["turn"] == "white"


def test_unknown_game_returns_404(client):
    assert client.get("/api/games/nope").status_code == 404
    assert client.get("/api/games/nope/moves?square=e2").status_code == 404
    assert move(client, "nope", "e2", "e4").status_code == 404


def test_games_are_independent(client):
    first, second = new_game(client), new_game(client)
    move(client, first, "e2", "e4")
    assert client.get(f"/api/games/{first}").json()["turn"] == "black"
    assert client.get(f"/api/games/{second}").json()["turn"] == "white"


# ---------- легальные ходы ----------

def test_moves_of_pawn_on_start(client):
    game_id = new_game(client)
    data = client.get(f"/api/games/{game_id}/moves?square=e2").json()
    assert data == {"moves": ["e3", "e4"], "promotions": []}


def test_moves_of_knight_on_start(client):
    game_id = new_game(client)
    data = client.get(f"/api/games/{game_id}/moves?square=g1").json()
    assert data["moves"] == ["f3", "h3"]


def test_no_moves_for_opponent_piece(client):
    game_id = new_game(client)
    data = client.get(f"/api/games/{game_id}/moves?square=e7").json()
    assert data == {"moves": [], "promotions": []}


def test_no_moves_for_empty_square(client):
    game_id = new_game(client)
    data = client.get(f"/api/games/{game_id}/moves?square=e4").json()
    assert data == {"moves": [], "promotions": []}


def test_moves_with_invalid_square_returns_400(client):
    game_id = new_game(client)
    assert client.get(f"/api/games/{game_id}/moves?square=z9").status_code == 400


# ---------- ходы ----------

def test_move_updates_state(client):
    game_id = new_game(client)
    response = move(client, game_id, "e2", "e4")
    assert response.status_code == 200
    data = response.json()
    assert data["turn"] == "black"
    assert data["history"] == ["e4"]
    assert data["last_move"] == {"source": "e2", "destination": "e4"}
    pieces = squares(data)
    assert "e2" not in pieces
    assert pieces["e4"]["type"] == "P"


def test_state_after_move_is_kept_on_server(client):
    game_id = new_game(client)
    move(client, game_id, "e2", "e4")
    data = client.get(f"/api/games/{game_id}").json()
    assert data["history"] == ["e4"]
    assert data["turn"] == "black"


def test_illegal_move_returns_400_with_message(client):
    game_id = new_game(client)
    response = move(client, game_id, "e2", "e5")
    assert response.status_code == 400
    assert response.json()["detail"] == "Недопустимый ход"


def test_illegal_move_changes_nothing(client):
    game_id = new_game(client)
    move(client, game_id, "e2", "e5")
    data = client.get(f"/api/games/{game_id}").json()
    assert data["turn"] == "white"
    assert data["history"] == []
    assert squares(data)["e2"]["type"] == "P"


def test_wrong_turn_returns_400(client):
    game_id = new_game(client)
    response = move(client, game_id, "e7", "e5")
    assert response.status_code == 400
    assert response.json()["detail"] == "Сейчас ходит другой цвет"


def test_empty_source_returns_400(client):
    game_id = new_game(client)
    response = move(client, game_id, "e4", "e5")
    assert response.status_code == 400
    assert response.json()["detail"] == "На клетке нет фигуры"


def test_invalid_square_string_returns_400(client):
    game_id = new_game(client)
    assert move(client, game_id, "z9", "e4").status_code == 400


def test_unknown_promotion_piece_returns_400(client):
    game_id = new_game(client)
    assert move(client, game_id, "e2", "e4", promotion="x").status_code == 400


# ---------- конец партии ----------

def test_fools_mate_ends_game(client):
    game_id = new_game(client)
    for source, destination in [("f2", "f3"), ("e7", "e5"), ("g2", "g4"), ("d8", "h4")]:
        assert move(client, game_id, source, destination).status_code == 200
    data = client.get(f"/api/games/{game_id}").json()
    assert data["status"] == "checkmate"
    assert data["game_over"] is True
    assert data["winner"] == "black"
    assert data["check_square"] == "e1"
    assert data["history"][-1] == "Qh4#"


def test_no_moves_after_checkmate(client):
    game_id = new_game(client)
    for source, destination in [("f2", "f3"), ("e7", "e5"), ("g2", "g4"), ("d8", "h4")]:
        move(client, game_id, source, destination)
    assert move(client, game_id, "e2", "e3").status_code == 400


def test_draw_has_reason(client):
    game_id = new_game(client)
    game = games[game_id]
    game.board.clear()
    game.board.place(King(Color.WHITE), pos("e1"))
    game.board.place(King(Color.BLACK), pos("e8"))
    data = client.get(f"/api/games/{game_id}").json()
    assert data["status"] == "draw"
    assert data["game_over"] is True
    assert data["draw_reason"] == "недостаточно материала"
    assert data["winner"] is None


# ---------- превращение пешки ----------

def promotion_game(client) -> str:
    """Белая пешка на e7, короли далеко"""
    game_id = new_game(client)
    game = games[game_id]
    game.board.clear()
    game.board.place(King(Color.WHITE), pos("a1"))
    game.board.place(King(Color.BLACK), pos("h6"))
    game.board.place(Pawn(Color.WHITE), pos("e7"))
    game.positions = [game.position_key()]
    return game_id


def test_moves_report_promotion_squares(client):
    game_id = promotion_game(client)
    data = client.get(f"/api/games/{game_id}/moves?square=e7").json()
    assert data == {"moves": ["e8"], "promotions": ["e8"]}


def test_promotion_to_chosen_piece(client):
    game_id = promotion_game(client)
    response = move(client, game_id, "e7", "e8", promotion="n")
    assert response.status_code == 200
    data = response.json()
    assert squares(data)["e8"] == {"square": "e8", "type": "N", "color": "white"}
    assert data["history"] == ["e8=N"]


def test_promotion_without_choice_returns_400(client):
    game_id = promotion_game(client)
    assert move(client, game_id, "e7", "e8").status_code == 400
    assert squares(client.get(f"/api/games/{game_id}").json())["e7"]["type"] == "P"


def test_game_against_bot_replies_in_separate_request(client):
    data = client.post("/api/games", json={"opponent": "greedy"}).json()
    after_human = move(client, data["id"], "e2", "e4").json()
    assert len(after_human["history"]) == 1
    assert after_human["turn"] == "black"

    reply = client.post(f"/api/games/{data['id']}/bot-move")
    assert reply.status_code == 200
    state = reply.json()
    assert len(state["history"]) == 2
    assert state["turn"] == "white"


def test_game_against_advanced_bot(client, monkeypatch):
    monkeypatch.setitem(BOTS, "advanced", lambda: MinimaxBot(depth=2))    # в тестах глубина поменьше
    data = client.post("/api/games", json={"opponent": "advanced"}).json()
    move(client, data["id"], "e2", "e4")
    state = client.post(f"/api/games/{data['id']}/bot-move").json()
    assert len(state["history"]) == 2


def test_bot_move_does_nothing_on_humans_turn(client):
    data = client.post("/api/games", json={"opponent": "greedy"}).json()
    response = client.post(f"/api/games/{data['id']}/bot-move")
    assert response.status_code == 200
    assert response.json()["history"] == []


def test_bot_move_without_bot_returns_400(client):
    game_id = new_game(client)
    assert client.post(f"/api/games/{game_id}/bot-move").status_code == 400


def test_bot_move_unknown_game_returns_404(client):
    assert client.post("/api/games/nope/bot-move").status_code == 404
