-- =======================================================
-- | Script de Creación de Base de Datos (PostgreSQL 16) |
-- |       para Multiverse Anime Store                   |
-- |  Compatible con Django 5.2 — Proyecto PPI           |
-- |  Basado en: ppi sql final.sql (Oracle → PostgreSQL) |
-- =======================================================

-- =======================================================
-- | Script de Eliminación de Tablas                     |
-- =======================================================

DROP TABLE IF EXISTS PEDIDOS_PRODUCTOS CASCADE;
DROP TABLE IF EXISTS PERFILPERMISOS CASCADE;
DROP TABLE IF EXISTS PRODUCTOS_AUDITORIA CASCADE;
DROP TABLE IF EXISTS CONTACTOS CASCADE;
DROP TABLE IF EXISTS PEDIDOS CASCADE;
DROP TABLE IF EXISTS PRODUCTOS CASCADE;
DROP TABLE IF EXISTS CATEGORIA CASCADE;
DROP TABLE IF EXISTS USUARIOS CASCADE;
DROP TABLE IF EXISTS SEXOS CASCADE;
DROP TABLE IF EXISTS PERFILES CASCADE;
DROP TABLE IF EXISTS ROLES CASCADE;
DROP TABLE IF EXISTS CONFIG_CONTACTO CASCADE;
DROP TABLE IF EXISTS ESTADOPEDIDOS CASCADE;
DROP TABLE IF EXISTS MODULOS CASCADE;
DROP TABLE IF EXISTS CONSULTAS_DINAMICAS CASCADE;

-- =======================================================
-- | Script de Creación de Tablas                        |
-- =======================================================

CREATE TABLE MODULOS (
    id_mod INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_mod VARCHAR(100) UNIQUE NOT NULL,
    url_mod VARCHAR(200) NOT NULL,
    padre_mod INTEGER,
    descripcion VARCHAR(200)
);

CREATE TABLE ROLES (
    id_rol INTEGER PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE,
    descripcion VARCHAR(255)
);

CREATE TABLE PERFILES (
    id_perfil INTEGER PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE,
    rol_id INTEGER NOT NULL,
    descripcion VARCHAR(255)
);

CREATE TABLE SEXOS (
    id_sexo INTEGER PRIMARY KEY,
    nombre_sexo VARCHAR(20) NOT NULL
);

CREATE TABLE ESTADOPEDIDOS (
    est_id INTEGER PRIMARY KEY,
    est_nombre VARCHAR(50) NOT NULL
);

CREATE TABLE CONFIG_CONTACTO (
    id_regla INTEGER PRIMARY KEY,
    nombre_contacto VARCHAR(50) NOT NULL,
    descripcion VARCHAR(100),
    regex_val VARCHAR(200),
    min_length DOUBLE PRECISION,
    max_length DOUBLE PRECISION,
    mensaje_error VARCHAR(200) NOT NULL
);

CREATE TABLE CATEGORIA (
    cat_id VARCHAR(10) PRIMARY KEY,
    cat_nombre VARCHAR(50) UNIQUE,
    cat_descripcion VARCHAR(200)
);

CREATE TABLE USUARIOS (
    id_usuario VARCHAR(50) PRIMARY KEY,
    nombre VARCHAR(300),
    primer_apellido VARCHAR(50),
    segundo_apellido VARCHAR(50),
    fecha_nacimiento DATE,
    password_hash VARCHAR(255),
    usuario_id_sexo INTEGER NOT NULL,
    usuario_id_perfil INTEGER NOT NULL,
    activo DOUBLE PRECISION DEFAULT 1
);

CREATE TABLE PRODUCTOS (
    prod_id VARCHAR(10) PRIMARY KEY,
    cat_id VARCHAR(10) NOT NULL,
    prod_nombre VARCHAR(100) NOT NULL DEFAULT 'Sin nombre',
    prod_descripcion VARCHAR(400),
    prod_precio_venta NUMERIC(10,2),
    prod_stock INTEGER,
    prod_imagen_url VARCHAR(500),
    prod_descuento NUMERIC(4,2) DEFAULT 0
);

