import sqlite3
import pandas as pd
from PyQt6.QtCore import QObject, pyqtSignal
from logger import log
from datetime import datetime


class DataManager:
    """Handles loading and processing of step data to avoid re-computation."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.df = pd.DataFrame()
        self.daily = pd.Series(dtype=int)
        self.hourly = pd.Series(dtype=int)
        self.monthly = pd.Series(dtype=int)
        self.yearly = pd.Series(dtype=int)
        self.available_dates = []

    def load_and_process(self):
        """Loads data from the DB and performs all aggregations once."""
        if not self.db_path:
            return
        try:
            log.info(f"Connecting to database: {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT _begin_time, _steps FROM StepsTable", conn)
            conn.close()

            if df.empty:
                log.warning("Database table is empty.")
                return

            # Process data
            df["ts"] = pd.to_datetime(
                df["_begin_time"], unit="ms", utc=True
            ).dt.tz_convert(datetime.now().astimezone().tzinfo)
            df["date"] = df["ts"].dt.date
            df["hour"] = df["ts"].dt.hour
            df["month"] = df["ts"].dt.strftime('%Y-%m')
            df["year"] = df["ts"].dt.year

            # Aggregate data
            self.df = df
            self.hourly = self.df.groupby(["date", "hour"])["_steps"].sum()
            self.daily = self.df.groupby("date")["_steps"].sum()
            self.monthly = self.df.groupby("month")["_steps"].sum()
            self.yearly = self.df.groupby("year")["_steps"].sum()
            self.available_dates = sorted(self.daily.index)
            log.info("Data processing complete.")
        except Exception as e:
            log.error(f"Error processing database: {e}")
            self.__init__(None)  # Reset data on failure


class DataWorker(QObject):
    """Worker thread for loading data asynchronously."""

    finished = pyqtSignal(DataManager)
    error = pyqtSignal(str)

    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path

    def run(self):
        try:
            data_manager = DataManager(self.db_path)
            data_manager.load_and_process()
            self.finished.emit(data_manager)
        except Exception as e:
            self.error.emit(str(e))
