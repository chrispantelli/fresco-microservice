from datetime import datetime, timezone
from typing import Any

import ulid


def insert_generated_report(conn, *, type: str, related_to: str, pdf_url: str, date_from: str, date_to: str):
    """
    Synchronous insert using psycopg2.
    """
    report_id = str(ulid.new())
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tblgeneratedreports (
                id,
                type,
                related_to,
                pdf_url,
                date_to,
                date_from
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                report_id,
                type,
                related_to,
                pdf_url,
                date_to,
                date_from
            ),
        )
        return cursor.fetchone()[0]