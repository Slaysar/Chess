from __future__ import annotations
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING
from tools.position import Position
from pieces.pawn import Pawn

if TYPE_CHECKING:
    from pieces.piece import Piece


@dataclass(frozen=True)
class MoveRecord:
    source: Position
    destination: Position
    notation: str          # 'e4', 'Nf3', 'exd5', 'O-O', 'e8=Q', 'Qxf7#'

    @staticmethod
    def disambiguation(source: Position, rivals: list[Position]) -> str:
        """Уточнение, если на ту же клетку может пойти такая же фигура: Rad1, N1c3"""
        if not rivals:
            return ""
        file, rank = Position.CHARS[source.col], str(source.row + 1)
        if all(r.col != source.col for r in rivals):
            return file
        if all(r.row != source.row for r in rivals):
            return rank
        return file + rank

    @classmethod
    def build(cls, piece: Piece, source: Position, destination: Position, *,
              is_capture: bool, castling: bool,
              promotion: type[Piece] | None, rivals: list[Position]) -> MoveRecord:
        if castling:
            text = "O-O" if destination.col > source.col else "O-O-O"
        else:
            capture = "x" if is_capture else ""
            if isinstance(piece, Pawn):
                text = (Position.CHARS[source.col] if is_capture else "") + capture + str(destination)
            else:
                text = piece.SYMBOL + cls.disambiguation(source, rivals) + capture + str(destination)
            if promotion is not None:
                text += "=" + promotion.SYMBOL
        return cls(source, destination, text)

    def with_suffix(self, suffix: str) -> MoveRecord:
        """Запись с '+' или '#' в конце (сама запись неизменяемая)"""
        return replace(self, notation=self.notation + suffix)


def history_text(records: list[MoveRecord]) -> str:
    """'1. e4 e5 2. Nf3 Nc6'"""
    parts = []
    for i, record in enumerate(records):
        if i % 2 == 0:
            parts.append(f"{i // 2 + 1}.")
        parts.append(record.notation)
    return " ".join(parts)