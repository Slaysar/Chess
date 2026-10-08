from tools.color import Color
from tools.position import Position
from tools.board import Board
from figures.pawn import Pawn
from figures.rook import Rook

if __name__ == "__main__":
    board = Board()
    rook = Rook(Color.WHITE)
    black_pawn = Pawn(Color.BLACK)
    white_pawn = Pawn(Color.WHITE)

    rook_pos = Position.from_str("e3")
    board.place(rook, rook_pos)
    board.place(black_pawn, Position.from_str("e4"))
    board.place(white_pawn, Position.from_str("d3"))

    print(board)
    print(sorted(map(str, rook.get_possible_moves(board, rook_pos))))