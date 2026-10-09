from game import Game
from tools.game_status import GameStatus
from tools.position import Position
from pieces.piece import Piece


def ask_promotion() -> type[Piece]:
    while True:
        choice = input("Превращение (q - ферзь, r - ладья, b - слон, n - конь) [q]: ").strip().lower() or "q"
        if choice in Game.PROMOTION_PIECES:
            return Game.PROMOTION_PIECES[choice]
        print("Недопустимая фигура")


def parse_move(raw: str) -> tuple[Position, Position]:
    """'e2 e4' или 'e2e4' -> (Position, Position)"""
    raw = raw.replace(" ", "").lower()
    if len(raw) != 4:
        raise ValueError("Формат хода: e2 e4")
    return Position.from_str(raw[:2]), Position.from_str(raw[2:])


def main() -> None:
    game = Game()
    while True:
        print()
        print(game.board)
        status = game.status()

        if status is GameStatus.CHECKMATE:
            print(f"Мат. Победили {game.turn.opposite}.")
            break
        if status is GameStatus.STALEMATE:
            print("Пат. Ничья.")
            break
        if status is GameStatus.CHECK:
            print("Шах")

        raw = input(f"Ходят {game.turn} (например e2 e4, q для выхода): ").strip()
        if raw.lower() in ("q", "quit", "exit"):
            print("Выход.")
            break

        try:
            source, destination = parse_move(raw)
            promotion = None
            if game.is_promotion(source, destination) and destination in game.legal_moves(source):
                promotion = ask_promotion()
            game.make_move(source, destination, promotion)
        except ValueError as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
