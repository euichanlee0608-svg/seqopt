# -*- coding: utf-8 -*-
"""Find user-visible strings that bypass `tr()` — the mechanical half of "both languages, always".

Rules (all on the AST, so comments and docstrings never count):
  · a string given to a call that puts text on screen (`setText`, `QLabel(...)`, `Paragraph(...)`, …)
    or a text-carrying keyword (`label=`, `placeholderText=`, …) must be `tr("…")`
  · a string that reads like prose (two words, 10+ characters) is user text wherever it is
  · a module-level list/tuple of words (ui/, app.py) is a label list
  · strings inside `tr(...)` are the keys; an f-string as the key is an error (the key would vary)
  · `tr()` must not run at import time (module or class level) — the language can change at run time
  · a trailing `# i18n: skip` exempts the line; `# i18n: key` marks literals that are looked up
    with `tr(variable)` later (so the catalog check knows they are keys)

Run it on a file to see what is left:  python -m tests.i18n_scan ui/tab_data.py
"""
from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP, KEY = "i18n: skip", "i18n: key"

# Calls whose string arguments the user reads
TEXT_CALLS = {
    # Qt
    "setText", "setPlainText", "setHtml", "setMarkdown", "setToolTip", "setStatusTip", "setWhatsThis",
    "setTitle", "setWindowTitle", "setPlaceholderText", "setInformativeText", "setDetailedText",
    "setFormat", "setSuffix", "setPrefix", "setTabText", "setTabToolTip", "addTab", "insertTab",
    "addItem", "addItems", "insertItem", "setItemText", "setHorizontalHeaderLabels",
    "setVerticalHeaderLabels", "setHeaderLabels", "setHeaderLabel", "showMessage", "setLabelText",
    "addMenu", "addAction", "setButtonText", "setTextValue",
    "QLabel", "QPushButton", "QCheckBox", "QRadioButton", "QGroupBox", "QAction", "QMenu",
    "QListWidgetItem", "QTableWidgetItem", "QTreeWidgetItem", "QStandardItem", "QMessageBox",
    "critical", "warning", "information", "question", "about",
    "getOpenFileName", "getSaveFileName", "getExistingDirectory", "getText", "getItem",
    # this program's widgets
    "PageHeader", "Section", "link_button", "Advanced", "set_summary", "set_desc", "set_message",
    "MathLabel", "FormulaCard", "_Card", "Topic", "_p", "_ul", "_li", "_table",
    # matplotlib
    "set_title", "set_xlabel", "set_ylabel", "set_zlabel", "suptitle", "text", "annotate",
    "set_label", "set_xticklabels", "set_yticklabels", "figtext",
    # reportlab / csv
    "Paragraph", "drawString", "drawCentredString", "drawRightString", "setAuthor", "setSubject",
    "writerow", "writerows", "drawText",
}
TEXT_KWARGS = {"text", "title", "desc", "summary", "label", "placeholderText", "toolTip", "tooltip",
               "suffix", "prefix", "xlabel", "ylabel", "tags", "headline", "message", "note", "when",
               "hint", "caption", "reason", "body", "name"}
# Calls whose string arguments are never shown: keys, styles, files, logs
QUIET_CALLS = {
    "setObjectName", "setProperty", "property", "setStyleSheet", "set_role", "card", "emit",
    "connect", "open_help", "show_topic", "QSettings", "value", "setValue", "get", "getattr",
    "setattr", "hasattr", "isinstance", "environ", "startswith", "endswith", "split", "rsplit",
    "join", "replace", "strip", "lstrip", "rstrip", "encode", "decode", "mark", "print", "open",
    "read_text", "write_text", "glob", "rglob", "findChild", "findChildren", "setData", "data",
    "Signal", "Slot", "compile", "match", "search", "sub", "findall", "fullmatch", "format_exc",
    "register", "make_acquisition", "make_surrogate", "setCurrentData", "currentData", "warn",
    "simplefilter", "filterwarnings", "catch_warnings", "setdefault", "pop", "keys", "items",
    "setFont", "QFont", "QColor", "QIcon", "QPixmap", "setNamedColor", "setdefault", "Path",
    "exists", "mkdir", "mkstemp", "NamedTemporaryFile", "run", "Popen", "check_output", "strftime",
    "isoformat", "fromisoformat", "getenv", "putenv", "index", "count", "find", "rfind",
    "setShortcut", "QKeySequence", "setAccessibleName", "setWindowIconText", "processEvents",
    "setPixelSize", "setPointSize", "addFont", "applicationFontFamilies", "families", "rc",
    "rcParams", "use", "set_cmap", "get_cmap", "colormaps", "set_prop_cycle", "grid", "tick_params",
    "setDefaultStyleSheet", "setLayoutDirection", "setPen", "setBrush", "elidedText",
    "horizontalAdvance", "boundingRect", "tr", "_pct", "spec",
}
LETTERS = re.compile(r"[A-Za-z]{2,}")
PROSE = re.compile(r"[A-Za-z]{2,}[^\n]*\s[^\n]*[A-Za-z]{2,}")      # two words with whitespace between
PLACEHOLDER = re.compile(r"(?<!\{)\{(\w+)")
PROSE_EXEMPT = {"ui/theme.py", "core/plotstyle.py", "core/fonts.py"}   # style sheets, font names, paths


