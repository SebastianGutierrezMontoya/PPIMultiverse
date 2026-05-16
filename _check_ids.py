import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print('=== sqlite_sequence table ===')
cursor.execute('SELECT * FROM sqlite_sequence')
rows = cursor.fetchall()
for row in rows:
    print(f'{row[0]}: last_id={row[1]}')

print()
print('=== User tables and their PK columns ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'django_%' AND name NOT LIKE 'auth_%' ORDER BY name")
tables = [r[0] for r in cursor.fetchall()]
for t in tables:
    print(t)

print()
print('=== CREATE TABLE statements ===')
for t in tables:
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{t}'")
    sql = cursor.fetchone()
    if sql:
        print(f'--- {t} ---')
        print(sql[0])
        print()

# Now check max IDs for tables with integer PKs
print()
print('=== Max IDs for tables with integer PKs ===')
max_queries = {
    'Sexos': 'id_sexo',
    'Roles': 'id_rol',
    'Perfiles': 'id_perfil',
    'Modulos': 'id_mod',
    'EstadoPedidos': 'est_id',
    'Pedidos': 'ped_id',
    'Config_Contacto': 'id_regla',
    'Contactos': 'id_contacto',
    'Consultas_Dinamicas': 'cons_id',
    'Productos_Auditoria': 'dummy_id',
}
for table, pk_col in max_queries.items():
    cursor.execute(f'SELECT COALESCE(MAX({pk_col}), 0) FROM {table}')
    max_id = cursor.fetchone()[0]
    # Get row count too
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'{table}.{pk_col}: max_id={max_id}, row_count={count}')

conn.close()
