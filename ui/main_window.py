from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QDateEdit, QPushButton, QFileDialog, QStackedWidget,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from app_controller import AppController, ENGLISH_MONTHS_FULL
from .adb_dialog import AdbSyncDialog

class StepViewer(QMainWindow):
    def __init__(self, db_path="Steps.db"):
        super().__init__()
        self.controller = AppController(self)
        self.adb_dialog = None
        self.init_ui()
        self.controller.load_database(db_path)

    def init_ui(self):
        self.setWindowTitle("MIUI Steps Explorer")
        self.resize(800, 700)
        self.setWindowIcon(QIcon.fromTheme("walk"))
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top Bar
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar_layout = QHBoxLayout(top_bar)
        self.status_label = QLabel("Ready")
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sync_btn = QPushButton(" Sync from Device")
        sync_btn.setIcon(QIcon.fromTheme("network-transmit-receive"))
        sync_btn.clicked.connect(self.open_adb_sync)
        load_btn = QPushButton(" Load DB…")
        load_btn.setIcon(QIcon.fromTheme("document-open"))
        load_btn.clicked.connect(self.prompt_load_db)
        top_bar_layout.addWidget(self.status_label)
        top_bar_layout.addWidget(sync_btn)
        top_bar_layout.addWidget(load_btn)
        main_layout.addWidget(top_bar)

        # Page Stack
        self.stack = QStackedWidget()
        self.stack.currentChanged.connect(self.controller.draw_plots)
        main_layout.addWidget(self.stack)

        # Create Pages
        self.day_view = self.create_day_view()
        self.month_view = self.create_month_view()
        self.year_view = self.create_year_view()
        self.stack.addWidget(self.day_view["widget"])
        self.stack.addWidget(self.month_view["widget"])
        self.stack.addWidget(self.year_view["widget"])

        # Bottom Navigation
        nav_bar = QFrame()
        nav_bar.setObjectName("NavBar")
        nav_layout = QHBoxLayout(nav_bar)
        btn_day = QPushButton(" Day")
        btn_day.setIcon(QIcon.fromTheme("go-jump"))
        btn_day.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_month = QPushButton(" Month")
        btn_month.setIcon(QIcon.fromTheme("view-calendar-month"))
        btn_month.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_year = QPushButton(" Year")
        btn_year.setIcon(QIcon.fromTheme("view-calendar"))
        btn_year.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        nav_layout.addStretch()
        nav_layout.addWidget(btn_day)
        nav_layout.addWidget(btn_month)
        nav_layout.addWidget(btn_year)
        nav_layout.addStretch()
        main_layout.addWidget(nav_bar, 0, Qt.AlignmentFlag.AlignBottom)

    def create_day_view(self):
        widget, layout = QWidget(), QVBoxLayout()
        widget.setLayout(layout)
        control_layout = QHBoxLayout()
        prev_btn, next_btn = QPushButton("< Prev"), QPushButton("Next >")
        prev_btn.clicked.connect(self.prev_day)
        next_btn.clicked.connect(self.next_day)
        self.day_date_edit = QDateEdit(calendarPopup=True)
        self.day_date_edit.setDate(QDate.currentDate())
        self.day_date_edit.dateChanged.connect(self.controller.draw_plots)
        control_layout.addWidget(prev_btn)
        control_layout.addWidget(self.day_date_edit)
        control_layout.addWidget(next_btn)
        layout.addLayout(control_layout)
        self.day_total_label = QLabel("Total Steps: 0")
        self.day_total_label.setObjectName("TotalStepsLabel")
        self.day_total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas = FigureCanvas(Figure(figsize=(5, 4)))
        layout.addWidget(self.day_total_label)
        layout.addWidget(canvas)
        return {"widget": widget, "canvas": canvas, "controls": [prev_btn, self.day_date_edit, next_btn]}

    def create_month_view(self):
        widget, layout = QWidget(), QVBoxLayout()
        widget.setLayout(layout)
        control_layout = QHBoxLayout()
        self.month_year_combo = QComboBox()
        self.month_month_combo = QComboBox()
        self.month_month_combo.addItems(ENGLISH_MONTHS_FULL)
        self.month_year_combo.currentIndexChanged.connect(self.controller.draw_plots)
        self.month_month_combo.currentIndexChanged.connect(self.controller.draw_plots)
        control_layout.addWidget(QLabel("Year:"))
        control_layout.addWidget(self.month_year_combo)
        control_layout.addWidget(QLabel("Month:"))
        control_layout.addWidget(self.month_month_combo)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        self.month_stats_label = QLabel("Total: 0 | Avg: 0")
        self.month_stats_label.setObjectName("TotalStepsLabel")
        self.month_stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas = FigureCanvas(Figure(figsize=(5, 4)))
        canvas.mpl_connect("pick_event", self.controller.on_pick_month_bar)
        layout.addWidget(self.month_stats_label)
        layout.addWidget(canvas)
        return {"widget": widget, "canvas": canvas, "controls": [self.month_year_combo, self.month_month_combo]}

    def create_year_view(self):
        widget, layout = QWidget(), QVBoxLayout()
        widget.setLayout(layout)
        control_layout = QHBoxLayout()
        self.year_year_combo = QComboBox()
        self.year_year_combo.currentIndexChanged.connect(self.controller.draw_plots)
        control_layout.addWidget(QLabel("Year:"))
        control_layout.addWidget(self.year_year_combo)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        self.year_stats_label = QLabel("Total: 0 | Avg: 0")
        self.year_stats_label.setObjectName("TotalStepsLabel")
        self.year_stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas = FigureCanvas(Figure(figsize=(5, 4)))
        layout.addWidget(self.year_stats_label)
        layout.addWidget(canvas)
        return {"widget": widget, "canvas": canvas, "controls": [self.year_year_combo]}

    def open_adb_sync(self):
        self.adb_dialog = AdbSyncDialog(self)
        self.adb_dialog.sync_successful.connect(self.controller.load_database)
        self.adb_dialog.exec()

    def prompt_load_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Steps DB", "", "SQLite DB (*.db)")
        if path:
            self.controller.load_database(path)

    def set_ui_enabled(self, enabled):
        for view in [self.day_view, self.month_view, self.year_view]:
            for control in view["controls"]:
                control.setEnabled(enabled)

    def prev_day(self):
        self.day_date_edit.setDate(self.day_date_edit.date().addDays(-1))

    def next_day(self):
        self.day_date_edit.setDate(self.day_date_edit.date().addDays(1))
