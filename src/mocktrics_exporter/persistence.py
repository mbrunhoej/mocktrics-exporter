import logging
import sqlite3
from typing import cast

from mocktrics_exporter import valueModels
from mocktrics_exporter.metrics import Metric


class Persistence:

    def __init__(self, database: str) -> None:
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self._connection.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self._ensure_tables()
        self._ensure_indicies()

    def add_metric(self, metric: Metric):
        logging.info(f"Adding metric {metric.name} to database")
        try:
            with self._connection:
                self.cursor.execute(
                    """
                INSERT INTO metrics (name, documentation, unit)
                VALUES (?, ?, ?)
                """,
                    (metric.name, metric.documentation, metric.unit),
                )
                metric_id = self.cursor.lastrowid
                assert metric_id is not None

                for label in metric.labels:

                    self.cursor.execute(
                        """
                    INSERT INTO metric_labels (name, metric_id)
                    VALUES (?, ?)
                    """,
                        (label, metric_id),
                    )

                for value in metric.values:
                    self.add_metric_value(value, metric_id)

        except sqlite3.IntegrityError as e:

            metrics = self.get_metrics()
            if metric in metrics:
                logging.debug(f"Metric {metric.name} already exists in database")
            else:
                raise e

    def get_metric_id(self, name: str) -> int:
        with self._connection:
            id = self.cursor.execute(
                """
            SELECT id FROM metrics WHERE name = ?
            """,
                (name),
            ).fetchone()

        return id

    def get_metrics(self) -> list[Metric]:

        result = []

        with self._connection:
            metrics = self.cursor.execute(
                """
            SELECT
                m.id,
                m.name,
                m.documentation,
                m.unit,
                GROUP_CONCAT(ml.name, ', ') AS labels
            FROM metrics AS m
            LEFT JOIN metric_labels AS ml
                ON ml.metric_id = m.id
            GROUP BY m.id;
            """
            )

            for metric in metrics.fetchall():

                kinds = self.cursor.execute(
                    """
                SELECT
                    v.id,
                    v.kind,
                    GROUP_CONCAT(vl.label, ', ') AS labels
                FROM value_base AS v
                LEFT JOIN value_labels AS vl
                    ON vl.value_id = v.id
                WHERE v.metric_id = ?
                GROUP BY v.id;
                """,
                    (metric[0],),
                ).fetchall()

                values: list[valueModels.MetricValue] = []

                for kind in kinds:

                    value = self.cursor.execute(
                        f"""
                    SELECT * FROM {kind[1]} WHERE id = ?
                    """,
                        (kind[0],),
                    ).fetchall()[0]

                    match kind[1]:
                        case "static":
                            v = valueModels.StaticValue(
                                kind=kind[1], value=value[1], labels=kind[2].split(", ")
                            )
                        case "ramp":
                            v = valueModels.RampValue(
                                kind=kind[1],
                                period=value[1],
                                peak=value[2],
                                offset=value[3],
                                invert=bool(value[4]),
                                labels=kind[2].split(", "),
                            )
                        case "square":
                            v = valueModels.SquareValue(
                                kind=kind[1],
                                period=value[1],
                                magnitude=value[2],
                                offset=value[3],
                                duty_cycle=value[4],
                                invert=bool(value[5]),
                                labels=kind[2].split(", "),
                            )
                        case "sine":
                            v = valueModels.SineValue(
                                kind=kind[1],
                                period=value[1],
                                amplitude=value[2],
                                offset=value[3],
                                labels=kind[2].split(", "),
                            )
                        case "gaussian":
                            v = valueModels.GaussianValue(
                                kind=kind[1],
                                mean=value[1],
                                sigma=value[2],
                                labels=kind[2].split(", "),
                            )

                    values.append(v)

                result.append(
                    Metric(
                        name=metric[1],
                        documentation=metric[2],
                        unit=metric[3],
                        values=values,
                        labels=metric[4].split(", "),
                    )
                )

        return result

    def delete_metric(self, metric: Metric):
        logging.info(f"Deleting metric {metric.name} from database")
        with self._connection:
            self.cursor.execute(
                """
            DELETE FROM metrics
            WHERE name = ?
            """,
                (metric.name,),
            )
            metric_id = self.cursor.lastrowid
            assert metric_id is not None

    def add_metric_value(self, value: valueModels.MetricValue, metric_id: int):

        with self._connection:
            self.cursor.execute(
                """
            INSERT INTO value_base (kind, metric_id)
            VALUES (?, ?)
            """,
                (value.kind, metric_id),
            )
            value_id = self.cursor.lastrowid

            for label in value.labels:

                self.cursor.execute(
                    """
                INSERT INTO value_labels (label, value_id)
                VALUES (?, ?)
                """,
                    (label, value_id),
                )

            match value.kind:
                case "static":
                    val = cast(valueModels.StaticValue, value)
                    self.cursor.execute(
                        """
                    INSERT INTO static (value, id)
                    VALUES (?, ?)
                    """,
                        (val.value, value_id),
                    )

                case "ramp":
                    val = cast(valueModels.RampValue, value)
                    self.cursor.execute(
                        """
                    INSERT INTO ramp (period, peak, offset, invert, id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                        (val.period, val.peak, val.offset, val.invert, value_id),
                    )

                case "square":
                    val = cast(valueModels.SquareValue, value)
                    self.cursor.execute(
                        """
                    INSERT INTO square (period, magnitude, offset, duty_cycle, offset, invert, id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            val.period,
                            val.magnitude,
                            val.offset,
                            val.duty_cycle,
                            val.offset,
                            val.invert,
                            value_id,
                        ),
                    )

                case "sine":
                    val = cast(valueModels.SineValue, value)
                    self.cursor.execute(
                        """
                    INSERT INTO sine (period, amplitude, offset, offset, id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                        (val.period, val.amplitude, val.offset, val.offset, value_id),
                    )

                case "gaussian":
                    val = cast(valueModels.GaussianValue, value)
                    self.cursor.execute(
                        """
                    INSERT INTO gaussian (mean, sigma, id)
                    VALUES (?, ?)
                    """,
                        (val.mean, val.sigma, value_id),
                    )

    def delete_metric_value(self, metric: Metric, value: valueModels.MetricValue):
        logging.info(f"Deleting value from database")

        with self._connection:

            id = self.get_metric_id(metric.name)

            db_values = self.cursor.execute(
                """
            SELECT
                v.id,
                GROUP_CONCAT(vl.name, ', ') AS labels
            FROM value_base as v
            LEFT JOIN value_labels AS vl
                ON vl.value_id = m.id
            WHERE metric_id = ?
            """,
                (id,),
            ).fetchall()

            for db_v in db_values:

                if all([value.labels in v for v in db_v[1].split(", ")]):

                    self.cursor.execute(
                        """
                    DELETE FROM value_base
                    WHERE id = ?
                    """,
                        (db_v[0],),
                    )
            metric_id = self.cursor.lastrowid
            assert metric_id is not None

    def _ensure_tables(self) -> None:

        logging.info('Ensuring table "metrics"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            documentation TEXT NOT NULL,
            unit TEXT NOT NULL
            
        )
        """
        )

        logging.info('Ensuring table "metric_labels"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS metric_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            metric_id INT NOT NULL,
            UNIQUE (metric_id, name),
            FOREIGN KEY (metric_id)
                REFERENCES metrics(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
        )
        """
        )

        logging.info('Ensuring table "value_base"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS value_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_id INT NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('static','ramp','square','sine','gaussian')),
            FOREIGN KEY (metric_id)
                REFERENCES metrics(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
        )
        """
        )

        logging.info('Ensuring table "value_labels"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS value_labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            value_id INT NOT NULL,
            FOREIGN KEY (value_id)
                REFERENCES value_base(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
        )
        """
        )

        logging.info('Ensuring table "static"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS static (
            id INTEGER PRIMARY KEY REFERENCES value_base(id) ON DELETE CASCADE ON UPDATE CASCADE,
            value REAL NOT NULL
        )
        """
        )

        logging.info('Ensuring table "ramp"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS ramp (
            id INTEGER PRIMARY KEY REFERENCES value_base(id) ON DELETE CASCADE ON UPDATE CASCADE,
            period INT NOT NULL,
            peak INT NOT NULL,
            offset INT NOT NULL,
            invert INTEGER NOT NULL CHECK (invert IN (0,1))
        )
        """
        )

        logging.info('Ensuring table "square"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS square (
            id INTEGER PRIMARY KEY REFERENCES value_base(id) ON DELETE CASCADE ON UPDATE CASCADE,
            period INT NOT NULL,
            magnitude INT NOT NULL,
            offset INT NOT NULL,
            duty_cycle REAL NOT NULL,
            invert INTEGER NOT NULL CHECK (invert IN (0,1))
        )
        """
        )

        logging.info('Ensuring table "sine"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS sine (
            id INTEGER PRIMARY KEY REFERENCES value_base(id) ON DELETE CASCADE ON UPDATE CASCADE,
            period INT NOT NULL,
            amplitude INT NOT NULL,
            offset INT NOT NULL
        )
        """
        )

        logging.info('Ensuring table "gaussian"')
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS gaussian (
            id INTEGER PRIMARY KEY REFERENCES value_base(id) ON DELETE CASCADE ON UPDATE CASCADE,
            mean INT NOT NULL,
            sigma REAL NOT NULL
        )
        """
        )

        self._connection.commit()

    def _ensure_indicies(self) -> None:
        ...
        # self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_metric_name ON metric(name);")

        # self._connection.commit()


database = Persistence("mocktrics-exporter.db")