CREATE TABLE CONTACTOS (
    id_contacto INTEGER PRIMARY KEY,
    id_usuario VARCHAR(50),
    tipo_contacto INTEGER,
    dato_contacto VARCHAR(100)
);

CREATE TABLE PEDIDOS (
    ped_id INTEGER PRIMARY KEY,
    usu_id VARCHAR(50) NOT NULL,
    ped_fecha_pedido DATE,
    ped_total NUMERIC(10,2) DEFAULT 0,
    ped_estado INTEGER DEFAULT 1 NOT NULL,
    ped_direccion_envio VARCHAR(200),
    ped_notas VARCHAR(200)
);

CREATE TABLE PERFILPERMISOS (
    perfil_id INTEGER NOT NULL,
    mod_id INTEGER NOT NULL,
    can_create CHAR(1) DEFAULT 'N' CHECK (can_create IN ('Y','N')),
    can_read   CHAR(1) DEFAULT 'Y' CHECK (can_read IN ('Y','N')),
    can_update CHAR(1) DEFAULT 'N' CHECK (can_update IN ('Y','N')),
    can_delete CHAR(1) DEFAULT 'N' CHECK (can_delete IN ('Y','N'))
);

CREATE TABLE PEDIDOS_PRODUCTOS (
    ped_id INTEGER NOT NULL,
    prod_id VARCHAR(10) NOT NULL,
    pped_cantidad INTEGER,
    pped_fecha_entrega DATE,
    pped_precio_unitario NUMERIC(10,2),
    pped_descuento NUMERIC(4,2) DEFAULT 0,
    pped_total NUMERIC(10,2) NOT NULL,
    pped_estado INTEGER
);

CREATE TABLE PRODUCTOS_AUDITORIA (
    dummy_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    creation_date DATE,
    au_type INTEGER,
    auditoria VARCHAR(500)
);

CREATE TABLE CONSULTAS_DINAMICAS (
    cons_id INTEGER PRIMARY KEY,
    cons_nombre VARCHAR(50) NOT NULL UNIQUE,
    cons_sql VARCHAR(4000) NOT NULL,
    cons_descripcion VARCHAR(200)
);

-- =======================================================
-- | Script de Constraints COMPLETO                      |
-- =======================================================

-- MODULOS
ALTER TABLE MODULOS ADD CONSTRAINT fk_modulo_padre FOREIGN KEY (padre_mod) REFERENCES MODULOS (id_mod);

-- PERFILES
ALTER TABLE PERFILES ADD CONSTRAINT fk_perfil_rol FOREIGN KEY (rol_id) REFERENCES ROLES (id_rol);

-- USUARIOS
ALTER TABLE USUARIOS ADD CONSTRAINT fk_usuario_sexo FOREIGN KEY (usuario_id_sexo) REFERENCES SEXOS (id_sexo);
ALTER TABLE USUARIOS ADD CONSTRAINT fk_usuario_perfil FOREIGN KEY (usuario_id_perfil) REFERENCES PERFILES (id_perfil);
ALTER TABLE USUARIOS ADD CONSTRAINT ck_activo_valido CHECK (activo IN (0, 1));

-- PRODUCTOS
ALTER TABLE PRODUCTOS ADD CONSTRAINT fk_producto_categoria FOREIGN KEY (cat_id) REFERENCES CATEGORIA (cat_id);
ALTER TABLE PRODUCTOS ADD CONSTRAINT ck_precio_positivo CHECK (prod_precio_venta > 0);
ALTER TABLE PRODUCTOS ADD CONSTRAINT ck_stock_no_negativo CHECK (prod_stock >= 0);
ALTER TABLE PRODUCTOS ADD CONSTRAINT ck_descuento_maximo CHECK (prod_descuento <= 99);

