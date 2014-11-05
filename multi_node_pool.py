import re
import sys
from sqlalchemy import pool
from sqlalchemy import util
from sqlalchemy import exc

class MultiNodeConnectionPool(pool._DBProxy):
    def __init__(self, **kw):
        pool._DBProxy.__init__(self, self)
        self.nodes = []

    def connect(self, *cargs, **cparams):
        try:
            pool = self.get_pool(*cargs, **cparams)
            def is_healthy(conn):
                if self.run_query(conn, 
                                  ("select distinct(table_schema) from " 
                                   "information_schema.tables where " 
                                   "table_schema = 'ceilometer'")):
                    return True
                else:
                    return False

            if not self.nodes:
                conn = pool._dialect.connect(*cargs, **cparams)
                self.nodes = self.retrieve_nodes(conn)
                if not self.nodes:
                    self.nodes.append(cparams['host'])
                conn.close()

            self._conn_exception = None
            for node in self.nodes:
                cparams['host'] = node
                try:
                    conn = pool._dialect.connect(*cargs, **cparams)
                    if is_healthy(conn):
                        return conn
                except pool._dialect.dbapi.Error as e:
                    self._conn_exception = e
                    pass

            if self._conn_exception:
                raise self._conn_exception

            return None
        except pool._dialect.dbapi.Error as e:
            invalidated = pool._dialect.is_disconnect(e, None, None)
            util.raise_from_cause(
                exc.DBAPIError.instance(
                    None, None, e, pool._dialect.dbapi.Error,
                    connection_invalidated=invalidated
                ), sys.exc_info()
            )        

    def retrieve_nodes(self, conn):
        def cluster_nodes(conn):
            result = self.run_query(conn,
                                    "SHOW VARIABLES LIKE 'wsrep_cluster_address'")
            if result:
                return re.findall( r'[0-9]+(?:\.[0-9]+){3}', result)
            else:
                return []

        def local_node(conn):
            result = self.run_query(conn, 
                                    "SHOW VARIABLES LIKE 'wsrep_node_address'")
            return [result] if result else []

        return list(set(local_node(conn) + cluster_nodes(conn)))

    def run_query(self, conn, query):
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        return result
