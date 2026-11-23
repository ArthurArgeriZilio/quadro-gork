#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quadro - servidor local (somente biblioteca padrão do Python 3).

- Escuta APENAS em 127.0.0.1 (nunca 0.0.0.0).
- Serve index.html e uma API JSON em /api/...
- Persiste em quadro.json (escrita atômica) com backup em quadro.bak.json.
- Anexos de tarefas e post-its ficam na pasta anexos/ (só nesta máquina).
- Recusa requisições cujo Host não seja 127.0.0.1/localhost (anti DNS rebinding).

Uso:  python servidor.py            (porta 8765)
      python servidor.py --abrir   (abre o navegador depois de subir)
      python servidor.py 9000       (outra porta)
Parar: Ctrl+C ou fechar a janela.
"""
import copy
import hashlib
import json
import mimetypes
import os
import re
import secrets
import shutil
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "quadro.json")
BACKUP = os.path.join(BASE, "quadro.bak.json")
INDEX = os.path.join(BASE, "index.html")
ATTACH_DIR = os.path.join(BASE, "anexos")
HOST = "127.0.0.1"
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OPEN_BROWSER = "--abrir" in sys.argv
PORT = int(ARGS[0]) if ARGS else int(os.environ.get("QUADRO_PORT", "8765"))
MAX_BODY = 8 * 1024 * 1024
MAX_ATTACH = 50 * 1024 * 1024
MAX_ATTS = 20
LOCK = threading.Lock()
SAFE_FILE = re.compile(r"^a[0-9a-f]{16}_[A-Za-z0-9._\-]{1,80}$")
INLINE_MIME = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
    "image/x-icon", "image/vnd.microsoft.icon", "application/pdf",
}
FORCE_DOWNLOAD = {
    "text/html", "application/xhtml+xml", "image/svg+xml", "text/xml",
    "application/xml", "application/javascript", "text/javascript",
    "application/x-javascript",
}
MIME_BY_EXT = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    ".ico": "image/x-icon", ".pdf": "application/pdf", ".txt": "text/plain",
    ".md": "text/plain", ".csv": "text/csv", ".html": "text/html",
    ".htm": "text/html", ".svg": "image/svg+xml", ".json": "application/json",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".zip": "application/zip", ".mp3": "audio/mpeg", ".mp4": "video/mp4",
    ".wav": "audio/wav", ".odt": "application/vnd.oasis.opendocument.text",
}

# padrões 1-bit (novos) + nomes antigos de cor, aceitos por compatibilidade
PATTERNS = {"branco", "preto", "pontilhado", "denso", "listras"}
COLORS = PATTERNS | {"amarelo", "rosa", "verde", "azul", "laranja", "roxo", "vermelho", "cinza"}
URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.I)
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


class BadRequest(Exception):
    pass


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_id(prefix):
    return prefix + "_" + secrets.token_hex(5)


def empty_board():
    return {"version": 1, "updated_at": now(), "tasks": [], "notes": [], "strokes": [], "links": []}


# ---------------------------------------------------------------- validação
def v_str(d, key, maxlen, default=None, required=False):
    if key not in d or d[key] is None:
        if required:
            raise BadRequest("campo obrigatório: " + key)
        return default
    val = d[key]
    if not isinstance(val, str):
        raise BadRequest(key + " deve ser texto")
    if len(val) > maxlen:
        raise BadRequest(key + " muito longo (máx %d)" % maxlen)
    return val


def v_num(d, key, default=None):
    if key not in d or d[key] is None:
        return default
    val = d[key]
    if isinstance(val, bool) or not isinstance(val, (int, float)) or val != val or abs(val) > 1e7:
        raise BadRequest(key + " deve ser número")
    return round(float(val), 1)


def v_color(d, key, default):
    val = d.get(key)
    if val is None:
        return default
    if not isinstance(val, str) or not (val in COLORS or HEX.match(val)):
        raise BadRequest("cor inválida: use um nome (%s) ou #rrggbb" % ", ".join(sorted(COLORS)))
    return val


def v_url(d, key, default):
    if key not in d or d[key] is None:
        return default
    val = d[key]
    if not isinstance(val, str) or len(val) > 2000:
        raise BadRequest(key + " deve ser texto (até 2000)")
    val = val.strip()
    if val and not URL_RE.match(val):
        raise BadRequest(key + " deve começar com http:// ou https://")
    return val


def v_bool(d, key, default=None):
    if key not in d or d[key] is None:
        return default
    if not isinstance(d[key], bool):
        raise BadRequest(key + " deve ser true/false")
    return d[key]


HIST_AT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")
MAX_HIST = 200


def clean_history(v, old=None):
    """Lista {at, text}. Ausente vira a anterior (ou []). Entrada inválida é ignorada."""
    if v is None:
        v = old if isinstance(old, list) else []
    if not isinstance(v, list):
        raise BadRequest("history deve ser uma lista")
    if len(v) > 500:
        raise BadRequest("history muito longa")
    out, seen = [], set()
    for e in v:
        if not isinstance(e, dict):
            continue
        at, text = e.get("at"), e.get("text")
        if not isinstance(at, str) or not isinstance(text, str) or not HIST_AT.match(at):
            continue
        text = text.replace("\r", "").rstrip("\n")[:5000]
        if not text.strip():
            continue
        key = at + "\n" + text
        if key in seen:
            continue
        seen.add(key)
        out.append({"at": at, "text": text})
    out.sort(key=lambda e: e["at"])
    if len(out) > MAX_HIST:
        out = out[-MAX_HIST:]
    return out


MAX_SUBS = 100


def clean_subtasks(v, old=None):
    """Lista {id, text, done, at}. Ausente mantém a anterior (ou []). Id repetido: fica o último texto/done."""
    if v is None:
        v = old if isinstance(old, list) else []
    if not isinstance(v, list):
        raise BadRequest("subtasks deve ser uma lista")
    if len(v) > 300:
        raise BadRequest("subtasks muito longa")
    order, by_id = [], {}
    for e in v:
        if not isinstance(e, dict):
            continue
        text = e.get("text")
        if not isinstance(text, str):
            continue
        text = text.replace("\r", "").strip()[:500]
        if not text:
            continue
        sid = e.get("id")
        if not isinstance(sid, str) or not (0 < len(sid) <= 40):
            sid = new_id("st")
        done = e.get("done") is True
        at = e.get("at")
        if not isinstance(at, str) or not HIST_AT.match(at):
            at = now()
        if sid not in by_id:
            if len(order) >= MAX_SUBS:
                continue
            order.append(sid)
        by_id[sid] = {"id": sid, "text": text, "done": done, "at": at}
    return [by_id[i] for i in order]


def clean_task(d, old=None):
    if not isinstance(d, dict):
        raise BadRequest("tarefa deve ser um objeto")
    o = old or {}
    t = {
        "id": o.get("id") or (d.get("id") if isinstance(d.get("id"), str) and 0 < len(d["id"]) <= 40 else None) or new_id("t"),
        "title": v_str(d, "title", 500, o.get("title"), required=not old),
        "notes": v_str(d, "notes", 5000, o.get("notes", "")),
        "x": v_num(d, "x", o.get("x", 100.0)),
        "y": v_num(d, "y", o.get("y", 100.0)),
        "color": v_color(d, "color", o.get("color", "branco")),
        "done": v_bool(d, "done", o.get("done", False)),
        "column": v_str(d, "column", 60, o.get("column", "")),
        "url": v_url(d, "url", o.get("url", "")),
        "log": v_str(d, "log", 5000, o.get("log", "")),
        "history": clean_history(d["history"] if "history" in d else None, o.get("history", [])),
        "subtasks": clean_subtasks(d["subtasks"] if "subtasks" in d else None, o.get("subtasks", [])),
        "attachments": clean_attachments(d["attachments"] if "attachments" in d else None, o.get("attachments", [])),
        "created_at": o.get("created_at") or v_str(d, "created_at", 40, None) or now(),
        "updated_at": now(),
    }
    return t


def clean_note(d, old=None):
    if not isinstance(d, dict):
        raise BadRequest("nota deve ser um objeto")
    o = old or {}
    rot = v_num(d, "rotation", o.get("rotation"))
    if rot is None:
        rot = round((secrets.randbelow(61) - 30) / 10.0, 1)
    n = {
        "id": o.get("id") or (d.get("id") if isinstance(d.get("id"), str) and 0 < len(d["id"]) <= 40 else None) or new_id("n"),
        "text": v_str(d, "text", 5000, o.get("text", "")),
        "x": v_num(d, "x", o.get("x", 400.0)),
        "y": v_num(d, "y", o.get("y", 100.0)),
        "color": v_color(d, "color", o.get("color", "pontilhado")),
        "rotation": max(-15.0, min(15.0, rot)),
        "url": v_url(d, "url", o.get("url", "")),
        "attachments": clean_attachments(d["attachments"] if "attachments" in d else None, o.get("attachments", [])),
        "created_at": o.get("created_at") or v_str(d, "created_at", 40, None) or now(),
        "updated_at": now(),
    }
    return n


def clean_stroke(d):
    if not isinstance(d, dict):
        raise BadRequest("traço deve ser um objeto")
    pts = d.get("points")
    if not isinstance(pts, list) or not pts or len(pts) > 20000:
        raise BadRequest("points deve ser uma lista [[x,y], ...] com 1 a 20000 pontos")
    clean = []
    for p in pts:
        if (not isinstance(p, list) or len(p) != 2 or
                any(isinstance(c, bool) or not isinstance(c, (int, float)) or c != c or abs(c) > 1e7 for c in p)):
            raise BadRequest("ponto inválido em points")
        clean.append([round(float(p[0]), 1), round(float(p[1]), 1)])
    mode = d.get("mode", "pen")
    if mode not in ("pen", "erase"):
        raise BadRequest("mode deve ser 'pen' ou 'erase'")
    width = v_num(d, "width", 3.0)
    if not 0.5 <= width <= 100:
        raise BadRequest("width fora do intervalo 0.5–100")
    return {
        "id": d.get("id") if isinstance(d.get("id"), str) and 0 < len(d["id"]) <= 40 else new_id("s"),
        "color": v_color(d, "color", "preto"),
        "width": width,
        "mode": mode,
        "points": clean,
        "created_at": now(),
    }


def item_ids(b):
    return {x.get("id") for k in ("tasks", "notes", "strokes") for x in b.get(k, []) if isinstance(x, dict)}


def clean_link(d, ids, old=None):
    if not isinstance(d, dict):
        raise BadRequest("link deve ser um objeto")
    o = old or {}
    f = v_str(d, "from", 40, o.get("from"), required=not old)
    t = v_str(d, "to", 40, o.get("to"), required=not old)
    if f not in ids or t not in ids:
        raise BadRequest("from/to devem ser ids existentes de tarefa, nota ou traço")
    if f == t:
        raise BadRequest("from e to devem ser itens diferentes")
    out = {
        "id": o.get("id") or (d.get("id") if isinstance(d.get("id"), str) and 0 < len(d["id"]) <= 40 else None) or new_id("l"),
        "from": f,
        "to": t,
        "label": v_str(d, "label", 200, o.get("label", "")),
        "created_at": o.get("created_at") or v_str(d, "created_at", 40, None) or now(),
        "updated_at": now(),
    }
    color = v_color(d, "color", o.get("color") if o else None)
    if color:
        out["color"] = color
    return out


def prune_links(b):
    """Remove links cujo item de origem ou destino não existe mais. Retorna quantos saíram."""
    ids = item_ids(b)
    before = len(b["links"])
    b["links"] = [l for l in b["links"] if isinstance(l, dict) and l.get("from") in ids and l.get("to") in ids]
    return before - len(b["links"])



# ---------------------------------------------------------------- anexos
def sanitize_filename(name):
    if not isinstance(name, str):
        name = ""
    name = name.replace("\\", "/").replace("\x00", "")
    name = os.path.basename(name).split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._\-]+", "_", name)
    name = name.strip("._") or "arquivo"
    if name in (".", ".."):
        name = "arquivo"
    return name[:80]


def stored_name(orig):
    return "a" + secrets.token_hex(8) + "_" + sanitize_filename(orig)


def attach_path(fn):
    """Resolve um nome de arquivo dentro de anexos/. None se for inseguro."""
    fn = os.path.basename(str(fn or ""))
    if not SAFE_FILE.match(fn):
        return None
    root = os.path.realpath(ATTACH_DIR)
    path = os.path.realpath(os.path.join(root, fn))
    try:
        if os.path.commonpath([root, path]) != root:
            return None
    except ValueError:
        return None
    return path


def guess_mime(name, hinted=None):
    hinted = (hinted or "").split(";")[0].strip().lower()
    if hinted in ("", "application/octet-stream", "application/json"):
        hinted = ""
    ext = os.path.splitext(name or "")[1].lower()
    guessed = MIME_BY_EXT.get(ext) or (mimetypes.guess_type(name or "")[0] or "")
    guessed = (guessed or "").split(";")[0].strip().lower()
    # extensão perigosa (html/svg/js) ganha do Content-Type informado
    if guessed in FORCE_DOWNLOAD:
        return guessed
    return hinted or guessed or "application/octet-stream"


def referenced_files(b):
    used = set()
    for k in ("tasks", "notes"):
        for it in b.get(k) or []:
            if not isinstance(it, dict):
                continue
            for a in it.get("attachments") or []:
                if isinstance(a, dict) and isinstance(a.get("file"), str):
                    used.add(os.path.basename(a["file"]))
    return used


def cleanup_orphans():
    """Apaga em anexos/ só arquivos gerados por nós que nenhum item cita."""
    os.makedirs(ATTACH_DIR, exist_ok=True)
    b = load()
    used = referenced_files(b)
    n = 0
    for fn in os.listdir(ATTACH_DIR):
        if not SAFE_FILE.match(fn) or fn in used:
            continue
        path = os.path.join(ATTACH_DIR, fn)
        if os.path.isfile(path):
            try:
                os.remove(path)
                n += 1
            except OSError:
                pass
    return n


def clean_attachments(v, old=None):
    if v is None:
        v = old if old is not None else []
    if not isinstance(v, list):
        raise BadRequest("attachments deve ser uma lista")
    out, seen = [], set()
    for a in v:
        if len(out) >= MAX_ATTS:
            break
        if not isinstance(a, dict):
            continue
        fn = a.get("file")
        if not isinstance(fn, str):
            continue
        fn = os.path.basename(fn)
        if not SAFE_FILE.match(fn) or fn in seen:
            continue
        seen.add(fn)
        aid = a.get("id") if isinstance(a.get("id"), str) and 0 < len(a["id"]) <= 40 else new_id("a")
        name = a.get("name") if isinstance(a.get("name"), str) else ""
        name = os.path.basename(name.replace("\\", "/"))[:200].strip() or "arquivo"
        mime = a.get("mime") if isinstance(a.get("mime"), str) else ""
        mime = (mime.split(";")[0].strip().lower() or "application/octet-stream")[:100]
        size = a.get("size")
        if isinstance(size, bool) or not isinstance(size, (int, float)) or size < 0 or size > MAX_ATTACH:
            size = 0
        else:
            size = int(size)
        ca = a.get("created_at") if isinstance(a.get("created_at"), str) and len(a.get("created_at") or "") <= 40 else now()
        out.append({"id": aid, "name": name, "file": fn, "mime": mime, "size": size, "created_at": ca})
    return out


# ---------------------------------------------------------------- arquivo
_CACHE_MISS = object()
_BOARD_CACHE = {"key": _CACHE_MISS, "board": None, "rev": None, "body": None}


def _data_key():
    try:
        st = os.stat(DATA)
    except OSError:
        return None
    return (getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9)), st.st_size)


def _read_disk():
    if not os.path.exists(DATA):
        b = empty_board()
    else:
        try:
            with open(DATA, "r", encoding="utf-8") as f:
                b = json.load(f)
        except (ValueError, OSError):
            try:
                with open(BACKUP, "r", encoding="utf-8") as f:
                    b = json.load(f)
            except (ValueError, OSError):
                b = empty_board()
    if not isinstance(b, dict):
        b = empty_board()
    for k in ("tasks", "notes", "strokes", "links"):
        if not isinstance(b.get(k), list):
            b[k] = []
    b.setdefault("version", 1)
    b.pop("rev", None)
    return b


def _remember(board, key):
    rev = rev_of(board)
    payload = dict(board)
    payload["rev"] = rev
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    _BOARD_CACHE.update(key=key, board=board, rev=rev, body=body)
    return rev, body


def ensure_board():
    key = _data_key()
    c = _BOARD_CACHE
    if c["body"] is not None and c["key"] == key:
        return c["board"], c["rev"], c["body"]
    _remember(_read_disk(), key)
    c = _BOARD_CACHE
    return c["board"], c["rev"], c["body"]


def load():
    board, _rev, _body = ensure_board()
    return copy.deepcopy(board)


def save(b):
    b["updated_at"] = now()
    b.pop("rev", None)
    tmp = DATA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(b, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    if os.path.exists(DATA):
        try:
            shutil.copy2(DATA, BACKUP)
        except OSError:
            pass
    os.replace(tmp, DATA)
    _remember(b, _data_key())


def rev_of(b):
    c = {k: b.get(k, []) for k in ("tasks", "notes", "strokes", "links")}
    return hashlib.sha1(json.dumps(c, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def with_rev(b):
    out = dict(b)
    out["rev"] = rev_of(b)
    return out


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "Quadro/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stdout.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    # --- utilidades
    def send_json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_bytes(code, data)

    def send_bytes(self, code, data, etag=None):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if etag:
            self.send_header("ETag", '"' + etag + '"')
        self.end_headers()
        if code != 304 and data:
            self.wfile.write(data)

    def etag_matches(self, rev):
        header = self.headers.get("If-None-Match")
        if not header or not rev:
            return False
        want = '"' + rev + '"'
        for part in header.split(","):
            tag = part.strip()
            if tag.startswith("W/"):
                tag = tag[2:].strip()
            if tag == want or tag == rev:
                return True
        return False

    def error(self, code, msg):
        self.send_json(code, {"erro": msg})

    def host_ok(self):
        host = (self.headers.get("Host") or "").strip().lower()
        if not host:
            return False
        name = host.rsplit(":", 1)[0] if not host.startswith("[") else host
        if name not in ALLOWED_HOSTS:
            return False
        origin = self.headers.get("Origin")
        if origin and origin != "null":
            m = re.match(r"^https?://([^/:]+)(:\d+)?$", origin.lower())
            if not m or m.group(1) not in ALLOWED_HOSTS:
                return False
        return True

    def query(self):
        q = parse_qs(urlparse(self.path).query)
        return {k: (v[0] if v else "") for k, v in q.items()}

    def read_raw(self, limit):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise BadRequest("Content-Length inválido")
        if n <= 0:
            raise BadRequest("arquivo vazio")
        if n > limit:
            raise BadRequest("arquivo grande demais (máx. 50 MB)")
        data = self.rfile.read(n) if n else b""
        if len(data) != n:
            raise BadRequest("arquivo incompleto")
        return data

    def serve_attachment(self, fn):
        path = attach_path(unquote(fn))
        if not path or not os.path.isfile(path):
            return self.error(404, "arquivo não encontrado")
        mime, name = None, os.path.basename(unquote(fn))
        with LOCK:
            b = load()
            for k in ("tasks", "notes"):
                for it in b[k]:
                    for a in it.get("attachments") or []:
                        if isinstance(a, dict) and a.get("file") == os.path.basename(path):
                            mime = a.get("mime")
                            name = a.get("name") or name
                            break
        mime = guess_mime(name, mime)
        force = mime in FORCE_DOWNLOAD or mime.endswith("+xml") and "svg" in mime
        inline = (not force) and mime in INLINE_MIME
        out_mime = "application/octet-stream" if force else (mime or "application/octet-stream")
        ascii_name = re.sub(r"[^\w.\-]+", "_", name)[:80] or "arquivo"
        cd = "%s; filename=\"%s\"; filename*=UTF-8''%s" % ("inline" if inline else "attachment", ascii_name, quote(name))
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", out_mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", cd)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "private, no-store")
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise BadRequest("Content-Length inválido")
        if n > MAX_BODY:
            raise BadRequest("corpo grande demais")
        raw = self.rfile.read(n) if n else b""
        if not raw.strip():
            raise BadRequest("corpo JSON vazio")
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise BadRequest("JSON inválido")

    def dispatch(self, method):
        if not self.host_ok():
            # lê e descarta o corpo para manter a conexão consistente
            self.close_connection = True
            return self.error(403, "Host não permitido (use 127.0.0.1 ou localhost)")
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        try:
            if path in ("/", "/index.html") and method == "GET":
                return self.serve_index()
            if path.startswith("/api/"):
                return self.api(method, path[5:].split("/"))
            return self.error(404, "não encontrado")
        except BadRequest as e:
            return self.error(400, str(e))
        except Exception as e:  # nunca derrubar o servidor
            self.log_message("ERRO: %r", e)
            return self.error(500, "erro interno")

    def do_GET(self): self.dispatch("GET")
    def do_POST(self): self.dispatch("POST")
    def do_PUT(self): self.dispatch("PUT")
    def do_PATCH(self): self.dispatch("PATCH")
    def do_DELETE(self): self.dispatch("DELETE")

    def serve_index(self):
        with open(INDEX, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
                         "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    # --- API
    def api(self, method, parts):
        res = parts[0]
        item_id = parts[1] if len(parts) > 1 else None
        if len(parts) > 2:
            return self.error(404, "rota não encontrada")

        if res == "board" and item_id is None:
            if method == "GET":
                with LOCK:
                    _board, rev, body = ensure_board()
                    if self.etag_matches(rev):
                        return self.send_bytes(304, b"", rev)
                    return self.send_bytes(200, body, rev)
            if method == "PUT":
                d = self.body()
                if not isinstance(d, dict):
                    raise BadRequest("esperado um objeto")
                b = d.get("board", d)
                if not isinstance(b, dict):
                    raise BadRequest("board deve ser um objeto")
                with LOCK:
                    _board, rev_now, body_now = ensure_board()
                    base = d.get("rev")
                    if base is not None and base != rev_now:
                        raw = b'{"erro":"quadro mudou, recarregue","board":' + body_now + b"}"
                        return self.send_bytes(409, raw, rev_now)
                    new = {"version": 1}
                    new["tasks"] = [self._keep(clean_task(x, None), x) for x in self._list(b, "tasks")]
                    new["notes"] = [self._keep(clean_note(x, None), x) for x in self._list(b, "notes")]
                    new["strokes"] = [clean_stroke(x) for x in self._list(b, "strokes")]
                    self._dedupe(new)
                    ids = item_ids(new)
                    old_links = {x.get("id"): x for x in _board.get("links", []) if isinstance(x, dict)}
                    links = []
                    for x in self._list(b, "links"):
                        if isinstance(x, dict) and x.get("from") in ids and x.get("to") in ids and x.get("from") != x.get("to"):
                            links.append(self._keep(clean_link(x, ids, old_links.get(x.get("id"))), x))
                    new["links"] = links
                    self._dedupe(new)
                    save(new)
                    return self.send_bytes(200, _BOARD_CACHE["body"], _BOARD_CACHE["rev"])
            return self.error(405, "método não permitido")

        coll = {"tasks": ("tasks", clean_task), "notes": ("notes", clean_note)}.get(res)
        if coll:
            key, cleaner = coll
            if item_id is None:
                if method == "GET":
                    with LOCK:
                        return self.send_json(200, load()[key])
                if method == "POST":
                    d = self.body()
                    if isinstance(d, dict):
                        d = dict(d)
                        d.pop("id", None)
                    item = cleaner(d)
                    with LOCK:
                        b = load()
                        b[key].append(item)
                        save(b)
                    return self.send_json(201, item)
                return self.error(405, "método não permitido")
            with LOCK:
                b = load()
                idx = next((i for i, x in enumerate(b[key]) if x.get("id") == item_id), None)
                if idx is None:
                    return self.error(404, "id não encontrado: " + item_id)
                if method == "GET":
                    return self.send_json(200, b[key][idx])
                if method == "PATCH":
                    d = self.body()
                    if not isinstance(d, dict):
                        raise BadRequest("esperado um objeto")
                    d = dict(d)
                    d.pop("id", None)
                    d.pop("created_at", None)
                    item = cleaner(d, b[key][idx])
                    b[key][idx] = item
                    save(b)
                    return self.send_json(200, item)
                if method == "DELETE":
                    gone = b[key].pop(idx)
                    n = prune_links(b)
                    save(b)
                    return self.send_json(200, {"ok": True, "removido": gone["id"], "links_removidos": n})
            return self.error(405, "método não permitido")

        if res == "strokes" and item_id is None:
            if method == "POST":
                d = self.body()
                items = d if isinstance(d, list) else [d]
                strokes = [clean_stroke(x) for x in items]
                with LOCK:
                    b = load()
                    b["strokes"].extend(strokes)
                    save(b)
                return self.send_json(201, strokes if isinstance(d, list) else strokes[0])
            if method == "GET":
                with LOCK:
                    return self.send_json(200, load()["strokes"])
            if method == "DELETE":
                with LOCK:
                    b = load()
                    n = len(b["strokes"])
                    b["strokes"] = []
                    nl = prune_links(b)
                    save(b)
                return self.send_json(200, {"ok": True, "removidos": n, "links_removidos": nl})
            return self.error(405, "método não permitido")

        if res == "strokes" and item_id is not None:
            if method != "DELETE":
                return self.error(405, "método não permitido")
            with LOCK:
                b = load()
                before = len(b["strokes"])
                b["strokes"] = [s for s in b["strokes"] if s.get("id") != item_id]
                if len(b["strokes"]) == before:
                    return self.error(404, "id não encontrado: " + item_id)
                nl = prune_links(b)
                save(b)
            return self.send_json(200, {"ok": True, "removido": item_id, "links_removidos": nl})

        if res == "links":
            with LOCK:
                b = load()
                if item_id is None:
                    if method == "GET":
                        return self.send_json(200, b["links"])
                    if method == "POST":
                        d = self.body()
                        if isinstance(d, dict):
                            d = dict(d)
                            d.pop("id", None)
                        link = clean_link(d, item_ids(b))
                        b["links"].append(link)
                        save(b)
                        return self.send_json(201, link)
                    return self.error(405, "método não permitido")
                idx = next((i for i, x in enumerate(b["links"]) if x.get("id") == item_id), None)
                if idx is None:
                    return self.error(404, "id não encontrado: " + item_id)
                if method == "GET":
                    return self.send_json(200, b["links"][idx])
                if method == "PATCH":
                    d = self.body()
                    if not isinstance(d, dict):
                        raise BadRequest("esperado um objeto")
                    d = dict(d)
                    d.pop("id", None)
                    d.pop("created_at", None)
                    link = clean_link(d, item_ids(b), b["links"][idx])
                    b["links"][idx] = link
                    save(b)
                    return self.send_json(200, link)
                if method == "DELETE":
                    gone = b["links"].pop(idx)
                    save(b)
                    return self.send_json(200, {"ok": True, "removido": gone["id"]})
            return self.error(405, "método não permitido")

        if res == "attachments":
            return self.api_attachments(method, item_id)

        return self.error(404, "rota não encontrada")

    def api_attachments(self, method, item_id):
        if method == "POST" and item_id is None:
            q = self.query()
            item = (q.get("item") or "").strip()
            name = q.get("name") or self.headers.get("X-Filename") or "arquivo"
            try:
                name = unquote(name)
            except Exception:
                pass
            hinted = (self.headers.get("Content-Type") or "").split(";")[0].strip()
            if hinted.lower().startswith("multipart/"):
                raise BadRequest("envie o arquivo no corpo (raw), com o nome em ?name= ou no cabeçalho X-Filename")
            raw = self.read_raw(MAX_ATTACH)
            mime = guess_mime(name, hinted)
            stored = stored_name(name)
            os.makedirs(ATTACH_DIR, exist_ok=True)
            path = os.path.join(ATTACH_DIR, stored)
            if attach_path(stored) is None:
                raise BadRequest("nome de arquivo inválido")
            tmp = path + ".tmp"
            with open(tmp, "wb") as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
            disp = os.path.basename(name.replace("\\", "/"))[:200].strip() or sanitize_filename(name)
            att = {
                "id": new_id("a"),
                "name": disp,
                "file": stored,
                "mime": mime,
                "size": len(raw),
                "created_at": now(),
            }
            with LOCK:
                b = load()
                found = None
                for k in ("tasks", "notes"):
                    for it in b[k]:
                        if it.get("id") == item:
                            found = it
                            break
                    if found:
                        break
                if not found:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                    return self.error(404, "item não encontrado: " + item)
                atts = list(found.get("attachments") or [])
                if len(atts) >= MAX_ATTS:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                    raise BadRequest("máximo de 20 anexos por item")
                atts.append(att)
                found["attachments"] = atts
                found["updated_at"] = now()
                save(b)
            return self.send_json(201, att)

        if item_id is None:
            return self.error(405, "método não permitido")

        if method == "GET":
            return self.serve_attachment(item_id)

        if method == "DELETE":
            key = unquote(item_id)
            with LOCK:
                b = load()
                found, owner = None, None
                for k in ("tasks", "notes"):
                    for it in b[k]:
                        atts = list(it.get("attachments") or [])
                        keep = []
                        hit = None
                        for a in atts:
                            if not isinstance(a, dict):
                                continue
                            if a.get("id") == key or a.get("file") == os.path.basename(key):
                                hit = a
                            else:
                                keep.append(a)
                        if hit:
                            found, owner = hit, it
                            it["attachments"] = keep
                            it["updated_at"] = now()
                            break
                    if found:
                        break
                if not found:
                    return self.error(404, "anexo não encontrado: " + key)
                save(b)
                fn = found.get("file")
                if fn and fn not in referenced_files(b):
                    path = attach_path(fn)
                    if path and os.path.isfile(path):
                        try:
                            os.remove(path)
                        except OSError:
                            pass
            return self.send_json(200, {"ok": True, "removido": found["id"]})

        return self.error(405, "método não permitido")

    @staticmethod
    def _list(b, key):
        v = b.get(key, [])
        if not isinstance(v, list):
            raise BadRequest(key + " deve ser uma lista")
        return v

    @staticmethod
    def _keep(item, src):
        # no PUT, preserva updated_at enviado se for válido (para não marcar tudo como alterado)
        ua = src.get("updated_at") if isinstance(src, dict) else None
        if isinstance(ua, str) and len(ua) <= 40:
            item["updated_at"] = ua
        return item

    @staticmethod
    def _dedupe(b):
        seen = set()
        for k, p in (("tasks", "t"), ("notes", "n"), ("strokes", "s"), ("links", "l")):
            for x in b.get(k, []):
                if x["id"] in seen:
                    x["id"] = new_id(p)
                seen.add(x["id"])


def main():
    if not os.path.exists(DATA):
        save(empty_board())
    os.makedirs(ATTACH_DIR, exist_ok=True)
    n_orphan = cleanup_orphans()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    httpd.daemon_threads = True
    print("Quadro rodando em http://%s:%d  (só nesta máquina)" % (HOST, PORT))
    print("Dados: %s" % DATA)
    print("Anexos: %s" % ATTACH_DIR)
    if n_orphan:
        print("Anexos órfãos removidos: %d" % n_orphan)
    print("Para parar: Ctrl+C ou feche esta janela.")
    if OPEN_BROWSER:
        import webbrowser
        threading.Timer(0.6, lambda: webbrowser.open("http://%s:%d/" % (HOST, PORT))).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Quadro parado.")


if __name__ == "__main__":
    main()
