"""PostgreSQL history. Failed turns are atomic and never leave half a response."""

from uuid import UUID, uuid4

from psycopg.types.json import Jsonb


class MissingSession(Exception):
    pass


class BusySession(Exception):
    pass


def lock_session(connection, session_id):
    # Nonblocking, transaction-scoped cross-process lock. Same session cannot race.
    locked = connection.execute(
        "SELECT pg_try_advisory_xact_lock(hashtextextended(%s,760076)) AS locked",
        (str(session_id),),
    ).fetchone()["locked"]
    if not locked:
        raise BusySession()


def get_session(connection, session_id):
    row = connection.execute(
        "SELECT id,title,created_at,updated_at FROM series76.conversations WHERE id=%s",
        (session_id,),
    ).fetchone()
    if row is None:
        raise MissingSession()
    return row


def list_sessions(connection, limit=50, offset=0):
    return connection.execute(
        """SELECT c.id,c.title,c.created_at,c.updated_at,
        COALESCE((SELECT left(m.content,180) FROM series76.messages m
          WHERE m.session_id=c.id AND m.role='assistant' ORDER BY m.sequence DESC LIMIT 1),'') AS preview
        FROM series76.conversations c ORDER BY c.updated_at DESC,c.id LIMIT %s OFFSET %s""", (limit, offset)
    ).fetchall()


def history(connection, session_id, limit=100, before=None, *, internal=False):
    columns = "id,role,content,products,created_at,sequence"
    if internal:
        columns += ",context"
    rows = connection.execute(
        f"""SELECT {columns} FROM series76.messages WHERE session_id=%s
        AND (%s::bigint IS NULL OR sequence < %s)
        ORDER BY sequence DESC LIMIT %s""", (session_id, before, before, limit)
    ).fetchall()
    return list(reversed(rows))


def recent_context(connection, session_id):
    row = connection.execute(
        """SELECT context FROM series76.messages
        WHERE session_id=%s AND role='assistant' ORDER BY sequence DESC LIMIT 1""",
        (session_id,),
    ).fetchone()
    return row["context"] if row else {}


def append_turn(connection, session_id, query, result, *, new=False):
    if new:
        connection.execute(
            "INSERT INTO series76.conversations(id,title) VALUES (%s,%s)",
            (session_id, " ".join(query.split())[:100]),
        )
    answer_id = uuid4()
    for role, content, products, traces, context, identifier in (
        ("user", query, [], [], {}, uuid4()),
        ("assistant", result.answer, result.products, result.tool_calls, result.context, answer_id),
    ):
        connection.execute(
            """INSERT INTO series76.messages
            (id,session_id,role,content,products,tool_calls,context)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (identifier, session_id, role, content, Jsonb(products), Jsonb(traces), Jsonb(context)),
        )
    connection.execute(
        "UPDATE series76.conversations SET updated_at=clock_timestamp() WHERE id=%s", (session_id,)
    )
    return answer_id


def debug_for_message(connection, message_id: UUID):
    return connection.execute(
        """SELECT id AS message_id,session_id,tool_calls FROM series76.messages
        WHERE id=%s AND role='assistant'""", (message_id,)
    ).fetchone()
