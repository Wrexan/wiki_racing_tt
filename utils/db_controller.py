import psycopg2


def create_page_names_table(conn_source, table_name: str):
    table_exist = is_table_exist(conn_source=conn_source, table_name=table_name)
    if table_exist:
        conn_source.cursor.execute(f'CREATE TABLE {table_name} (\
                page_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,\
                page_name VARCHAR(128) NOT NULL,\
                page_link VARCHAR(256) NOT NULL\
        )')


def create_page_relations_table(conn_source, page_table_name: str):
    relation_table_name = f'{page_table_name}_relations'
    table_exist = is_table_exist(conn_source=conn_source, table_name=relation_table_name)
    if table_exist:
        conn_source.cursor.execute(f'CREATE TABLE {page_table_name} (\
                parent_id INTEGER NOT NULL,\
                child_id INTEGER,\
                FOREIGN KEY (parent_id)\
                    REFERENCES {page_table_name} (page_id)\
                    ON UPDATE CASCADE ON DELETE CASCADE,\
                FOREIGN KEY (child_id)\
                    REFERENCES {page_table_name} (page_id)\
                    ON UPDATE CASCADE ON DELETE CASCADE,\
                UNIQUE (parent_id, child_id)\
        )')
    conn_source.connection.commit()


def is_table_exist(conn_source, table_name: str):
    conn_source.cursor.execute(f"SELECT EXISTS("
                               f"SELECT relname FROM pg_class "
                               f"WHERE relname = '{table_name}');")
    return conn_source.cursor.fetchone()[0]
