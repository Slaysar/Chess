const FILES = "abcdefgh";
// U+FE0E заставляет браузер рисовать шахматные значки текстом, а не эмодзи
const GLYPHS = {K: "♚", Q: "♛", R: "♜", B: "♝", N: "♞", P: "♟\uFE0E"};
const NO_MOVES = {moves: [], promotions: []};

let busy = false;
let refreshing = false;
let session = null;     // {id, token, color}: какая это партия и за кого мы в ней играем
let state = null;
let clockAt = 0;        // когда пришло состояние часов (performance.now), от этого момента считаем секунды
let selected = null;
let legal = NO_MOVES;

async function api(path, options = {}) {
    const headers = {"Content-Type": "application/json"};
    if (session) headers["X-Player-Token"] = session.token;   // по токену сервер понимает, кто ходит
    const res = await fetch(path, {...options, headers});
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Ошибка запроса");
    return data;
}

function saveSession() {
    try {
        localStorage.setItem("chess-session", JSON.stringify(session));
    } catch (_) {
    }
}

function loadSession() {
    try {
        return JSON.parse(localStorage.getItem("chess-session"));
    } catch (_) {
        return null;
    }
}

async function newGame() {
    const opponent = document.getElementById("opponent").value;
    const minutes = Number(document.getElementById("minutes").value);
    const data = await api("/api/games", {method: "POST", body: JSON.stringify({opponent, minutes})});
    session = {id: data.id, token: data.token, color: data.color};
    saveSession();
    setState(data);
}

function setState(newState) {
    document.getElementById("opponent").value = newState.opponent;
    state = newState;
    clockAt = performance.now();
    selected = null;
    legal = NO_MOVES;
    render();
}

function showError(message) {
    document.getElementById("error").textContent = message || "";
}

function statusText() {
    if (state.status === "timeout") {
        return `Время вышло. Победили ${state.winner === "white" ? "белые" : "чёрные"}.`;
    }
    if (state.opponent !== "human" && state.turn === "black" && !state.game_over) {
        return "Бот думает…";
    }
    const side = state.turn === "white" ? "белых" : "чёрных";
    switch (state.status) {
        case "checkmate":
            return `Мат. Победили ${state.winner === "white" ? "белые" : "чёрные"}.`;
        case "stalemate":
            return "Пат. Ничья.";
        case "draw":
            return `Ничья: ${state.draw_reason}.`;
        case "check":
            return `Шах. Ход ${side}.` + (state.turn === session.color ? " Ваш ход." : "");
        default:
            return `Ход ${side}.` + (state.turn === session.color ? " Ваш ход." : "");
    }
}

// ---------- часы ----------

function remainingOf(color) {
    const clock = state.clock;
    if (!clock) return null;
    let left = clock[color];
    if (clock.running === color) left -= (performance.now() - clockAt) / 1000;   // между ответами сервера считаем сами
    return Math.max(left, 0);
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}

function renderClocks() {
    if (!state || !session) return;
    const mine = session.color;
    const other = mine === "white" ? "black" : "white";
    for (const [id, color] of [["clock-bottom", mine], ["clock-top", other]]) {
        const left = remainingOf(color);
        const element = document.getElementById(id);
        element.textContent = `${color === "white" ? "Белые" : "Чёрные"}  ${left === null ? "" : formatTime(left)}`;
        element.classList.toggle("active", !!state.clock && state.clock.running === color && !state.game_over);
    }
}

// ---------- доска ----------

function render() {
    document.getElementById("status").textContent = statusText();
    renderClocks();

    const invite = document.getElementById("invite");
    invite.hidden = !state.waiting_for_opponent;
    invite.textContent = `Ссылка для соперника: ${location.origin}/?game=${session.id}`;

    const pieces = Object.fromEntries(state.pieces.map((p) => [p.square, p]));
    const board = document.getElementById("board");
    board.innerHTML = "";

    const flip = session.color === "black";          // свои фигуры всегда внизу
    for (let i = 0; i < 8; i++) {
        const row = flip ? i : 7 - i;
        for (let j = 0; j < 8; j++) {
            const col = flip ? 7 - j : j;
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
    if (state.game_over || busy) return;
    if (state.turn !== session.color) return;        // чужой ход: ничего не выбираем
    showError("");
    try {
        if (selected && legal.moves.includes(square)) {
            let promotion = null;
            if (legal.promotions.includes(square)) {
                promotion = await askPromotion();
                if (!promotion) return;                  // окно закрыли: ход не делаем
            }
            busy = true;
            try {
                const data = await api(`/api/games/${session.id}/move`, {
                    method: "POST",
                    body: JSON.stringify({source: selected, destination: square, promotion}),
                });
                setState(data);        // ход человека виден сразу, статус «Бот думает…»
                await botReply();      // дальше ждём ответ бота
            } finally {
                busy = false;
            }
            return;
        }

        const piece = state.pieces.find((p) => p.square === square);
        if (piece && piece.color === state.turn) {
            selected = square;
            legal = await api(`/api/games/${session.id}/moves?square=${square}`);
        } else {
            selected = null;
            legal = NO_MOVES;
        }
        render();
    } catch (e) {
        showError(e.message);
        render();
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

async function botReply() {
    if (state.opponent === "human" || state.game_over || state.turn !== "black") return;
    setState(await api(`/api/games/${session.id}/bot-move`, {method: "POST"}));
}

// ---------- опрос сервера ----------

async function refresh() {
    if (!session || !state || busy || refreshing) return;
    refreshing = true;
    try {
        const data = await api(`/api/games/${session.id}`);
        const changed = data.history.length !== state.history.length
            || data.status !== state.status
            || data.waiting_for_opponent !== state.waiting_for_opponent;
        if (changed) {
            setState(data);                 // соперник сходил, присоединился или кончилось время
        } else {
            state.clock = data.clock;       // просто сверяем часы с сервером
            clockAt = performance.now();
        }
    } catch (_) {
    } finally {
        refreshing = false;
    }
}

setInterval(() => {
    if (!state) return;
    renderClocks();
    const running = state.clock && state.clock.running;
    if (!state.game_over && running && remainingOf(running) <= 0) refresh();   // спросить у сервера про флажок
}, 250);

setInterval(() => {
    if (state && !state.game_over && state.opponent === "human") refresh();    // ждём ход человека-соперника
}, 1000);

document.getElementById("new-game").addEventListener("click", () => newGame().catch((e) => showError(e.message)));

document.getElementById("opponent").addEventListener("change", () => {
    newGame().catch((e) => showError(e.message));
});


(async function init() {
    const wanted = new URLSearchParams(location.search).get("game");   // ?game=<id> из ссылки соперника
    const saved = loadSession();
    try {
        if (wanted && (!saved || saved.id !== wanted)) {
            const data = await api(`/api/games/${wanted}/join`, {method: "POST"});
            session = {id: wanted, token: data.token, color: data.color};
            saveSession();
            setState(data);
            return;
        }
        if (saved) {
            session = saved;
            setState(await api(`/api/games/${session.id}`));
            busy = true;
            try {
                await botReply();
            } finally {
                busy = false;
            }
            return;
        }
    } catch (e) {
        session = null;                     // партии нет (сервер перезапускался) или место занято
        if (wanted) showError(e.message);
    }
    await newGame();
})();