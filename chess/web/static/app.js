const FILES = "abcdefgh";
// U+FE0E заставляет браузер рисовать шахматные значки текстом, а не эмодзи
const GLYPHS = { K: "♚", Q: "♛", R: "♜", B: "♝", N: "♞", P: "♟\uFE0E" };
const NO_MOVES = { moves: [], promotions: [] };

let gameId = null;
let state = null;
let selected = null;
let legal = NO_MOVES;

async function api(path, options = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Ошибка запроса");
  return data;
}

function saveId(id) {
  try { localStorage.setItem("chess-game-id", id); } catch (_) {}
}
function loadId() {
  try { return localStorage.getItem("chess-game-id"); } catch (_) { return null; }
}

async function newGame() {
  const data = await api("/api/games", { method: "POST" });
  gameId = data.id;
  saveId(gameId);
  setState(data);
}

function setState(newState) {
  state = newState;
  selected = null;
  legal = NO_MOVES;
  render();
}

function showError(message) {
  document.getElementById("error").textContent = message || "";
}

function statusText() {
  const side = state.turn === "white" ? "белых" : "чёрных";
  switch (state.status) {
    case "checkmate": return `Мат. Победили ${state.winner === "white" ? "белые" : "чёрные"}.`;
    case "stalemate": return "Пат. Ничья.";
    case "draw": return `Ничья: ${state.draw_reason}.`;
    case "check": return `Шах. Ход ${side}.`;
    default: return `Ход ${side}.`;
  }
}

function render() {
  document.getElementById("status").textContent = statusText();

  const pieces = Object.fromEntries(state.pieces.map((p) => [p.square, p]));
  const board = document.getElementById("board");
  board.innerHTML = "";

  for (let row = 7; row >= 0; row--) {           // белые внизу
    for (let col = 0; col < 8; col++) {
      const square = FILES[col] + (row + 1);
      const cell = document.createElement("div");
      cell.className = "cell " + ((row + col) % 2 === 0 ? "dark" : "light");
      cell.dataset.square = square;

      const last = state.last_move;
      if (last && (square === last.source || square === last.destination)) cell.classList.add("last");
      if (square === state.check_square) cell.classList.add("check");
      if (square === selected) cell.classList.add("selected");
      if (legal.moves.includes(square)) {
        cell.classList.add("target");
        if (pieces[square]) cell.classList.add("capture");
      }

      const piece = pieces[square];
      if (piece) {
        cell.textContent = GLYPHS[piece.type];
        cell.classList.add(piece.color === "white" ? "white-piece" : "black-piece");
      }

      cell.addEventListener("click", () => onCellClick(square));
      board.appendChild(cell);
    }
  }

  // ходы по парам: "1. e4 e5"
  const history = document.getElementById("history");
  history.innerHTML = "";
  for (let i = 0; i < state.history.length; i += 2) {
    const item = document.createElement("li");
    item.textContent = state.history.slice(i, i + 2).join(" ");
    history.appendChild(item);
  }
}

async function onCellClick(square) {
  if (state.game_over) return;
  showError("");
  try {
    if (selected && legal.moves.includes(square)) {
      let promotion = null;
      if (legal.promotions.includes(square)) {
        promotion = await askPromotion();
        if (!promotion) return;                  // окно закрыли: ход не делаем
      }
      const data = await api(`/api/games/${gameId}/move`, {
        method: "POST",
        body: JSON.stringify({ source: selected, destination: square, promotion }),
      });
      setState(data);
      return;
    }

    const piece = state.pieces.find((p) => p.square === square);
    if (piece && piece.color === state.turn) {
      selected = square;
      legal = await api(`/api/games/${gameId}/moves?square=${square}`);
    } else {
      selected = null;
      legal = NO_MOVES;
    }
    render();
  } catch (e) {
    showError(e.message);
  }
}

function askPromotion() {
  return new Promise((resolve) => {
    const overlay = document.getElementById("promotion");
    overlay.hidden = false;
    const done = (value) => {
      overlay.hidden = true;
      overlay.onclick = null;
      resolve(value);
    };
    overlay.onclick = (event) => {
      if (event.target === overlay) done(null);
      else if (event.target.dataset.piece) done(event.target.dataset.piece);
    };
  });
}

document.getElementById("new-game").addEventListener("click", () => newGame().catch((e) => showError(e.message)));

(async function init() {
  const saved = loadId();
  if (saved) {
    try {
      gameId = saved;
      setState(await api(`/api/games/${gameId}`));
      return;
    } catch (_) { /* партии нет (сервер перезапускался) */ }
  }
  await newGame();
})();