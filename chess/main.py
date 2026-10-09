from pieces.bishop import Bishop
from tools.color import Color
from tools.position import Position
from tools.board import Board
from pieces.pawn import Pawn
from pieces.rook import Rook
from pieces.bishop import Bishop

if __name__ == "__main__":
    board = Board()
    rook = Rook(Color.WHITE)
    bishop = Bishop(Color.BLACK)
    black_pawn = Pawn(Color.BLACK)
    white_pawn = Pawn(Color.WHITE)

    rook_pos = Position.from_str("e3")
    board.place(rook, rook_pos)

    board.place(black_pawn, Position.from_str("e4"))
    board.place(white_pawn, Position.from_str("d3"))

    bishop_pos = Position.from_str("d5")
    board.place(bishop, bishop_pos)

    print(board)
    print(sorted(map(str, rook.get_possible_moves(board, rook_pos))))
    print(sorted(map(str, bishop.get_possible_moves(board, bishop_pos))))