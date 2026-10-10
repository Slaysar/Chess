import dataclasses
import pytest
from tools.color import Color
from tools.move_record import MoveRecord, history_text
from pieces.king import King
from pieces.knight import Knight
from pieces.pawn import Pawn
from pieces.queen import Queen
from pieces.rook import Rook
from tests.helpers import pos


def build(piece, src, dst, *, capture=False, castling=False, promotion=None, rivals=()):
    return MoveRecord.build(
        piece, pos(src), pos(dst),
        is_capture=capture, castling=castling,
        promotion=promotion, rivals=[pos(r) for r in rivals],
    )


# ---------- disambiguation ----------

def test_disambiguation_no_rivals():
    assert MoveRecord.disambiguation(pos("a1"), []) == ""


def test_disambiguation_by_file_when_rival_on_other_file():
    assert MoveRecord.disambiguation(pos("a1"), [pos("h1")]) == "a"


def test_disambiguation_by_rank_when_rival_on_same_file():
    assert MoveRecord.disambiguation(pos("a1"), [pos("a5")]) == "1"


def test_disambiguation_by_file_and_rank_when_both_clash():
    rivals = [pos("h1"), pos("a5")]  # один на той же горизонтали, другой на той же вертикали
    assert MoveRecord.disambiguation(pos("a1"), rivals) == "a1"


# ---------- build: обычные ходы ----------

def test_build_pawn_push():
    assert build(Pawn(Color.WHITE), "e2", "e4").notation == "e4"


def test_build_pawn_capture_starts_with_file():
    assert build(Pawn(Color.WHITE), "e4", "d5", capture=True).notation == "exd5"


def test_build_knight_move():
    assert build(Knight(Color.WHITE), "g1", "f3").notation == "Nf3"


def test_build_piece_capture():
    assert build(Queen(Color.WHITE), "h5", "f7", capture=True).notation == "Qxf7"


def test_build_keeps_source_and_destination():
    record = build(Knight(Color.WHITE), "g1", "f3")
    assert record.source == pos("g1")
    assert record.destination == pos("f3")


# ---------- build: особые ходы ----------

def test_build_kingside_castling():
    assert build(King(Color.WHITE), "e1", "g1", castling=True).notation == "O-O"


def test_build_queenside_castling():
    assert build(King(Color.BLACK), "e8", "c8", castling=True).notation == "O-O-O"


def test_build_promotion():
    assert build(Pawn(Color.WHITE), "e7", "e8", promotion=Queen).notation == "e8=Q"


def test_build_promotion_with_capture():
    record = build(Pawn(Color.WHITE), "e7", "d8", capture=True, promotion=Knight)
    assert record.notation == "exd8=N"


def test_build_uses_disambiguation_for_pieces():
    record = build(Rook(Color.WHITE), "a1", "d1", rivals=["h1"])
    assert record.notation == "Rad1"


def test_build_pawn_ignores_rivals():
    record = build(Pawn(Color.WHITE), "e2", "e4", rivals=["d2"])
    assert record.notation == "e4"


# ---------- with_suffix ----------

def test_with_suffix_adds_check_and_mate():
    record = build(Queen(Color.WHITE), "h5", "f7", capture=True)
    assert record.with_suffix("+").notation == "Qxf7+"
    assert record.with_suffix("#").notation == "Qxf7#"


def test_with_suffix_returns_new_record_and_keeps_old():
    record = build(Knight(Color.WHITE), "g1", "f3")
    new = record.with_suffix("+")
    assert record.notation == "Nf3"
    assert new.notation == "Nf3+"
    assert new.source == record.source and new.destination == record.destination


# ---------- history_text ----------

def make(notation):
    return MoveRecord(pos("a1"), pos("a2"), notation)


def test_history_text_empty():
    assert history_text([]) == ""


def test_history_text_single_move():
    assert history_text([make("e4")]) == "1. e4"


def test_history_text_full_move_pair():
    assert history_text([make("e4"), make("e5")]) == "1. e4 e5"


def test_history_text_numbers_each_white_move():
    records = [make(n) for n in ("e4", "e5", "Nf3")]
    assert history_text(records) == "1. e4 e5 2. Nf3"


def test_history_text_ten_moves():
    records = [make(f"m{i}") for i in range(1, 21)]
    text = history_text(records)
    assert text.startswith("1. m1 m2 2. m3 m4")
    assert text.endswith("10. m19 m20")
