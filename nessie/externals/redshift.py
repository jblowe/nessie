"""
Copyright ©2018. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""


"""Client code to run queries against Redshift."""


from datetime import datetime

from flask import current_app as app
from nessie.lib.db import get_psycopg_cursor
import psycopg2
import psycopg2.extras
import psycopg2.sql


def execute(sql, **kwargs):
    """Execute SQL write operation with optional keyword arguments for formatting, returning a status string."""
    return _execute(sql, 'write', **kwargs)


def execute_ddl_script(sql):
    """Handle Redshift DDL scripts, which are exceptional in a number of ways.

    * CREATE EXTERNAL SCHEMA must be executed separately from any later references to that schema.
      The simplest way to enforce that requirement is to split the multi-statement SQL string by semicolon,
      and execute each statement in turn.
    * DROP EXTERNAL TABLE and CREATE EXTERNAL TABLE will fail with a 'cannot run inside a transaction block'
      message unless autocommit is enabled.

    WARNING: This will break horribly if a semicolon terminated statement is inside a block quote.
    """
    statements = sql.split(';')
    # Remove any trailing debris after the last SQL statement.
    del statements[-1]
    for index, statement in enumerate(statements):
        app.logger.info(f'Executing DDL script {index + 1} of {len(statements)}')
        result = execute(statement)
        if not result:
            app.logger.error('Error executing statement from DDL script; aborting remainder of script.')
            return False
    return True


def drop_external_schema(schema_name):
    app.logger.info(f'Dropping external schema {schema_name}')
    sql = f'SELECT * FROM SVV_EXTERNAL_TABLES WHERE SCHEMANAME=\'{schema_name}\''
    results = fetch(sql)
    if results:
        def _get_tablename(r):
            # We tolerate both dict and object when parsing result row
            return r['tablename'] if 'tablename' in r else r.tablename

        tables = [_get_tablename(r) for r in results]
        for table in tables:
            sql = f'DROP TABLE {schema_name}.{table} CASCADE'
            execute(sql)
    sql = f'DROP SCHEMA IF EXISTS {schema_name}'
    execute(sql)


def fetch(sql, **kwargs):
    """Execute SQL read operation with optional keyword arguments for formatting, returning an array of dictionaries."""
    rows = _execute(sql, 'read', **kwargs)
    if rows is None:
        return None
    else:
        # For Pandas compatibility, copy psycopg's list-like object of dict-like objects to a real list of dicts.
        return [r.copy() for r in rows]


def _execute(sql, operation, **kwargs):
    """Execute SQL string with optional keyword arguments for formatting.

    If 'operation' is set to 'write', a transaction is enforced and a status string is returned. If 'operation' is
    set to 'read', results are returned as an array of named tuples.
    """
    result = None
    try:
        params = None
        if kwargs:
            params = kwargs.pop('params', None)
            sql = psycopg2.sql.SQL(sql).format(**kwargs)
        with get_psycopg_cursor(
                operation=operation,
                dbname=app.config.get('REDSHIFT_DATABASE'),
                host=app.config.get('REDSHIFT_HOST'),
                port=app.config.get('REDSHIFT_PORT'),
                user=app.config.get('REDSHIFT_USER'),
                password=app.config.get('REDSHIFT_PASSWORD'),
        ) as cursor:
            ts = datetime.now().timestamp()
            cursor.execute(sql, params)
            if operation == 'read':
                result = [row for row in cursor]
                query_time = datetime.now().timestamp() - ts
                app.logger.debug(f'Redshift query returned {len(result)} rows in {query_time} seconds:\n{sql}\n{params or ""}')
            else:
                result = cursor.statusmessage
                query_time = datetime.now().timestamp() - ts
                app.logger.debug(f'Redshift query returned status {result} in {query_time} seconds:\n{sql}\n{params or ""}')
    except psycopg2.Error as e:
        error_str = str(e)
        if e.pgcode:
            error_str += f'{e.pgcode}: {e.pgerror}\n'
        error_str += f'on SQL: {sql}'
        app.logger.warn({'message': error_str})
    return result