-- CONTACTOS
ALTER TABLE CONTACTOS ADD CONSTRAINT fk_contacto_usuario FOREIGN KEY (id_usuario) REFERENCES USUARIOS (id_usuario);
ALTER TABLE CONTACTOS ADD CONSTRAINT fk_contacto_tipo FOREIGN KEY (tipo_contacto) REFERENCES CONFIG_CONTACTO (id_regla);
ALTER TABLE CONTACTOS ADD CONSTRAINT uq_usuario_tipo_contacto UNIQUE (id_usuario, tipo_contacto);

-- PEDIDOS
ALTER TABLE PEDIDOS ADD CONSTRAINT fk_pedido_usuario FOREIGN KEY (usu_id) REFERENCES USUARIOS (id_usuario);
ALTER TABLE PEDIDOS ADD CONSTRAINT fk_pedido_estado FOREIGN KEY (ped_estado) REFERENCES ESTADOPEDIDOS (est_id);
ALTER TABLE PEDIDOS ADD CONSTRAINT ck_total_no_negativo CHECK (ped_total >= 0);

-- PERFILPERMISOS
ALTER TABLE PERFILPERMISOS ADD CONSTRAINT pk_perfil_mod PRIMARY KEY (perfil_id, mod_id);
ALTER TABLE PERFILPERMISOS ADD CONSTRAINT fk_permiso_perfil FOREIGN KEY (perfil_id) REFERENCES PERFILES (id_perfil);
ALTER TABLE PERFILPERMISOS ADD CONSTRAINT fk_permiso_modulo FOREIGN KEY (mod_id) REFERENCES MODULOS (id_mod);

-- PEDIDOS_PRODUCTOS
ALTER TABLE PEDIDOS_PRODUCTOS ADD CONSTRAINT pk_pedido_producto PRIMARY KEY (ped_id, prod_id);
ALTER TABLE PEDIDOS_PRODUCTOS ADD CONSTRAINT fk_pped_pedido FOREIGN KEY (ped_id) REFERENCES PEDIDOS (ped_id);
ALTER TABLE PEDIDOS_PRODUCTOS ADD CONSTRAINT fk_pped_producto FOREIGN KEY (prod_id) REFERENCES PRODUCTOS (prod_id);
ALTER TABLE PEDIDOS_PRODUCTOS ADD CONSTRAINT fk_pped_estado FOREIGN KEY (pped_estado) REFERENCES ESTADOPEDIDOS (est_id);

-- =======================================================
-- | Datos Iniciales (Seed Data)                         |
-- =======================================================

-- Sexos
INSERT INTO SEXOS (id_sexo, nombre_sexo) VALUES (1, 'Hombre');
INSERT INTO SEXOS (id_sexo, nombre_sexo) VALUES (2, 'Mujer');
INSERT INTO SEXOS (id_sexo, nombre_sexo) VALUES (3, 'Otro');

-- Roles
INSERT INTO ROLES (id_rol, nombre, descripcion) VALUES (1, 'Administrador', 'Acceso total al sistema');
INSERT INTO ROLES (id_rol, nombre, descripcion) VALUES (2, 'Cliente', 'Usuario comprador');

-- Perfiles
INSERT INTO PERFILES (id_perfil, nombre, descripcion, rol_id) VALUES (1, 'Admin', 'Perfil administrador con todos los permisos', 1);
INSERT INTO PERFILES (id_perfil, nombre, descripcion, rol_id) VALUES (2, 'Cliente', 'Perfil cliente con permisos básicos', 2);

-- EstadoPedidos (6 estados)
INSERT INTO ESTADOPEDIDOS (est_id, est_nombre) VALUES (1, 'Pendiente');
INSERT INTO ESTADOPEDIDOS (est_id, est_nombre) VALUES (2, 'Confirmado');
INSERT INTO ESTADOPEDIDOS (est_id, est_nombre) VALUES (3, 'En preparación');
INSERT INTO ESTADOPEDIDOS (est_id, est_nombre) VALUES (4, 'Enviado');
INSERT INTO ESTADOPEDIDOS (est_id, est_nombre) VALUES (5, 'Entregado');
INSERT INTO ESTADOPEDIDOS (est_id, est_nombre) VALUES (6, 'Cancelado');