@dataclass
class Finding:
    file: str
    line: int
    text: str
    why: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: {self.why}: {self.text[:90]!r}"


@dataclass
class Scan:
    keys: list[tuple[str, int, str]]            # (file, line, english) — every tr("…") and # i18n: key literal
    bare: list[Finding]                         # user-visible strings outside tr()
    errors: list[Finding]                       # f-string keys, tr() at import time


def sources() -> list[Path]:
    files = [ROOT / "app.py"] + sorted((ROOT / "ui").rglob("*.py"))
    files += sorted(p for p in (ROOT / "core").rglob("*.py")
                    if "lang" not in p.parts and p.name not in ("i18n.py", "boot.py"))
    return [p for p in files if p.name != "__init__.py"]


def _literal(node) -> str | None:
    """The literal text of a str constant or the literal parts of an f-string."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value for v in node.values if isinstance(v, ast.Constant))
    return None


def _call_name(call: ast.Call) -> str:
    f = call.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def scan_file(path: Path) -> Scan:
    rel = path.relative_to(ROOT).as_posix()
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    tree = ast.parse(src)
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.body and isinstance(node.body[0], ast.Expr) \
                and isinstance(node.body[0].value, ast.Constant) \
                and isinstance(node.body[0].value.value, str):
            docstrings.add(node.body[0].value)

    def marked(node, mark: str) -> bool:
        for ln in range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1):
            if mark in lines[ln - 1]:
                return True
        # a marker on the call/statement line covers its multi-line arguments
        cur = node
        while cur in parents and not isinstance(cur, ast.stmt):
            cur = parents[cur]
        return mark in lines[cur.lineno - 1]

    def enclosing_call(node):
        """(call, keyword name) of the nearest call this string is an argument of, looking through containers."""
        cur, kw = node, None
        while cur in parents:
            p = parents[cur]
            if isinstance(p, ast.keyword):
                kw = p.arg
            elif isinstance(p, ast.Call):
                return p, kw
            elif not isinstance(p, (ast.List, ast.Tuple, ast.BinOp, ast.JoinedStr, ast.FormattedValue,
                                    ast.IfExp, ast.BoolOp, ast.Dict, ast.Set, ast.Starred,
                                    ast.keyword)):
                return None, kw
            cur = p
        return None, kw

    def inside_function(node) -> bool:
        cur = node
        while cur in parents:
            cur = parents[cur]
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                return True
        return False

    keys, bare, errors = [], [], []
    flagged_nodes = set()
    for node in ast.walk(tree):
        text = _literal(node)
        if text is None or node in docstrings or not LETTERS.search(text):
            continue
        if isinstance(parents.get(node), ast.JoinedStr):
            continue                                    # the f-string as a whole is scanned instead
        call, kw = enclosing_call(node)
        name = _call_name(call) if call is not None else ""
        if name == "tr" and call.args and call.args[0] is node:
            if isinstance(node, ast.JoinedStr):
                errors.append(Finding(rel, node.lineno, text, "f-string as a tr() key"))
            else:
                keys.append((rel, node.lineno, text))
                if not inside_function(node):
                    errors.append(Finding(rel, node.lineno, text, "tr() at import time"))
            continue
        if marked(node, KEY):
            if isinstance(node, ast.Constant):
                keys.append((rel, node.lineno, text))
            continue
        if marked(node, SKIP) or name in QUIET_CALLS:
            continue
        if name in TEXT_CALLS or (kw in TEXT_KWARGS and name != ""):
            bare.append(Finding(rel, node.lineno, text, f"text given to {name}()"))
        elif rel not in PROSE_EXEMPT and len(text) >= 10 and PROSE.search(text):
            bare.append(Finding(rel, node.lineno, text, "reads like prose"))
        else:
            continue
        flagged_nodes.add(node)

    # a label list: a module-level list/tuple of words in the UI layer, or any list holding a flagged string
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        strings = [e for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)
                   and LETTERS.search(e.value)]
        if len(strings) < 2:
            continue
        at_module = isinstance(parents.get(node), (ast.Assign, ast.AnnAssign)) \
            and isinstance(parents.get(parents[node]), ast.Module) \
            and (rel.startswith("ui/") or rel == "app.py")
        if any(e in flagged_nodes for e in strings) or (at_module and len(strings) >= 3):
            for e in strings:
                if e in flagged_nodes or e in docstrings or marked(e, SKIP) or marked(e, KEY):
                    continue
                call, _ = enclosing_call(e)
                if call is not None and (_call_name(call) in QUIET_CALLS or _call_name(call) == "tr"):
                    continue
                bare.append(Finding(rel, e.lineno, e.value, "part of a label list"))
                flagged_nodes.add(e)
    return Scan(keys, bare, errors)


def scan_all(files=None) -> Scan:
    total = Scan([], [], [])
    for path in files or sources():
        s = scan_file(path)
        total.keys += s.keys
        total.bare += s.bare
        total.errors += s.errors
    return total


def placeholders(text: str) -> set[str]:
    return set(PLACEHOLDER.findall(text))


if __name__ == "__main__":
    targets = [ROOT / a for a in sys.argv[1:]] or sources()
    result = scan_all(targets)
    for f in result.errors:
        print("ERROR", f)
    for f in result.bare:
        print("BARE ", f)
    print(f"{len(result.keys)} tr() keys · {len(result.bare)} bare strings · {len(result.errors)} errors")
