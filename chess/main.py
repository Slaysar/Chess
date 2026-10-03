from tools.color import Color
from tools.position import Position
from tools.board import Board
from figures.pawn import Pawn
from figures.rook import Rook

if __name__ == "__main__":
    print("Debug")
    color = Color("black")
    pos = Position('c2')

    board = Board()
    rook = Rook(board, pos, color)
    pawn = Pawn(board, Position('c3'), Color('white'))
    pawn2 = Pawn(board, Position('c4'), Color('white'))

    print(board.board)
    print(rook.get_possible_moves())


