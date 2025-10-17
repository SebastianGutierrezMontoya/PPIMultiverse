-- 1) Estado del trigger y errores
SELECT owner, object_name, status
FROM all_objects
WHERE object_type = 'TRIGGER'
  AND object_name = 'TG_AUDITORIA_PRODUCTOS';

SELECT line, text
FROM all_source
WHERE owner = 'PPIMULTIVERSE' AND name = 'TG_AUDITORIA_PRODUCTOS'
ORDER BY line;

SELECT owner, name, type, line, position, text
FROM all_errors
WHERE owner = 'PPIMULTIVERSE' AND name = 'TG_AUDITORIA_PRODUCTOS'
ORDER BY line, position;

-- 2) Intentar recompilar y mostrar errores resultantes
ALTER TRIGGER PPIMULTIVERSE.TG_AUDITORIA_PRODUCTOS COMPILE;

-- (ver nuevamente errores si los hubiera)
SELECT * FROM all_errors WHERE owner='PPIMULTIVERSE' AND name='TG_AUDITORIA_PRODUCTOS';

-- 3) Ver objetos dependientes típicos (ajusta nombres si difieren)
SELECT owner, object_name, object_type, status
FROM all_objects
WHERE object_name IN ('PRODUCTOS','PRODUCTOS_AUDITORIA', 'TG_AUDITORIA_PRODUCTOS');

-- 4) Si falta DDL del trigger, extraerlo (útil para revisar/recrear)
SET LONG 100000
SELECT dbms_metadata.get_ddl('TRIGGER','TG_AUDITORIA_PRODUCTOS','PPIMULTIVERSE') FROM dual;

-- 5) Si el trigger requiere privilegios sobre otros esquemas, conceder temporalmente (ejemplo)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON other_schema.productos_auditoria TO PPIMULTIVERSE;

-- 6) Si necesitas deshabilitar temporalmente para evitar ORA-04098 en operaciones
ALTER TRIGGER PPIMULTIVERSE.TG_AUDITORIA_PRODUCTOS DISABLE;

-- 7) Tras corregir código (o privilegios), recompilar y comprobar estado
ALTER TRIGGER PPIMULTIVERSE.TG_AUDITORIA_PRODUCTOS COMPILE;
SELECT owner, object_name, status FROM all_objects WHERE object_type='TRIGGER' AND object_name='TG_AUDITORIA_PRODUCTOS';
SELECT * FROM all_errors WHERE owner='PPIMULTIVERSE' AND name='TG_AUDITORIA_PRODUCTOS';

-- 8) Si decides recrear: drop + create (ejemplo)
-- DROP TRIGGER PPIMULTIVERSE.TG_AUDITORIA_PRODUCTOS;
-- (usar el DDL corregido obtenido por dbms_metadata.get_ddl para crear de nuevo)
