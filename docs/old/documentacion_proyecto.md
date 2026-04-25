# Documentación Técnica - PPIMultiverse (Multiverse Anime Store)

## 📋 Índice
1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Tecnologías Utilizadas](#tecnologías-utilizadas)
4. [Diseño de Base de Datos](#diseño-de-base-de-datos)
5. [Modelo Lógico](#modelo-lógico)
6. [Modelo Físico](#modelo-físico)
7. [Sistemas Avanzados](#sistemas-avanzados)
8. [Frontend y UX](#frontend-y-ux)

---

## 🎯 Descripción del Proyecto

**PPIMultiverse (Multiverse Anime Store)** es una plataforma de e-commerce especializada en productos de anime y cultura japonesa. El sistema permite la gestión completa de ventas, inventario, usuarios y reportes, con un enfoque en la experiencia del cliente y la trazabilidad de operaciones.

**Objetivos principales:**
- Gestión de catálogo de productos de anime (figuras, manga, ropa, accesorios)
- Sistema de pedidos y carrito de compras
- Control de inventario y alertas de stock bajo
- Sistema de permisos y roles granular
- Auditoría automática de operaciones
- Reportes dinámicos y análisis de ventas

---

## 🏗️ Arquitectura del Sistema

### **Arquitectura en 3 Capas**

```
┌─────────────────────────────────────────────┐
│            CAPA DE PRESENTACIÓN             │
│  ┌─────────────────────────────────────┐    │
│  │   Django Templates (HTML/CSS/JS)    │    │
│  │  • Bootstrap 5 + CSS Custom         │    │
│  │  • Templates dinámicos              │    │
│  │  • Responsive Design                │    │
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│            CAPA DE LÓGICA DE NEGOCIO        │
│  ┌─────────────────────────────────────┐    │
│  │        Django Framework             │    │
│  │  • Models (ORM)                     │    │
│  │  • Views (Controladores)            │    │
│  │  • Forms (Validación)               │    │
│  │  • URLs (Enrutamiento)              │    │
│  └─────────────────────────────────────┘    │
├─────────────────────────────────────────────┤
│            CAPA DE DATOS                    │
│  ┌─────────────────────────────────────┐    │
│  │      PostgreSQL 16 + PL/pgSQL       │    │
│  │  • Tablas relacionales              │    │
│  │  • Triggers para auditoría          │    │
│  │  • Funciones almacenadas            │    │
│  │  • Consultas dinámicas              │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### **Flujo de Datos**
```
Usuario → Frontend (Django Templates) → Views → Models → PostgreSQL
       ←           Respuesta HTML        ←      ←       ← (Triggers/Funciones)
```

---

## 🛠️ Tecnologías Utilizadas

### **Backend**
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.12.3 | Lenguaje principal |
| **Django** | 5.2.6 | Framework web |
| **Psycopg2** | 2.9.9 | Adaptador PostgreSQL |
| **OracleDB** | 3.3.0 | (Legacy) Soporte Oracle |
| **OpenPyXL** | 3.1.5 | Exportación Excel |
| **xlrd** | 2.0.1 | Importación Excel legacy |

### **Base de Datos**
| Tecnología | Versión | Características |
|------------|---------|-----------------|
| **PostgreSQL** | 16.13 | SGBD principal |
| **PL/pgSQL** | - | Lógica en base de datos |
| **JSON Support** | ✓ | Auditoría estructurada |
| **Triggers** | ✓ | Automatización |
| **Foreign Keys** | ✓ | Integridad referencial |

### **Frontend**
| Tecnología | Propósito |
|------------|-----------|
| **HTML5** | Estructura semántica |
| **CSS3** | Estilos y diseño |
| **JavaScript** | Interactividad |
| **Bootstrap 5** | Framework CSS |
| **Django Templates** | Renderizado dinámico |

### **Herramientas de Desarrollo**
| Herramienta | Uso |
|-------------|-----|
| **Git** | Control de versiones |
| **GitHub** | Repositorio remoto |
| **Virtualenv** | Entornos aislados |
| **pip** | Gestión de dependencias |
| **PostgreSQL CLI** | Administración BD |

---

## 🗄️ Diseño de Base de Datos

### **Modelo Lógico (Diagrama Entidad-Relación)**

```
                     ┌─────────────────┐
                     │    USUARIOS     │
                     ├─────────────────┤
                     │ • id_usuario (PK)│
                     │ • nombre        │
                     │ • apellidos     │
                     │ • fecha_nacimiento│
                     │ • password_hash │
                     │ • id_sexo (FK)  │
                     │ • id_perfil (FK)│
                     └────────┬────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
┌─────────▼─────────┐ ┌──────▼──────┐ ┌──────────▼──────────┐
│     CONTACTOS     │ │   SEXOS     │ │      PERFILES       │
├───────────────────┤ ├─────────────┤ ├─────────────────────┤
│ • id_contacto (PK)│ │ • id_sexo (PK)│ │ • id_perfil (PK)   │
│ • id_usuario (FK) │ │ • nombre_sexo│ │ • nombre           │
│ • tipo_contacto(FK)│ └─────────────┘ │ • descripcion      │
│ • dato_contacto   │                 │ • rol_id (FK)      │
└─────────┬─────────┘                 └──────────┬─────────┘
          │                                      │
┌─────────▼─────────┐                 ┌──────────▼─────────┐
│ CONFIG_CONTACTO   │                 │       ROLES        │
├───────────────────┤                 ├─────────────────────┤
│ • id_regla (PK)   │                 │ • id_rol (PK)      │
│ • nombre_contacto │                 │ • nombre           │
│ • regex_val       │                 │ • descripcion      │
│ • min/max_length  │                 └─────────────────────┘
│ • mensaje_error   │
└───────────────────┘

                     ┌─────────────────┐
                     │    PRODUCTOS    │
                     ├─────────────────┤
                     │ • prod_id (PK)  │
                     │ • cat_id (FK)   │
                     │ • prod_nombre   │
                     │ • prod_descripcion│
                     │ • prod_precio_venta│
                     │ • prod_stock    │
                     │ • prod_imagen_url│
                     │ • prod_descuento│
                     └────────┬────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
┌─────────▼─────────┐ ┌──────▼──────┐ ┌──────────▼──────────┐
│     CATEGORIA     │ │   PEDIDOS   │ │ PEDIDOS_PRODUCTOS   │
├───────────────────┤ ├─────────────┤ ├─────────────────────┤
│ • cat_id (PK)     │ │ • ped_id (PK)│ │ • ped_id (PK/FK)   │
│ • cat_nombre      │ │ • usu_id (FK)│ │ • prod_id (PK/FK)  │
│ • cat_descripcion │ │ • ped_fecha_pedido│ │ • pped_cantidad   │
└───────────────────┘ │ • ped_total  │ │ • pped_precio_unitario│
                      │ • ped_estado(FK)│ │ • pped_descuento   │
                      │ • ped_direccion_envio│ │ • pped_total     │
                      │ • ped_notas   │ │ • pped_estado (FK) │
                      └──────┬────────┘ └─────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   ESTADOPEDIDOS  │
                    ├──────────────────┤
                    │ • est_id (PK)    │
                    │ • est_nombre     │
                    └──────────────────┘
```

### **Modelo Físico (Implementación PostgreSQL)**

#### **Tabla: USUARIOS**
```sql
CREATE TABLE usuarios (
    id_usuario VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(300),
    primer_apellido VARCHAR(50),
    segundo_apellido VARCHAR(50),
    fecha_nacimiento DATE,
    password_hash VARCHAR(255),
    usuario_id_sexo INTEGER REFERENCES sexos(id_sexo),
    usuario_id_perfil INTEGER REFERENCES perfiles(id_perfil),
    activo SMALLINT DEFAULT 1
);
```

#### **Tabla: PRODUCTOS**
```sql
CREATE TABLE productos (
    prod_id VARCHAR(10) PRIMARY KEY,
    cat_id VARCHAR(10) NOT NULL REFERENCES categoria(cat_id),
    prod_nombre VARCHAR(100) NOT NULL,
    prod_descripcion VARCHAR(400) NOT NULL,
    prod_precio_venta NUMERIC(10,2) NOT NULL,
    prod_stock INTEGER NOT NULL,
    prod_imagen_url VARCHAR(500),
    prod_descuento NUMERIC(4,2) DEFAULT 0.0 NOT NULL
);
```

#### **Tabla: PEDIDOS**
```sql
CREATE TABLE pedidos (
    ped_id INTEGER PRIMARY KEY,
    usu_id VARCHAR(50) NOT NULL REFERENCES usuarios(id_usuario),
    ped_fecha_pedido DATE NOT NULL,
    ped_total NUMERIC(10,2) DEFAULT 0 NOT NULL,
    ped_estado INTEGER REFERENCES estadopedidos(est_id),
    ped_direccion_envio VARCHAR(200) NOT NULL,
    ped_notas VARCHAR(200)
);
```

#### **Tabla: PEDIDOS_PRODUCTOS (Tabla de relación N:M)**
```sql
CREATE TABLE pedidos_productos (
    ped_id INTEGER REFERENCES pedidos(ped_id),
    prod_id VARCHAR(10) REFERENCES productos(prod_id),
    pped_cantidad INTEGER NOT NULL,
    pped_fecha_entrega DATE,
    pped_precio_unitario NUMERIC(10,2) NOT NULL,
    pped_descuento NUMERIC(4,2) DEFAULT 0.0 NOT NULL,
    pped_total NUMERIC(10,2) NOT NULL,
    pped_estado INTEGER NOT NULL REFERENCES estadopedidos(est_id),
    PRIMARY KEY (ped_id, prod_id)
);
```

#### **Tabla: CONSULTAS_DINAMICAS (Metadatos de reportes)**
```sql
CREATE TABLE consultas_dinamicas (
    cons_id INTEGER PRIMARY KEY,
    cons_nombre VARCHAR(50) UNIQUE NOT NULL,
    cons_sql TEXT NOT NULL,
    cons_descripcion VARCHAR(200)
);
```

#### **Tabla: PRODUCTOS_AUDITORIA (Log de cambios)**
```sql
CREATE TABLE productos_auditoria (
    creation_date TIMESTAMP,
    au_type INTEGER,
    auditoria TEXT  -- JSON con cambios
);
```

### **Relaciones y Restricciones**

#### **Claves Foráneas Implementadas:**
```sql
-- Usuarios → Sexos y Perfiles
ALTER TABLE usuarios ADD CONSTRAINT fk_usuario_sexo 
    FOREIGN KEY (usuario_id_sexo) REFERENCES sexos(id_sexo);
ALTER TABLE usuarios ADD CONSTRAINT fk_usuario_perfil 
    FOREIGN KEY (usuario_id_perfil) REFERENCES perfiles(id_perfil);

-- Productos → Categoría
ALTER TABLE productos ADD CONSTRAINT fk_producto_categoria 
    FOREIGN KEY (cat_id) REFERENCES categoria(cat_id);

-- Pedidos → Usuarios y Estados
ALTER TABLE pedidos ADD CONSTRAINT fk_pedido_usuario 
    FOREIGN KEY (usu_id) REFERENCES usuarios(id_usuario);
ALTER TABLE pedidos ADD CONSTRAINT fk_pedido_estado 
    FOREIGN KEY (ped_estado) REFERENCES estadopedidos(est_id);

-- Sistema de Permisos
ALTER TABLE perfilpermisos ADD CONSTRAINT fk_perfperm_perfil 
    FOREIGN KEY (perfil_id) REFERENCES perfiles(id_perfil);
ALTER TABLE perfilpermisos ADD CONSTRAINT fk_perfperm_mod 
    FOREIGN KEY (mod_id) REFERENCES modulos(id_mod);
```

### **Tipos de Datos Utilizados**

| Tipo PostgreSQL | Uso | Ejemplo |
|-----------------|-----|---------|
| `VARCHAR(n)` | Texto de longitud variable | `VARCHAR(50)` para nombres |
| `INTEGER` | Números enteros | IDs, contadores |
| `NUMERIC(p,s)` | Números decimales precisos | `NUMERIC(10,2)` para precios |
| `DATE` | Fechas sin hora | Fecha de nacimiento |
| `TIMESTAMP` | Fecha y hora | Auditoría |
| `TEXT` | Texto largo ilimitado | Descripciones, SQL |
| `BOOLEAN` | Valores verdadero/falso | Estado activo |
| `JSON` | Datos estructurados | Auditoría de cambios |

---

## ⚙️ Sistemas Avanzados

### **1. Sistema de Triggers para Auditoría**

```sql
-- Trigger que captura cambios en productos
CREATE TRIGGER tg_auditoria_productos
BEFORE INSERT OR UPDATE OR DELETE ON productos
FOR EACH ROW EXECUTE FUNCTION tg_auditoria_productos_fn();

-- Función del trigger (guarda cambios como JSON)
CREATE OR REPLACE FUNCTION tg_auditoria_productos_fn()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO productos_auditoria VALUES (
            NOW(), 1,
            json_build_object('accion','INSERT','producto',row_to_json(NEW))::text
        );
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO productos_auditoria VALUES (
            NOW(), 2,
            json_build_object('accion','UPDATE','old',row_to_json(OLD),'new',row_to_json(NEW))::text
        );
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO productos_auditoria VALUES (
            NOW(), 3,
            json_build_object('accion','DELETE','producto',row_to_json(OLD))::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### **2. Funciones Almacenadas PL/pgSQL**

#### **Función para Estado de Pedidos:**
```sql
CREATE OR REPLACE FUNCTION fn_estado_pedido(p_ped_id INTEGER)
RETURNS TEXT AS $$
DECLARE
    v_min_estado INTEGER;
    v_max_estado INTEGER;
    v_count_entregados INTEGER;
BEGIN
    SELECT MIN(pped_estado), MAX(pped_estado),
           SUM(CASE WHEN pped_estado = 10 THEN 1 ELSE 0 END)
    INTO v_min_estado, v_max_estado, v_count_entregados
    FROM pedidos_productos WHERE ped_id = p_ped_id;
    
    IF v_min_estado IS NULL THEN RETURN 'Sin productos'; END IF;
    IF v_min_estado = v_max_estado THEN
        RETURN (SELECT est_nombre FROM estadopedidos WHERE est_id = v_min_estado);
    END IF;
    IF v_count_entregados > 0 THEN RETURN 'Parcialmente entregado'; END IF;
    RETURN (SELECT est_nombre FROM estadopedidos WHERE est_id = v_min_estado);
END;
$$ LANGUAGE plpgsql;
```

#### **Función para Reportes Dinámicos:**
```sql
CREATE OR REPLACE FUNCTION fn_ejecutar_reporte(p_id_consulta INTEGER)
RETURNS REFCURSOR AS $$
DECLARE
    v_sql_text TEXT;
    v_cursor REFCURSOR;
BEGIN
    SELECT cons_sql INTO v_sql_text
    FROM consultas_dinamicas WHERE cons_id = p_id_consulta;
    
    IF v_sql_text IS NULL THEN
        RAISE EXCEPTION 'El reporte con ID % no existe', p_id_consulta;
    END IF;
    
    OPEN v_cursor FOR EXECUTE v_sql_text;
    RETURN v_cursor;
END;
$$ LANGUAGE plpgsql;
```

### **3. Consultas Dinámicas Predefinidas**

```sql
-- Reporte 1: Productos con bajo stock
INSERT INTO consultas_dinamicas VALUES (
    1, 'TOP_BAJO_STOCK',
    'SELECT p.prod_nombre, c.cat_nombre, p.prod_stock, p.prod_precio_venta
     FROM productos p JOIN categoria c ON p.cat_id = c.cat_id
     WHERE p.prod_stock < 20 ORDER BY p.prod_stock ASC LIMIT 5',
    'Muestra los 5 productos con menor inventario.'
);

-- Reporte 2: Ventas por categoría
INSERT INTO consultas_dinamicas VALUES (
    2, 'VENTAS_POR_CATEGOR