-- Config_Contacto
INSERT INTO CONFIG_CONTACTO (id_regla, nombre_contacto, descripcion, regex_val, min_length, max_length, mensaje_error)
VALUES (1, 'Teléfono', 'Número de contacto telefónico', NULL, 7, 15, 'Teléfono inválido');

INSERT INTO CONFIG_CONTACTO (id_regla, nombre_contacto, descripcion, regex_val, min_length, max_length, mensaje_error)
VALUES (2, 'Email', 'Correo electrónico', NULL, 5, 100, 'Email inválido');

INSERT INTO CONFIG_CONTACTO (id_regla, nombre_contacto, descripcion, regex_val, min_length, max_length, mensaje_error)
VALUES (3, 'Dirección', 'Dirección física', NULL, 5, 200, 'Dirección inválida');

-- Módulos (11 módulos del panel admin)
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Categoria', '/AdminMultiverse/categorias/', 'Gestión de categorías de productos');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Productos', '/AdminMultiverse/productos/', 'Gestión de productos del catálogo');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Pedidos', '/AdminMultiverse/pedidos/', 'Gestión de pedidos de clientes');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Usuarios', '/AdminMultiverse/usuarios/', 'Gestión de usuarios del sistema');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Contactos', '/AdminMultiverse/contactos/', 'Gestión de datos de contacto');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Roles', '/AdminMultiverse/roles/', 'Gestión de roles de usuario');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Perfiles', '/AdminMultiverse/perfiles/', 'Gestión de perfiles y permisos');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Sexos', '/AdminMultiverse/sexos/', 'Gestión de sexos');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('EstadoPedidos', '/AdminMultiverse/estado_pedidos/', 'Gestión de estados de pedido');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Config_Contactos', '/AdminMultiverse/config_contacto/', 'Configuración de tipos de contacto');
INSERT INTO MODULOS (nombre_mod, url_mod, descripcion) VALUES ('Consultas', '/AdminMultiverse/consultas_dinamicas/', 'Consultas dinámicas SQL');

-- Permisos: Admin (id_perfil=1) tiene Y/Y/Y/Y en todos los módulos
INSERT INTO PERFILPERMISOS (perfil_id, mod_id, can_create, can_read, can_update, can_delete)
SELECT p.id_perfil, m.id_mod, 'Y', 'Y', 'Y', 'Y'
FROM PERFILES p, MODULOS m
WHERE p.nombre = 'Admin';

-- Usuario administrador
INSERT INTO USUARIOS (id_usuario, nombre, primer_apellido, segundo_apellido, fecha_nacimiento, password_hash, usuario_id_sexo, usuario_id_perfil, activo)
VALUES ('admin', 'Admin', 'Sistema', '', '2000-01-01'::DATE, '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 3, 1, 1);

-- =====================================================
-- CATEGORÍAS DE PRODUCTOS - TIENDA DE ANIME
-- =====================================================

INSERT INTO CATEGORIA (cat_id, cat_nombre, cat_descripcion)
VALUES ('CAT-1', 'Figuras de Acción', 'Figuras coleccionables de personajes anime');

INSERT INTO CATEGORIA (cat_id, cat_nombre, cat_descripcion)
VALUES ('CAT-2', 'Manga', 'Manga y novelas ligeras');

INSERT INTO CATEGORIA (cat_id, cat_nombre, cat_descripcion)
VALUES ('CAT-3', 'Accesorios', 'Llaveros, pulseras y accesorios anime');

INSERT INTO CATEGORIA (cat_id, cat_nombre, cat_descripcion)
VALUES ('CAT-4', 'Ropa', 'Camisetas, hoodies y más');

INSERT INTO CATEGORIA (cat_id, cat_nombre, cat_descripcion)
VALUES ('CAT-5', 'Tarjetas TCG', 'Cartas coleccionables y juegos de cartas');

INSERT INTO CATEGORIA (cat_id, cat_nombre, cat_descripcion)
VALUES ('CAT-6', 'Peluches', 'Peluches suaves de tus personajes favoritos');

INSERT INTO CATEGORIA (cat_id, cat_nombre, cat_descripcion)
VALUES ('CAT-7', 'Pósters', 'Pósters y láminas decorativas');

-- =====================================================
-- PRODUCTOS - 22 ARTÍCULOS TEMÁTICOS DE ANIME
-- =====================================================

-- Figuras de Acción (CAT-1)
INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-1', 'CAT-1', 'Goku Ultra Instinct', 'Figura de acción Goku Ultra Instinct 30cm', 85000.00, 20, 10);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-2', 'CAT-1', 'Naruto Modo Sabio', 'Figura Naruto Modo Sabio 25cm', 72000.00, 15, 5);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-3', 'CAT-1', 'Zoro Roronoa', 'Figura Zoro Roronoa 3 espadas 28cm', 95000.00, 12, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-4', 'CAT-1', 'Luffy Gear 5', 'Figura Monkey D. Luffy Gear 5 30cm', 89900.00, 18, 8);

