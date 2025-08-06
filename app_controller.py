from datetime import datetime, timedelta
import pandas as pd
import matplotlib.dates as mdates

from PyQt6.QtCore import QThread, QObject, pyqtSignal, QDate

from data_manager import DataManager, DataWorker

ENGLISH_MONTHS_FULL = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
ENGLISH_MONTHS_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

class AppController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.data_manager = DataManager(None)
        self.thread = None
        self.worker = None

    def load_database(self, db_path):
        self.view.set_ui_enabled(False)
        self.view.status_label.setText(f"Loading {db_path}...")
        self.thread = QThread()
        self.worker = DataWorker(db_path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_loading_finished)
        self.worker.error.connect(self.on_loading_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_loading_finished(self, data_manager):
        self.data_manager = data_manager
        if not data_manager.db_path or self.data_manager.df.empty:
            self.view.status_label.setText("Failed to load data or DB is empty.")
            self.view.set_ui_enabled(True)
            for view_dict in [self.view.day_view, self.view.month_view, self.view.year_view]:
                view_dict['canvas'].figure.clear()
                view_dict['canvas'].draw()
            return
        self.view.status_label.setText(f"Loaded successfully from {data_manager.db_path}")
        self.populate_controls()
        self.view.set_ui_enabled(True)
        self.draw_plots()

    def on_loading_error(self, err_msg):
        self.view.status_label.setText(f"Error: {err_msg}")
        self.view.set_ui_enabled(True)

    def populate_controls(self):
        if self.data_manager.df.empty: return
        view = self.view
        controls_to_block = [view.month_year_combo, view.year_year_combo, view.day_date_edit, view.month_month_combo]
        for control in controls_to_block:
            control.blockSignals(True)

        years = sorted(self.data_manager.yearly.index.astype(str))
        view.month_year_combo.clear()
        view.month_year_combo.addItems(years)
        view.year_year_combo.clear()
        view.year_year_combo.addItems(years)

        if years:
            view.month_year_combo.setCurrentText(years[-1])
            view.year_year_combo.setCurrentText(years[-1])
        if self.data_manager.available_dates:
            last_date = self.data_manager.available_dates[-1]
            view.day_date_edit.setDate(QDate(last_date.year, last_date.month, last_date.day))
            view.month_month_combo.setCurrentIndex(last_date.month - 1)

        for control in controls_to_block:
            control.blockSignals(False)

    def draw_plots(self, _=None):
        if self.data_manager.df.empty or not self.view.centralWidget().isVisible():
            return
        current_index = self.view.stack.currentIndex()
        if current_index == 0: self.draw_day_plot()
        elif current_index == 1: self.draw_month_plot()
        elif current_index == 2: self.draw_year_plot()

    def draw_day_plot(self):
        view = self.view.day_view
        canvas, fig = view["canvas"], view["canvas"].figure
        fig.clear()
        ax = fig.add_subplot(111)
        sel_date = self.view.day_date_edit.date().toPyDate()
        hourly_data = self.data_manager.hourly.get(sel_date, pd.Series(dtype=int))
        all_hours = pd.Series(0, index=range(24))
        hourly_data = all_hours.add(hourly_data, fill_value=0)
        ax.bar(hourly_data.index, hourly_data.values, color="#4FC3F7", alpha=0.8)
        ax.set_title(f"Hourly Steps for {sel_date.strftime('%Y-%m-%d')}", color="white")
        ax.set_xticks(range(0, 24, 2))
        total_steps = int(self.data_manager.daily.get(sel_date, 0))
        self.view.day_total_label.setText(f"Total Steps: {total_steps:,}")
        self.finalize_plot(ax, fig, canvas, xlabel="Hour of the Day")

    def draw_month_plot(self):
        view = self.view.month_view
        canvas, fig = view["canvas"], view["canvas"].figure
        fig.clear()
        ax = fig.add_subplot(111)
        year_str = self.view.month_year_combo.currentText()
        if not year_str: return
        year, month = int(year_str), self.view.month_month_combo.currentIndex() + 1
        start_date = datetime(year, month, 1).date()
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
        date_range = pd.date_range(start=start_date, end=end_date).date
        daily_data = self.data_manager.daily.reindex(date_range, fill_value=0)
        ax.bar(daily_data.index, daily_data.values, color="#81C784", picker=5)
        month_name = f"{ENGLISH_MONTHS_FULL[month - 1]} {year}"
        ax.set_title(f"Daily Steps for {month_name}", color="white")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        fig.autofmt_xdate(rotation=0, ha="center")
        total = int(daily_data.sum())
        avg = int(daily_data[daily_data > 0].mean()) if total > 0 else 0
        self.view.month_stats_label.setText(f"Total: {total:,} steps  |  Daily Avg: {avg:,} steps")
        self.finalize_plot(ax, fig, canvas, xlabel="Day of Month")

    def draw_year_plot(self):
        view = self.view.year_view
        canvas, fig = view["canvas"], view["canvas"].figure
        fig.clear()
        ax = fig.add_subplot(111)
        year_str = self.view.year_year_combo.currentText()
        if not year_str: return
        year = int(year_str)
        monthly_data_for_year = self.data_manager.monthly[self.data_manager.monthly.index.str.startswith(year_str)]
        steps = [monthly_data_for_year.get(f"{year}-{m:02d}", 0) for m in range(1, 13)]
        ax.plot(ENGLISH_MONTHS_ABBR, steps, "-o", color="#FFB74D", markersize=8, markerfacecolor="#F57C00")
        ax.set_title(f"Monthly Steps for {year}", color="white")
        total = int(sum(steps))
        avg = int(pd.Series(steps)[pd.Series(steps) > 0].mean()) if total > 0 else 0
        self.view.year_stats_label.setText(f"Total: {total:,} steps  |  Monthly Avg: {avg:,} steps")
        self.finalize_plot(ax, fig, canvas, xlabel="Month", grid=True)

    def finalize_plot(self, ax, fig, canvas, xlabel="", ylabel="Steps", grid=False):
        ax.set_xlabel(xlabel, color="white")
        ax.set_ylabel(ylabel, color="white")
        ax.tick_params(axis="x", colors="white")
        ax.tick_params(axis="y", colors="white")
        for spine in ax.spines.values():
            spine.set_color("gray")
        ax.set_facecolor("#212121")
        fig.set_facecolor("#212121")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        if grid:
            ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()
        canvas.draw()

    def on_pick_month_bar(self, event):
        if not hasattr(event.artist, "get_x"): return
        date_num = event.artist.get_x() + event.artist.get_width() / 2
        try:
            date = mdates.num2date(date_num).date()
            self.view.day_date_edit.setDate(QDate(date.year, date.month, date.day))
            self.view.stack.setCurrentIndex(0)
        except (ValueError, TypeError):
            pass
