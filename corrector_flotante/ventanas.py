"""Ventanas: icono flotante, recuadro de revisión y aviso breve."""
import html

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMenu, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from motor import ICON_SIZE, HOTKEY_TOGGLE, MAX_SUGGESTIONS, snippet_parts

FLOAT = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
MAX_CARDS = 8

CSS = """
    QFrame#card { background: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 8px; }
    QFrame#item { background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 6px; }
    QLabel { color: #111827; font-family: 'Segoe UI'; font-size: 12px; }
    QLabel#title { font-weight: bold; color: #1E3A8A; font-size: 13px; }
    QLabel#why { color: #4B5563; font-size: 11px; }
    QLabel#cat { color: #1E3A8A; font-weight: bold; font-size: 11px; }
    QLabel#hint { color: #15803D; font-weight: bold; }
    QScrollArea { background: transparent; border: none; }
    QWidget#list { background: transparent; }
    QPushButton { padding: 4px 10px; border: none; border-radius: 6px; font-family: 'Segoe UI'; font-size: 12px; }
    QPushButton#sug { background: #DCFCE7; color: #166534; font-weight: bold; }
    QPushButton#sug:hover { background: #BBF7D0; }
    QPushButton#all { background: #2563EB; color: white; font-weight: bold; }
    QPushButton#all:hover { background: #1D4ED8; }
    QPushButton#close { background: #F3F4F6; color: #374151; }
    QPushButton#close:hover { background: #E5E7EB; }
"""


def snippet_html(text: str, start: int, end: int) -> str:
    """Fragmento con el error resaltado; el texto del usuario se escapa."""
    p = snippet_parts(text, start, end)
    return ("{pre}{before}<span style='background:#FEE2E2; color:#B91C1C; "
            "text-decoration:line-through; font-weight:bold;'>{wrong}</span>{after}{post}").format(
        pre="… " if p["cut_left"] else "", before=html.escape(p["before"]),
        wrong=html.escape(p["wrong"]), after=html.escape(p["after"]),
        post=" …" if p["cut_right"] else "")


class FloatingIcon(QWidget):
    clicked = Signal()
    toggle_requested = Signal()
    quit_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(FLOAT)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(ICON_SIZE, ICON_SIZE)
        self.setToolTip(f"Revisar lo escrito (clic derecho: opciones; {HOTKEY_TOGGLE} oculta o muestra)")
        self._busy = False
        self._drag = None
        self._moved = False

    @property
    def busy(self) -> bool:
        return self._busy

    def set_busy(self, busy: bool):
        self._busy = busy
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#9CA3AF" if self._busy else "#2563EB"))
        p.drawEllipse(1, 1, ICON_SIZE - 2, ICON_SIZE - 2)
        p.setPen(QColor("white"))
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, "✓")

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.addAction("Revisar ahora", self.clicked.emit)
        menu.addAction("Ocultar icono", self.toggle_requested.emit)
        menu.addSeparator()
        menu.addAction("Salir", self.quit_requested.emit)
        menu.exec(e.globalPos())

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._moved = False

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            new = e.globalPosition().toPoint() - self._drag
            if (new - self.pos()).manhattanLength() > 3:
                self._moved = True
            self.move(new)

    def mouseReleaseEvent(self, _):
        if self._drag is not None and not self._moved:
            self.clicked.emit()
        self._drag = None


class Toast(QLabel):
    def __init__(self):
        super().__init__(None, FLOAT)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setWordWrap(True)
        self.setFixedWidth(320)
        self.setStyleSheet("background:#111827; color:#F9FAFB; border-radius:8px; padding:8px 10px;"
                           "font-family:'Segoe UI'; font-size:12px;")
        self._timer = QTimer(self, singleShot=True)
        self._timer.timeout.connect(self.hide)

    def show_near(self, text: str, anchor, ms: int):
        self.setText(text)
        self.adjustSize()
        self.move(max(0, anchor.x() + ICON_SIZE - self.width()), max(0, anchor.y() - self.height() - 8))
        self.show()
        self._timer.start(ms)


class SuggestionPopup(QWidget):
    fix_chosen = Signal(object, str)
    fix_all_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(FLOAT)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setStyleSheet(CSS)
        self._issues = []

        outer = QVBoxLayout(self)
        card = QFrame(objectName="card")
        outer.addWidget(card)
        root = QVBoxLayout(card)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)
        self.title = QLabel("Revisión", objectName="title")
        root.addWidget(self.title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.list_widget = QWidget(objectName="list")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.scroll.setWidget(self.list_widget)
        self.scroll.setMaximumHeight(430)
        root.addWidget(self.scroll)

        footer = QHBoxLayout()
        self.all_btn = QPushButton("", objectName="all")
        self.all_btn.clicked.connect(self._fix_all)
        close = QPushButton("Cerrar", objectName="close")
        close.clicked.connect(self.hide)
        footer.addWidget(self.all_btn)
        footer.addStretch()
        footer.addWidget(close)
        root.addLayout(footer)

    def _card(self, text: str, issue) -> QFrame:
        frame = QFrame(objectName="item")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(3)
        ctx = QLabel(snippet_html(text, issue.start, issue.end))
        ctx.setTextFormat(Qt.RichText)
        ctx.setWordWrap(True)
        why = QLabel("<b>Por qué:</b> " + html.escape(issue.explanation), objectName="why")
        why.setTextFormat(Qt.RichText)
        why.setWordWrap(True)
        lay.addWidget(QLabel(html.escape(issue.category), objectName="cat"))
        lay.addWidget(ctx)
        lay.addWidget(why)
        if issue.suggestions:
            row = QHBoxLayout()
            row.addWidget(QLabel("Cambiar por:", objectName="hint"))
            for s in issue.suggestions[:min(3, MAX_SUGGESTIONS)]:
                btn = QPushButton(s, objectName="sug")
                btn.clicked.connect(lambda _=False, i=issue, r=s: self._choose(i, r))
                row.addWidget(btn)
            row.addStretch()
            lay.addLayout(row)
        return frame

    def show_issues(self, text, issues, pos):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._issues = list(issues)
        fixable = [i for i in issues if i.suggestions]
        if not issues:
            self.title.setText("✓ Sin errores detectados")
            self.list_layout.addWidget(QLabel("No encontré errores en las últimas palabras."))
        else:
            self.title.setText(f"Se encontraron {len(issues)} posible(s) error(es)")
            for issue in issues[:MAX_CARDS]:
                self.list_layout.addWidget(self._card(text, issue))
            if len(issues) > MAX_CARDS:
                self.list_layout.addWidget(QLabel(f"… y {len(issues) - MAX_CARDS} más"))
        self.list_layout.addStretch()
        self.all_btn.setText(f"Corregir todo ({len(fixable)})")
        self.all_btn.setVisible(len(fixable) > 1)
        self.setFixedWidth(400)
        self.adjustSize()
        self.move(pos)
        self.show()

    def _choose(self, issue, replacement):
        self.hide()
        self.fix_chosen.emit(issue, replacement)

    def _fix_all(self):
        self.hide()
        self.fix_all_requested.emit([i for i in self._issues if i.suggestions])