-- Manga (CAT-2)
INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-5', 'CAT-2', 'One Piece Vol. 1', 'One Piece volumen 1 - Romance Dawn', 25000.00, 50, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-6', 'CAT-2', 'Jujutsu Kaisen Vol. 1', 'Jujutsu Kaisen volumen 1', 22000.00, 45, 10);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-7', 'CAT-2', 'Attack on Titan Vol. 1', 'Ataque a los Titanes volumen 1', 23000.00, 30, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-8', 'CAT-2', 'Demon Slayer Vol. 1', 'Kimetsu no Yaiba volumen 1', 22000.00, 35, 5);

-- Accesorios (CAT-3)
INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-9', 'CAT-3', 'Llavero Sharingan', 'Llavero ojo Sharingan de acero', 12000.00, 100, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-10', 'CAT-3', 'Pulsera Akatsuki', 'Pulsera de cuero con dije Akatsuki', 18000.00, 80, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-11', 'CAT-3', 'Anillo Esfera del Dragón', 'Anillo con esfera del dragón 4 estrellas', 25000.00, 40, 15);

-- Ropa (CAT-4)
INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-12', 'CAT-4', 'Camiseta Multiverse', 'Camiseta algodón diseño exclusivo Multiverse', 45000.00, 30, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-13', 'CAT-4', 'Hoodie Akatsuki', 'Hoodie negro nubes rojas Akatsuki', 95000.00, 20, 10);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-14', 'CAT-4', 'Gorra Bola de Dragón', 'Gorra con bordado esfera del dragón', 32000.00, 25, 0);

-- Tarjetas TCG (CAT-5)
INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-15', 'CAT-5', 'Booster One Piece TCG', 'Sobre de 12 cartas One Piece TCG', 18000.00, 60, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-16', 'CAT-5', 'Deck Dragon Ball Z', 'Mazo básico Dragon Ball Z TCG', 35000.00, 25, 5);

-- Peluches (CAT-6)
INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-17', 'CAT-6', 'Peluche Pikachu', 'Peluche Pikachu 25cm', 42000.00, 15, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-18', 'CAT-6', 'Peluche Totoro', 'Peluche Totoro gigante 40cm', 65000.00, 10, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-19', 'CAT-6', 'Peluche Eevee', 'Peluche Eevee 20cm', 38000.00, 20, 15);

-- Pósters (CAT-7)
INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-20', 'CAT-7', 'Póster Sword Art Online', 'Lámina A2 Sword Art Online', 15000.00, 40, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-21', 'CAT-7', 'Póster My Hero Academia', 'Lámina A2 My Hero Academia', 15000.00, 35, 0);

INSERT INTO PRODUCTOS (prod_id, cat_id, prod_nombre, prod_descripcion, prod_precio_venta, prod_stock, prod_descuento)
VALUES ('PROD-22', 'CAT-7', 'Combo 3 Pósters Anime', 'Set 3 láminas A2: Demon Slayer + One Piece + Jujutsu', 35000.00, 20, 20);

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
