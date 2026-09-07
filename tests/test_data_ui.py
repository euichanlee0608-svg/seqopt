# -*- coding: utf-8 -*-
"""Setup · Data · the import wizard, in Korean.

`tests/test_i18n.py` proves every string has a Korean line; these prove the screens actually
ask for it at the moment they are built. The two places that could not, because they were
module-level constants translated once at import, are the variable-type combo and the
wizard's role combo — so those are what is checked.
"""
from __future__ import annotations

from core.project import Project
from core.spec import ObjSpec, VarSpec


def test_variable_type_combo_is_korean(qapp, korean):
    """The type combo was a module constant; built at import it would stay English forever."""
    from ui.tab_setup import SetupTab

    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    tab = SetupTab(p)
    combo = tab.vars.cellWidget(0, 2)
    assert [combo.itemText(i) for i in range(combo.count())] == ["연속형", "정수형", "범주형"]
    assert combo.currentText() == "연속형"
    assert combo.currentData() == "continuous"           # the key behind it never changes
    # the column is sized from the labels in front of the user, not from the English ones
    assert tab.vars.columnWidth(2) >= tab.vars.fontMetrics().horizontalAdvance("범주형") + 34


def test_import_wizard_title_and_roles_are_korean(qapp, korean):
    from ui.import_wizard import ImportWizard

    dlg = ImportWizard()
    assert dlg.windowTitle() == "데이터 가져오기 — 구조 세팅"
    assert dlg.summary.text() == "파일을 고르면 결과를 미리 알려 드립니다."
    heads = [dlg.mapper.horizontalHeaderItem(c).text() for c in range(dlg.mapper.columnCount())]
    assert heads == ["열", "예시 값", "역할", "이름", "단위", "형"]
    dlg.deleteLater()


def test_data_tab_headers_and_summary_are_korean(qapp, korean):
    from ui.tab_data import DataTab

    p = Project(inputs=[VarSpec("power", "W", "continuous", 150, 200)], objective=ObjSpec("G/D"))
    p.add([150.0], 1.2)
    tab = DataTab(p)
    heads = [tab.table.horizontalHeaderItem(c).text() for c in range(tab.table.columnCount())]
    assert heads == ["power (W)", "G/D", "제외", "메모"]      # variable names stay as they are
    assert "유효 조건" in tab.summary.text()


def test_setup_validation_messages_are_korean(qapp, korean):
    from ui.tab_setup import SetupTab

    p = Project(inputs=[VarSpec("x", "", "continuous", 0, 10)], objective=ObjSpec("y"))
    tab = SetupTab(p)
    tab.vars.item(0, 4).setText("")                  # max is gone → min/max is not a number
    assert "숫자가 아닙니다" in tab.var_msg.text()
