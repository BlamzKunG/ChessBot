// ==UserScript==
// @name         Chess.com Coach Highlights Top5 (show source+dest)
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  Highlight top-5 engine moves as bordered squares (show source + dest) with center score on live Chess.com board.
// @match        https://www.chess.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    const WS_URL = 'ws://localhost:8765';
    const SEND_INTERVAL_MS = 300;
    const MAX_PVS = 5;
    const RANK_COLORS = ['#00FF00', '#7FFF00', '#FFFF00', '#FFA500', '#FF0000'];

    // ----- WebSocket -----
    let ws = null;
    function connectWS() {
        if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
        ws = new WebSocket(WS_URL);
        ws.onopen = () => console.log('[Coach] WS connected');
        ws.onerror = (e) => console.error('[Coach] WS error', e);
        ws.onclose = () => { console.log('[Coach] WS closed, retry in 1s'); setTimeout(connectWS, 1000); };
        ws.onmessage = (ev) => {
            try {
                const data = JSON.parse(ev.data);
                if (data.status === 'reset') return;
                const pvs = data.pvs || data.moves || [];
                console.log('[Coach] analysis received pvs count=', pvs.length, pvs);
                if (pvs && pvs.length > 0) drawHighlightsOnLiveBoard(pvs);
                else clearAllOverlays();
            } catch (e) {
                console.error('[Coach] invalid analysis reply', e, ev.data);
            }
        };
    }
    connectWS();

    // ----- Live board detection -----
    function getLiveBoardElement() {
        const container = document.querySelector('.board-layout-main');
        if (container) {
            const b = container.querySelector('wc-chess-board, .board');
            if (b) return b;
        }
        const candidates = [
            document.querySelector('wc-chess-board#board-play'),
            document.querySelector('wc-chess-board#board-play-computer'),
            document.querySelector('wc-chess-board.board'),
            document.querySelector('wc-chess-board')
        ];
        for (const c of candidates) if (c) return c;
        return null;
    }

    // ----- Move parsing -----
    function cleanMoveText(node) {
        const copy = node.cloneNode(true);
        copy.querySelectorAll('span').forEach(s => s.remove());
        return copy.innerText.trim().replace(/[+#]/g, '').trim();
    }

    function moveNodeToSAN(node) {
        try {
            const moveTextNode = node.querySelector('.node-highlight-content');
            if (!moveTextNode) return null;
            let target = cleanMoveText(moveTextNode);
            if (target === 'O-O' || target === 'O-O-O') return target;
            let piece = 'P';
            const icon = moveTextNode.querySelector('.icon-font-chess');
            if (icon && icon.dataset && icon.dataset.figurine) {
                const figurine = icon.dataset.figurine;
                if (figurine === 'N') piece = 'N';
                else if (figurine === 'B') piece = 'B';
                else if (figurine === 'R') piece = 'R';
                else if (figurine === 'Q') piece = 'Q';
                else if (figurine === 'K') piece = 'K';
            }
            if (piece === 'P') return target;
            return piece + target;
        } catch (e) {
            console.error('[Coach] Error parsing move node:', e, node);
            return null;
        }
    }

    function getMovesForLiveGame() {
        const rows = document.querySelectorAll('.main-line-row.move-list-row');
        const moves = [];
        rows.forEach(row => {
            const w = row.querySelector('.white-move');
            const b = row.querySelector('.black-move');
            if (w) {
                const san = moveNodeToSAN(w);
                if (san) moves.push(san);
            }
            if (b) {
                const san = moveNodeToSAN(b);
                if (san) moves.push(san);
            }
        });
        return moves;
    }

    // ----- Flipped detection (robust) -----
    function isBoardFlippedElement(boardEl) {
        if (!boardEl) return false;
        try {
            if (boardEl.hasAttribute && boardEl.hasAttribute('flipped')) return true;
            const att = boardEl.getAttribute && boardEl.getAttribute('flipped');
            if (att === 'true') return true;
        } catch (e) {}
        try {
            if (boardEl.classList && boardEl.classList.contains('flipped')) return true;
        } catch (e) {}
        try {
            const controllers = [
                window.ChessBoardController, window.chessboardController,
                window.__CHESS_BOARD__, window.boardController, window.board
            ];
            for (const ctrl of controllers) {
                if (!ctrl) continue;
                if (ctrl.board && ctrl.board.orientation && String(ctrl.board.orientation) === 'black') return true;
                if (ctrl.orientation && String(ctrl.orientation) === 'black') return true;
            }
        } catch (e) {}
        try {
            const coords = boardEl.querySelectorAll('svg.coordinates text');
            if (coords && coords.length >= 8) {
                for (let i = 0; i < coords.length; i++) {
                    const t = coords[i];
                    if (t && t.textContent && t.textContent.trim() === '1') {
                        const yAttr = t.getAttribute('y');
                        if (yAttr !== null) {
                            const ynum = parseFloat(yAttr);
                            if (!isNaN(ynum)) return ynum < 50;
                        }
                    }
                }
            }
        } catch (e) {}
        return false;
    }

    // ----- Overlay layers: bg (borders) below pieces, fg (labels) above pieces -----
    function ensureOverlayLayers(boardEl) {
        if (!boardEl) return { bg: null, fg: null };
        const firstPiece = boardEl.querySelector('.piece');
        let bg = boardEl.querySelector('svg.coach-overlay-bg');
        if (!bg) {
            bg = document.createElementNS('http://www.w3.org/2000/svg','svg');
            bg.setAttribute('viewBox','0 0 100 100');
            bg.setAttribute('preserveAspectRatio','none');
            bg.classList.add('coach-overlay-bg');
            bg.style.pointerEvents = 'none';
            if (firstPiece && firstPiece.parentNode === boardEl) {
                boardEl.insertBefore(bg, firstPiece);
            } else {
                boardEl.insertBefore(bg, boardEl.firstChild || null);
            }
        }
        let fg = boardEl.querySelector('svg.coach-overlay-fg');
        if (!fg) {
            fg = document.createElementNS('http://www.w3.org/2000/svg','svg');
            fg.setAttribute('viewBox','0 0 100 100');
            fg.setAttribute('preserveAspectRatio','none');
            fg.classList.add('coach-overlay-fg');
            fg.style.pointerEvents = 'none';
            boardEl.appendChild(fg);
        }
        return { bg, fg };
    }

    function clearOverlaySvg(svg) {
        if (!svg) return;
        while (svg.firstChild) svg.removeChild(svg.firstChild);
    }

    function clearAllOverlays() {
        const board = getLiveBoardElement();
        if (!board) return;
        const bg = board.querySelector('svg.coach-overlay-bg');
        const fg = board.querySelector('svg.coach-overlay-fg');
        if (bg) clearOverlaySvg(bg);
        if (fg) clearOverlaySvg(fg);
    }

    // ----- geometry helpers -----
    const SQ = 100 / 8;
    function uciToRect(uciSquare, flipped) {
        const file = uciSquare.charCodeAt(0) - 97;
        const rank = parseInt(uciSquare[1], 10);
        let col, row;
        if (!flipped) {
            col = file;
            row = 8 - rank;
        } else {
            col = 7 - file;
            row = rank - 1;
        }
        const x = col * SQ;
        const y = row * SQ;
        return { x, y, w: SQ, h: SQ, cx: x + SQ/2, cy: y + SQ/2 };
    }

    function colorForIndex(i, n) {
        if (n <= 1) return RANK_COLORS[0];
        const t = i / (n - 1);
        const r = Math.round(255 * t);
        const g = Math.round(255 * (1 - t));
        return `rgb(${r},${g},0)`;
    }

    // ----- draw highlights (bg: rectangles, fg: labels) -----
    function drawHighlightsOnLiveBoard(pvs) {
        const board = getLiveBoardElement();
        if (!board) { console.warn('[Coach] no live board'); return; }
        const layers = ensureOverlayLayers(board);
        if (!layers.bg || !layers.fg) return;

        // normalize entries & dedupe by target square
        const entries = (pvs || []).filter(Boolean).map(e => {
            if (e.move) return e;
            if (e.uci) return { move: e.uci, score_cp: e.score_cp ?? null, mate: e.mate ?? null };
            return null;
        }).filter(Boolean);

        const seenTo = new Set();
        const unique = [];
        for (let i = 0; i < entries.length && unique.length < MAX_PVS; i++) {
            const en = entries[i];
            if (!en || !en.move || en.move.length < 4) continue;
            const to = en.move.slice(2,4);
            if (seenTo.has(to)) continue;
            seenTo.add(to);
            unique.push(en);
        }

        // clear
        clearOverlaySvg(layers.bg);
        clearOverlaySvg(layers.fg);

        const flipped = isBoardFlippedElement(board);
        const n = Math.min(unique.length, MAX_PVS);
        if (n === 0) return;

        for (let i = 0; i < n; i++) {
            const entry = unique[i];
            const uci = entry.move;
            const from = uci.slice(0,2);
            const to = uci.slice(2,4);
            const rectFrom = uciToRect(from, flipped);
            const rectTo = uciToRect(to, flipped);
            const color = colorForIndex(i, n);

            // draw SOURCE border (dashed, thinner) on bg layer so pieces still visible
            const borderFrom = document.createElementNS('http://www.w3.org/2000/svg','rect');
            borderFrom.setAttribute('x', rectFrom.x.toString());
            borderFrom.setAttribute('y', rectFrom.y.toString());
            borderFrom.setAttribute('width', rectFrom.w.toString());
            borderFrom.setAttribute('height', rectFrom.h.toString());
            borderFrom.setAttribute('fill', 'none');
            borderFrom.setAttribute('stroke', color);
            borderFrom.setAttribute('stroke-width', (0.45 + (0.25 - i * 0.03)).toFixed(2));
            borderFrom.setAttribute('rx', '0.4');
            borderFrom.setAttribute('ry', '0.4');
            borderFrom.setAttribute('opacity', '0.9');
            borderFrom.setAttribute('stroke-dasharray', '2,2');
            layers.bg.appendChild(borderFrom);

            // draw DEST border (solid)
            const borderTo = document.createElementNS('http://www.w3.org/2000/svg','rect');
            borderTo.setAttribute('x', rectTo.x.toString());
            borderTo.setAttribute('y', rectTo.y.toString());
            borderTo.setAttribute('width', rectTo.w.toString());
            borderTo.setAttribute('height', rectTo.h.toString());
            borderTo.setAttribute('fill', 'none');
            borderTo.setAttribute('stroke', color);
            borderTo.setAttribute('stroke-width', '0.4');
            borderTo.setAttribute('rx', '0.4');
            borderTo.setAttribute('ry', '0.4');
            borderTo.setAttribute('opacity', '0.95');
            layers.bg.appendChild(borderTo);

            // LABEL (fg) centered on destination
            const txt = document.createElementNS('http://www.w3.org/2000/svg','text');
            txt.setAttribute('x', rectTo.cx.toString());
            txt.setAttribute('y', rectTo.cy.toString());
            txt.setAttribute('fill', '#ffffff');
            txt.setAttribute('font-size', '3.6');
            txt.setAttribute('font-family', 'Segoe UI, Arial');
            txt.setAttribute('font-weight', '700');
            txt.setAttribute('text-anchor', 'middle');
            txt.setAttribute('dominant-baseline', 'central');

            let label = '';
            if (entry.mate !== null && entry.mate !== undefined) label = '#'+entry.mate;
            else if (entry.score_cp !== null && entry.score_cp !== undefined) label = (entry.score_cp / 100).toFixed(2);
            txt.textContent = label;
            txt.setAttribute('style', 'stroke:black; stroke-width:0.4; paint-order:stroke;');
            layers.fg.appendChild(txt);
        }
    }

    // ----- periodic send (only for live board) -----
    let lastSentMovesJson = null;
    setInterval(() => {
        const board = getLiveBoardElement();
        if (!board) return;
        const moves = getMovesForLiveGame();
        const j = JSON.stringify(moves);
        if (j === lastSentMovesJson) return;
        lastSentMovesJson = j;
        if (ws && ws.readyState === WebSocket.OPEN) {
            try { ws.send(j); } catch (e) { console.error('[Coach] WS send error', e); }
        } else {
            if (!ws || ws.readyState === WebSocket.CLOSED) connectWS();
        }
    }, SEND_INTERVAL_MS);

    // observe DOM to reattach overlays if board replaced
    const observer = new MutationObserver(() => {
        const board = getLiveBoardElement();
        if (!board) return;
        ensureOverlayLayers(board);
    });
    observer.observe(document.body, { childList: true, subtree: true });

    console.log('[Coach] Live-board highlights (source+dest) loaded');
})();
