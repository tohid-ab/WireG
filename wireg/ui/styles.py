"""
shadcn-inspired Glassmorphism Theme and Design System for WireG.
Combines deep zinc tones, frosted glass translucency, crisp borders, and radiant accents.
"""

DARK_THEME_QSS = """
/* ==========================================================================
   Base & Window Level
   ========================================================================== */
QWidget {
    background-color: transparent;
    color: #f4f4f5;
    font-family: 'Inter', 'SF Pro Display', 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #090d16;
}

QDialog {
    background-color: #0d121f;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
}

/* ==========================================================================
   Glass Panels & Frames (shadcn Card style)
   ========================================================================== */
QFrame#glassPanel, QFrame#trafficCard {
    background-color: rgba(20, 26, 40, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 14px;
}

QFrame#configCard {
    background-color: rgba(18, 24, 38, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
}

QFrame#configCard:hover {
    background-color: rgba(26, 35, 54, 0.75);
    border: 1px solid rgba(99, 102, 241, 0.35);
}

/* ==========================================================================
   Scroll Area & Modern Thin Scrollbars
   ========================================================================== */
QScrollArea {
    background: transparent;
    border: none;
}

QScrollBar:vertical {
    border: none;
    background: rgba(255, 255, 255, 0.02);
    width: 6px;
    margin: 4px 0px 4px 0px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.15);
    min-height: 30px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(99, 102, 241, 0.6);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ==========================================================================
   shadcn Inputs (Input, Textarea)
   ========================================================================== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: rgba(15, 20, 32, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
    padding: 8px 14px;
    color: #fafafa;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid #6366f1;
    background-color: rgba(20, 26, 42, 0.9);
}

QLineEdit:disabled, QTextEdit:disabled {
    background-color: rgba(12, 16, 26, 0.5);
    color: #71717a;
    border: 1px solid rgba(255, 255, 255, 0.04);
}

/* ==========================================================================
   shadcn Buttons (Primary, Outline, Ghost, Connect, Disconnect)
   ========================================================================== */
QPushButton {
    background-color: rgba(255, 255, 255, 0.05);
    color: #f4f4f5;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
    color: #ffffff;
}

QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.04);
}

QPushButton:disabled {
    background-color: rgba(255, 255, 255, 0.02);
    color: #52525b;
    border-color: rgba(255, 255, 255, 0.04);
}

/* Primary shadcn Accent Button (Indigo Glow) */
QPushButton#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #4f46e5);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.25);
    font-weight: 600;
}

QPushButton#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c7eff, stop:1 #6366f1);
    border-color: rgba(255, 255, 255, 0.4);
}

QPushButton#primaryButton:pressed {
    background: #4338ca;
}

/* Connect Button (Emerald Glass Glow) */
QPushButton#connectButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10b981, stop:1 #059669);
    color: #ffffff;
    border: 1px solid rgba(52, 211, 153, 0.4);
    font-weight: 700;
    font-size: 13px;
    padding: 8px 20px;
    border-radius: 9px;
}

QPushButton#connectButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #34d399, stop:1 #10b981);
    border-color: rgba(110, 231, 183, 0.6);
}

QPushButton#connectButton:pressed {
    background: #047857;
}

/* Disconnect Button (Ruby Glass Glow) */
QPushButton#disconnectButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ef4444, stop:1 #dc2626);
    color: #ffffff;
    border: 1px solid rgba(248, 113, 113, 0.4);
    font-weight: 700;
    font-size: 13px;
    padding: 8px 20px;
    border-radius: 9px;
}

QPushButton#disconnectButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f87171, stop:1 #ef4444);
    border-color: rgba(252, 165, 165, 0.6);
}

QPushButton#disconnectButton:pressed {
    background: #b91c1c;
}

/* Ghost / Icon Button */
QPushButton#iconButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 4px;
    color: #a1a1aa;
}

QPushButton#iconButton:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #ffffff;
}

/* ==========================================================================
   shadcn Dropdowns & Select (QComboBox)
   ========================================================================== */
QComboBox {
    background-color: rgba(15, 20, 32, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 10px;
    padding: 7px 14px;
    color: #fafafa;
    font-weight: 500;
}

QComboBox:hover {
    border-color: rgba(255, 255, 255, 0.18);
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #0f1422;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    selection-background-color: #6366f1;
    color: #fafafa;
    padding: 6px;
}

/* ==========================================================================
   shadcn Tabs (Segmented Control style)
   ========================================================================== */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: rgba(15, 20, 32, 0.55);
    border-radius: 12px;
    top: -1px;
}

QTabBar::tab {
    background-color: rgba(255, 255, 255, 0.04);
    color: #a1a1aa;
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 8px 22px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: rgba(99, 102, 241, 0.18);
    color: #818cf8;
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-bottom: 2px solid #6366f1;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(255, 255, 255, 0.08);
    color: #f4f4f5;
}

/* ==========================================================================
   Typography & Labels
   ========================================================================== */
QLabel {
    color: #f4f4f5;
}

QLabel#titleLabel {
    font-size: 19px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #a1a1aa;
}

QLabel#sectionTitle {
    font-size: 14px;
    font-weight: 700;
    color: #a5b4fc;
    margin-top: 10px;
    margin-bottom: 4px;
}

/* ==========================================================================
   shadcn Context Menu & Tooltips
   ========================================================================== */
QMenu {
    background-color: #0f1422;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 24px 8px 12px;
    border-radius: 6px;
    color: #e4e4e7;
    font-weight: 500;
}

QMenu::item:selected {
    background-color: #6366f1;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: rgba(255, 255, 255, 0.08);
    margin: 4px 6px;
}

QToolTip {
    background-color: #0d121f;
    color: #f4f4f5;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}
"""
