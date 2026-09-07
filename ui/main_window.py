# -*- coding: utf-8 -*-
"""The main window — the tab container and the status-bar gate badges (spec §4-1).

**The gate badges in the status bar are this program's face.** Whatever tab you
are on, they stay visible.

The state flow (§7-3) runs one way only.
    measurement change → Dataset.build() → diagnostics (fast) → diagnostics (slow) → gate → screens
No partial updates. State mismatch is the most dangerous bug this program can have.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QRect, QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QMainWindow, QMessageBox, QProgressBar, QPushButton,
                               QStackedWidget, QWidget, QVBoxLayout)

from core import i18n
from core.i18n import tr
from core.acquisition import make_acquisition
from core.diagnostics import gate
from core.project import EXT, Project, autosave_path
from .tab_data import DataTab
from .tab_diag import DiagTab
from .tab_recommend import RecommendTab
from .tab_help import HelpTab
from . import theme
from .resources import icon_path
from .start_screen import StartScreen
from .stepper import DIAG, HELP, MODEL, RECOMMEND, REPORT, STEPS, assess
from .tab_setup import SetupTab
from .widgets.nav import NavList
from .worker import DiagnosticsRunner

TABS = ["Setup", "Data", "Diagnose", "Model", "Recommend", "Report", "Help"]   # i18n: key
NAV_NUMBERS = ["1", "2", "3", "4", "5", "6", "?"]
MIN_SIZE = (1024, 660)      # any smaller and the Diagnose screen's two columns collide
AUTOSAVE_MS = 60_000
RECENT_MAX = 6
RECENT_FILE = os.path.join(os.path.expanduser('~'), '.seqopt_recent')


def tab_names() -> list[str]:
    """The seven screens, in rail order. A function, not a constant — `tr()` must not run at import."""
    return [tr(name) for name in TABS]


class _Elided(QLabel):
    """One line of text that shortens itself with "…" rather than being cut off.

    A project name or a file path is as long as the user made it. A plain QLabel keeps its
    full width in the layout and the window simply clips it (`tests/clipcheck.py` calls that
    a finding). This one reports no minimum width, so the header can squeeze it, and it
    re-elides to whatever width it ends up with. The whole text stays in the tooltip.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._full = ""

    def setText(self, text: str) -> None:                    # noqa: N802 (Qt)
        self._full = text
        self.setToolTip(text)
        self._elide()

    def full_text(self) -> str:
        return self._full

    def minimumSizeHint(self) -> QSize:                      # noqa: N802 (Qt)
        return QSize(0, super().minimumSizeHint().height())

    def resizeEvent(self, event) -> None:                    # noqa: N802 (Qt)
        super().resizeEvent(event)
        self._elide()

    def _elide(self) -> None:
        # Font metrics measure the text; the widget also pays for its style sheet's padding and
        # border (the file pill has both). Measure that overhead instead of guessing it —
        # sizeHint minus the width of the text it is currently showing.
        fm = self.fontMetrics()
        chrome = max(0, super().sizeHint().width() - fm.horizontalAdvance(super().text()))
        shown = fm.elidedText(self._full, Qt.ElideRight, max(0, self.width() - chrome))
        if shown != super().text():
            super().setText(shown)


class MainWindow(QMainWindow):
    def __init__(self, project: Project | None = None):
        super().__init__()
        self.project = project or Project()
        self.gate = None
        self.dataset = None
        self._dirty = False
        self._last_fast = None
        self._last_loocv = None
        self._acquisition = make_acquisition()

        # Editing table cells in a row used to run the whole pipeline every time
        # and froze the screen (measured: 972ms per cell, 5.4s for five). Now it
        # waits briefly after the last edit and runs once.
        # Must be created **before** _build() and recompute().
        self._recalc = QTimer(self, singleShot=True)

        self.runner = DiagnosticsRunner(self)
        self.runner.started.connect(self._on_calc_started)
        self.runner.fast_done.connect(self._on_fast)
        self.runner.slow_done.connect(self._on_slow)
        self.runner.failed.connect(self._on_failed)

        self._recalc.timeout.connect(self._do_recompute)
        self._build()
        self._menu()
        self._place_window()
        self.recompute(immediate=True)

        self._autosave = QTimer(self)
        self._autosave.timeout.connect(self._do_autosave)
        self._autosave.start(AUTOSAVE_MS)

    # ── screen ─────────────────────────────────────────────────────
    def _build(self) -> None:
        self.setWindowTitle(tr("seqopt — sequential optimization"))
        self.setWindowIcon(QIcon(str(icon_path())))
        self.setMinimumSize(*MIN_SIZE)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._work_root = root

        # top bar — project name · save state · budget
        header = QFrame()
        header.setObjectName("header")
        top = QHBoxLayout(header)
        top.setContentsMargins(18, 9, 18, 9)
        top.setSpacing(12)
        self.title = _Elided()
        theme.set_role(self.title, "h2")
        top.addWidget(self.title)
        self.file_pill = _Elided()
        self.file_pill.setObjectName("pill")
        top.addWidget(self.file_pill)
        top.addStretch(1)
        self.budget_label = QLabel()
        theme.set_role(self.budget_label, "muted")
        top.addWidget(self.budget_label)
        self.budget_bar = QProgressBar()
        self.budget_bar.setFixedWidth(180)
        self.budget_bar.setTextVisible(False)
        top.addWidget(self.budget_bar)
        self.save_btn = QPushButton(tr("Save"))
        self.save_btn.setToolTip("Ctrl+S")                          # i18n: skip (a key sequence)
        self.save_btn.clicked.connect(self.save_project)
        top.addWidget(self.save_btn)
        root.addWidget(header)

        # left step rail + screens
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.nav = NavList(list(zip(NAV_NUMBERS, tab_names())))
        self.nav.currentRowChanged.connect(self._go)
        body.addWidget(self.nav)

        page = QVBoxLayout()
        page.setContentsMargins(22, 16, 22, 10)
        page.setSpacing(10)
        self.stack = QStackedWidget()
        self.tab_setup = SetupTab(self.project)
        self.tab_data = DataTab(self.project)
        self.tab_diag = DiagTab(self.project)
        # The Model and Report tabs drag in matplotlib. Import that before the
        # window shows and the first launch freezes for minutes building the
        # font cache (measured). They are created on first click.
        self._tab_model = None
        self._tab_report = None
        self.tab_recommend = RecommendTab(self.project)
        self.tab_help = HelpTab(self.project)
        self.tab_setup.changed.connect(self._on_project_changed)
        self.tab_data.changed.connect(lambda: self._on_project_changed(False))
        self.tab_recommend.points_accepted.connect(self._insert_suggested_rows)
        self.tab_recommend.override_changed.connect(self._on_override_changed)
        self.tab_recommend.acquisition_changed.connect(self._on_acquisition_changed)
        for w in (self.tab_setup, self.tab_data, self.tab_diag,
                  _Loading(tr("Model")), self.tab_recommend, _Loading(tr("Report")), self.tab_help):
            self.stack.addWidget(w)
        self.tab_diag.help_requested.connect(self.open_help)
        self.tab_recommend.help_requested.connect(self.open_help)
        page.addWidget(self.stack, 1)

        # what to do next — the screen decides (borrowed from Design-Expert's linear flow)
        self.guide = QLabel()
        self.guide.setWordWrap(True)
        # a wrapping label only gets the height its text needs if it asks for it
        sp = self.guide.sizePolicy()
        sp.setHeightForWidth(True)
        self.guide.setSizePolicy(sp)
        page.addWidget(self.guide)
        body.addLayout(page, 1)
        root.addLayout(body, 1)

        # the start screen and the workspace stack and swap
        self.shell = QStackedWidget()
        self.shell.addWidget(self._start_screen())
        self.shell.addWidget(central)
        self.shell.currentChanged.connect(lambda i: self.statusBar().setVisible(i == 1))
        self.setCentralWidget(self.shell)
        self.nav.setCurrentRow(0)

        # bottom status bar — the gate badges show on every screen
        self.badges = QLabel()
        self.badges.setContentsMargins(10, 0, 0, 0)
        self.calc_time = QLabel()
        self.calc_time.setStyleSheet(theme.small())
        self.statusBar().addWidget(self.badges, 1)
        self.statusBar().addPermanentWidget(self.calc_time)
        self.statusBar().setVisible(False)

    def _place_window(self) -> None:
        """Window size — 90% of the screen, capped at 1440×900, remembering the last position.

        A 1366×768 laptop has only ~730px of usable height. A fixed 860px used
        to clip the bottom. Measure per screen instead.
        """
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else QRect(0, 0, 1440, 900)
        if QApplication.platformName() != "offscreen":
            geo = QSettings("seqopt", "seqopt").value("geometry")
            if geo is not None and self.restoreGeometry(geo) \
                    and avail.contains(self.frameGeometry().center()):
                return
        w = max(MIN_SIZE[0], min(1440, int(avail.width() * 0.9)))
        h = max(MIN_SIZE[1], min(900, int(avail.height() * 0.92)))
        w, h = min(w, avail.width()), min(h, avail.height())
        self.resize(w, h)
        self.move(avail.center().x() - w // 2, avail.center().y() - h // 2)

    def _start_screen(self) -> StartScreen:
        scr = StartScreen(self.recent_files())
        scr.language_changed.connect(self.switch_language)
        scr.new_project.connect(self._start_new)
        scr.open_file.connect(self.open_project)
        scr.open_path.connect(self._open_path)
        return scr

    def show_start(self) -> None:
        """Return to the start screen, rereading the recent-file list."""
        old = self.shell.widget(0)
        self.shell.removeWidget(old)
        old.deleteLater()
        self.shell.insertWidget(0, self._start_screen())
        self.shell.setCurrentIndex(0)

    def _start_new(self) -> None:
        self._swap(Project())
        self.shell.setCurrentIndex(1)
        self.nav.setCurrentRow(0)

    def _open_path(self, path: str) -> None:
        try:
            self._swap(Project.load(path))
        except Exception as e:                       # noqa: BLE001
            QMessageBox.critical(self, tr("Could not open"), str(e))
            return
        self.remember_recent(path)
        self.shell.setCurrentIndex(1)

    # ── recent files ───────────────────────────────────────────────
    def recent_files(self) -> list[str]:
        try:
            lines = open(RECENT_FILE, encoding="utf-8").read().splitlines()
        except OSError:
            return []
        return [p for p in lines if p and os.path.exists(p)][:RECENT_MAX]

    def remember_recent(self, path: str) -> None:
        items = [path] + [p for p in self.recent_files() if p != path]
        try:
            with open(RECENT_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(items[:RECENT_MAX]))
        except OSError:
            pass

    def nav_to(self, index: int) -> None:
        if 0 <= index < self.nav.count():
            self.nav.setCurrentRow(index)

    def _menu(self) -> None:
        m = self.menuBar().addMenu(tr("File"))
        for text, seq, fn in (
            (tr("New project"), QKeySequence.New, self.new_project),
            (tr("Open…"), QKeySequence.Open, self.open_project),
            (tr("Save"), QKeySequence.Save, self.save_project),
            (tr("Save as…"), QKeySequence.SaveAs, lambda: self.save_project(as_new=True)),
        ):
            a = QAction(text, self)
            a.setShortcut(seq)
            a.triggered.connect(fn)
            m.addAction(a)
        m.addSeparator()
        imp = QAction(tr("Import data…"), self)
        imp.triggered.connect(self.tab_data.import_file)
        m.addAction(imp)
        m.addSeparator()
        home = QAction(tr("Start screen"), self)
        home.triggered.connect(self.show_start)
        m.addAction(home)

        lang = self.menuBar().addMenu(tr("Language"))
        group = QActionGroup(self)
        group.setExclusive(True)
        for code in i18n.LANGUAGES:
            a = QAction(i18n.NAMES[code], self)      # a language names itself — never translated
            a.setCheckable(True)
            a.setChecked(code == i18n.language())
            a.triggered.connect(lambda _=False, c=code: self.switch_language(c))
            group.addAction(a)
            lang.addAction(a)

    # ── language ───────────────────────────────────────────────────
    def switch_language(self, lang: str) -> "MainWindow":
        """Save the choice and rebuild this window in `lang`, carrying the open project across.

        Retranslating in place would mean every screen remembering every string it ever set —
        one forgotten label and half the window stays in the old language. A new window built
        from the same **project object** (not its file: unsaved edits come along) cannot drift.
        """
        if lang == i18n.language():
            return self
        QSettings("seqopt", "seqopt").setValue("language", lang)
        i18n.set_language(lang)

        self.runner.cancel()      # this window's diagnosis is about to have nowhere to land
        shell_index, row, dirty = self.shell.currentIndex(), self.nav.currentRow(), self._dirty
        win = MainWindow(self.project)
        win._dirty = dirty
        win.restoreGeometry(self.saveGeometry())
        win.shell.setCurrentIndex(shell_index)
        if shell_index == 1:
            win.nav.setCurrentRow(max(0, row))
        win.show()
        app = QApplication.instance()
        if app is not None:
            app._seqopt_window = win        # the old window is the only reference — hold the new one
        self._dirty = False                 # the new window carries the unsaved state; do not ask twice
        self.close()
        self.deleteLater()
        return win

    # ── heavy tabs: created on first view ──────────────────────────
    @property
    def tab_model(self):
        if self._tab_model is None:
            from .tab_model import ModelTab
            self._tab_model = ModelTab(self.project)
            self._tab_model.set_acquisition(self._acquisition)
            self._swap_stack(3, self._tab_model)
            if self._last_fast is not None:                 # hand over what was computed meanwhile
                self._tab_model.set_model(self.dataset, self._last_fast["model"],
                                          self._last_fast["nugget"])
            self._tab_model.set_loocv(self._last_loocv)
        return self._tab_model

    @property
    def tab_report(self):
        if self._tab_report is None:
            from .tab_report import ReportTab
            self._tab_report = ReportTab(self.project)
            self._tab_report.set_bypassed(self.tab_recommend.override.isChecked())
            self._swap_stack(5, self._tab_report)
        return self._tab_report

    def _swap_stack(self, index: int, widget) -> None:
        old = self.stack.widget(index)
        current = self.stack.currentIndex()
        self.stack.removeWidget(old)
        old.deleteLater()
        self.stack.insertWidget(index, widget)
        self.stack.setCurrentIndex(current)

    def _on_acquisition_changed(self) -> None:
        """The Recommend tab is the one place it is chosen. The Model tab redraws with the same method."""
        self._acquisition = self.tab_recommend.acquisition()
        if self._tab_model is not None:
            self._tab_model.set_acquisition(self._acquisition)
        self._push_recommend_context()

    def _on_override_changed(self, on: bool) -> None:
        if self._tab_report is not None:
            self._tab_report.set_bypassed(on)

    def _go(self, row: int) -> None:
        if row == 3:
            self.tab_model                    # first visit constructs it here
        elif row == 5:
            self.tab_report
        self.stack.setCurrentIndex(row)

    def open_help(self, key: str) -> None:
        """Clicking a "why?" link on any screen jumps straight to that topic."""
        self.nav.setCurrentRow(HELP)
        self.tab_help.show_topic(key)

    # ── state flow ─────────────────────────────────────────────────
    def _on_project_changed(self, reload_views: bool = True) -> None:
        """When the project changes, **every screen** redraws.

        Rename a variable in Setup while the data table still shows the old
        column title, and the user cannot tell which settings the screen was
        computed under. Recomputing while leaving the screens alone was exactly
        that state — so they redraw here, together.
        """
        self._dirty = True
        if reload_views:
            self._reload_views()
        self.recompute()

    def _reload_views(self) -> None:
        """Sync the settings-dependent views (column titles, axis names, controls) to the project."""
        self.tab_data.reload()
        if self._tab_model is not None:
            self._tab_model.refresh_labels()
        self.tab_recommend.result = None
        self.tab_recommend.acq_history = []
        if self._tab_report is not None:
            self._tab_report.data = None

    RECALC_DELAY_MS = 250

    def recompute(self, immediate: bool = False) -> None:
        """§7-3 — a measurement change re-runs the flow from here.

        **It waits briefly first.** Fitting a GP and running 4000 bootstrap
        draws on every keystroke freezes the table. It runs once, off the last edit.
        """
        self._refresh_header()
        self._refresh_guidance()
        if immediate:
            self._recalc.stop()
            self._do_recompute()
        else:
            self._recalc.start(self.RECALC_DELAY_MS)

    def _do_recompute(self) -> None:
        self.tab_diag.set_pending()
        self._last_loocv = None
        if self._tab_model is not None:
            self._tab_model.set_loocv(None)
        try:
            self.dataset = self.project.dataset()
        except Exception:                            # noqa: BLE001
            # Python exception text never reaches the screen — speak the user's language
            self.dataset = None
            self.gate = None
            self._set_badges(None)
            self.badges.setText(tr("Enter measurements and the requirements get judged."))
            self._refresh_guidance()
            return
        if self.dataset.n_conditions < 2:
            self.gate = None
            self._set_badges(None)
            self.badges.setText(tr("Diagnosis needs at least 2 conditions."))
            self._refresh_guidance()
            return
        self.runner.submit(self.dataset, want_slow=True)

    def _on_calc_started(self) -> None:
        self.calc_time.setText(tr("⏳ computing…"))
        self.calc_time.setStyleSheet(f"color:{theme.ACCENT};")

    def _on_fast(self, payload) -> None:
        self._last_fast = payload
        self.tab_diag.set_fast(payload["disc"], payload["nugget"])
        self.tab_diag.set_warning(self.dataset)
        if self._tab_model is not None:
            self._tab_model.set_model(self.dataset, payload["model"], payload["nugget"])
        self._apply_gate()
        self.calc_time.setText(tr("discriminability {t}s · ⏳ learnability…",
                                  t=f"{payload['elapsed']:.2f}"))
        self.calc_time.setStyleSheet(f"color:{theme.ACCENT};")

    def _on_slow(self, payload) -> None:
        self._last_loocv = payload["loocv"]
        self.tab_diag.set_slow(payload["loocv"])
        if self._tab_model is not None:
            self._tab_model.set_loocv(payload["loocv"])
        self._apply_gate()
        self.calc_time.setText(tr("✓ diagnosis done · learnability {t}s",
                                  t=f"{payload['elapsed']:.2f}"))
        self.calc_time.setStyleSheet(theme.muted())

    def _on_failed(self, msg: str) -> None:
        self.calc_time.setText(tr("computation failed"))
        self.statusBar().showMessage(tr("Diagnosis failed: {why}", why=msg), 8000)

    def _apply_gate(self) -> None:
        d = self.tab_diag.disc
        if d is None or self.dataset is None:
            return
        r2 = self.tab_diag.loocv.r2 if self.tab_diag.loocv else None
        self.gate = gate(self.project.n_candidates(), self.project.budget_total,
                         r2, d, self.dataset.frac_with_reps)
        self.tab_diag.refresh(self.dataset, self.gate)
        self._set_badges(self.gate)
        self._push_recommend_context()
        self._refresh_guidance()

    def _push_recommend_context(self) -> None:
        """The Recommend tab **does not judge** — it passes the gate, model and acquisition to the core."""
        model = self._last_fast["model"] if self._last_fast else None
        self._acquisition = self.tab_recommend.acquisition()
        self.tab_recommend.set_context(self.dataset, self.gate, model)
        if self._tab_report is not None:
            self._tab_report.set_bypassed(self.tab_recommend.override.isChecked())

    def _insert_suggested_rows(self, payload: list) -> None:
        """Insert the suggested conditions into the data table **as gray rows** (§4-4)."""
        self.tab_data.insert_pending(payload)
        self.nav.setCurrentRow(1)

    # ── status bar ─────────────────────────────────────────────────
    def _refresh_guidance(self) -> None:
        """Aligns step states, tab locks and the next action in one pass."""
        r = assess(self.project, self.dataset, self.gate)

        step_indices = [index for index, _, _ in STEPS]
        for i in range(self.nav.count()):
            item = self.nav.item(i)
            ok = r.ready.get(i, True)
            item.setFlags(item.flags() | Qt.ItemIsEnabled if ok
                          else item.flags() & ~Qt.ItemIsEnabled)
            item.setToolTip(r.blocked_reason(i) or "")
            if not ok:
                state = "locked"
            elif i == r.current:
                state = "next"
            elif i in step_indices and i < r.current:
                state = "done"
            else:
                state = "ready"
            self.nav.set_state(i, state)

        self.guide.setText(tr("<b>Next</b> — {action}", action=r.next_action))
        self.guide.setStyleSheet(theme.card("info"))
        return r

    def _set_badges(self, g) -> None:
        if g is None:
            self.badges.setText(tr("requirements —"))
            return
        parts = []
        for num, label, state in (("①", tr("candidates"), g.cond_count),
                                  ("②", tr("learnability"), g.learnable),
                                  ("③", tr("discriminability"), g.discrim),
                                  ("④", tr("replicates"), g.replicates)):
            colour = theme.STATE_COLOR.get(state, theme.TEXT_FAINT)
            parts.append(f"<span style='color:{colour}; font-weight:600'>"                  # i18n: skip
                         f"{num}{label} {theme.STATE_MARK.get(state, '—')}</span>")
        lock = (f"<b style='color:{theme.FAIL}'>{tr('recommendation LOCKED')}</b>"           # i18n: skip
                if g.locked else
                f"<b style='color:{theme.OK}'>{tr('recommendation available')}</b>")         # i18n: skip
        self.badges.setText(f"<span style='color:{theme.TEXT_MUTED}'>{tr('requirements')}</span>"   # i18n: skip
                            "&nbsp;&nbsp;" + "&nbsp;&nbsp;&nbsp;".join(parts)
                            + "&nbsp;&nbsp;·&nbsp;&nbsp;" + lock)

    def _refresh_header(self) -> None:
        p = self.project
        self.title.setText(p.name or tr("Untitled project"))
        if not p.path:
            where = tr("not saved yet")
        elif self._dirty:
            where = tr("{file} · modified", file=os.path.basename(p.path))
        else:
            where = tr("{file} · saved", file=os.path.basename(p.path))
        self.file_pill.setText(where)
        self.file_pill.setToolTip(p.path or where)
        self.budget_label.setText(tr("measured <b>{used}</b> / budget {total}",
                                     used=p.used, total=p.budget_total))
        # Actual measurements can exceed the budget (importing pre-existing data).
        # The bar fills and the overshoot stays visible — a budget is a plan, not a cap.
        over = p.used > p.budget_total
        self.budget_bar.setMaximum(max(1, p.used if over else p.budget_total))
        self.budget_bar.setValue(p.used)
        self.budget_bar.setFormat(f"{p.used} / {p.budget_total}"
                                  + (tr(" · over budget") if over else ""))
        if over:
            self.budget_label.setText(tr(
                "measured <b style='color:{c}'>{used}</b> / budget {total} · "
                "<span style='color:{c}'>over</span>",
                c=theme.FAIL, used=p.used, total=p.budget_total))
        self.budget_bar.setStyleSheet(
            f"QProgressBar::chunk{{background:{theme.FAIL}}}" if over else "")
        self.budget_bar.setToolTip(
            tr("There are more measurements than the planned budget. "
               "Fix the budget on the Setup tab.") if over else "")

    # ── files ──────────────────────────────────────────────────────
    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        a = QMessageBox.question(self, tr("There are unsaved changes"), tr("Save them?"),
                                 QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if a == QMessageBox.Cancel:
            return False
        if a == QMessageBox.Save:
            return bool(self.save_project())
        return True

    def new_project(self) -> None:
        if not self._confirm_discard():
            return
        self._swap(Project())

    def open_project(self) -> None:
        if not self._confirm_discard():
            return
        fn, _ = QFileDialog.getOpenFileName(self, tr("Open project"), "",
                                            tr("Projects (*{ext})", ext=EXT))
        if not fn:
            return
        try:
            self._swap(Project.load(fn))
            self.remember_recent(fn)
            self.shell.setCurrentIndex(1)
        except Exception as e:                       # noqa: BLE001
            QMessageBox.critical(self, tr("Could not open"), str(e))

    def _swap(self, p: Project) -> None:
        self.project = p
        for tab in (self.tab_setup, self.tab_data, self.tab_diag, self.tab_recommend,
                    self._tab_model, self._tab_report):
            if tab is not None:
                tab.project = p
        self._last_fast = self._last_loocv = None
        if self._tab_report is not None:
            self._tab_report.data = None
        self.tab_recommend.result = None
        self.tab_recommend.acq_history = []
        self.tab_setup.reload()
        self.tab_data.reload()
        self._dirty = False
        self.recompute(immediate=True)

    def save_project(self, as_new: bool = False) -> str | None:
        p = self.project
        path = p.path
        if as_new or not path:
            path, _ = QFileDialog.getSaveFileName(self, tr("Save project"),
                                                  f"{p.name}{EXT}", tr("Projects (*{ext})", ext=EXT))
            if not path:
                return None
            if not path.endswith(EXT):
                path += EXT
        try:
            p.save(path)
        except Exception as e:                       # noqa: BLE001
            QMessageBox.critical(self, tr("Could not save"), str(e))
            return None
        self._dirty = False
        self._refresh_header()
        self.remember_recent(path)
        self.statusBar().showMessage(tr("Saved — {path}", path=path), 4000)
        return path

    def _do_autosave(self) -> None:
        """A lab PC can die and the last state is still recoverable. The user's file is never touched."""
        if not self._dirty or not self.project.measurements:
            return
        try:
            self.project.save(autosave_path(self.project.path))
            self.project.path = self.project.path      # undo the path save() changed
        except Exception:                              # noqa: BLE001
            pass

    def closeEvent(self, event) -> None:
        if not self._confirm_discard():
            event.ignore()
            return
        if QApplication.platformName() != "offscreen":
            QSettings("seqopt", "seqopt").setValue("geometry", self.saveGeometry())
        event.accept()


class _Loading(QWidget):
    """A placeholder for a heavy tab not yet built. Clicking it swaps in the real one."""

    def __init__(self, name: str):
        super().__init__()
        v = QVBoxLayout(self)
        t = QLabel(tr("Preparing the {name} screen…", name=name))
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(theme.muted())
        v.addStretch(1)
        v.addWidget(t)
        v.addStretch(1)
