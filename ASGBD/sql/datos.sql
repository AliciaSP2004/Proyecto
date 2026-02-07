-- Script de inicialización para WordPress
-- Este archivo se ejecuta automáticamente al iniciar el contenedor

-- Asegurar que estamos usando la base de datos correcta
USE wordpress_db;

-- Crear tabla de ejemplo (opcional)
-- Si tienes un SQL específico, reemplaza esto con tu contenido

-- Tabla de usuarios de prueba (ejemplo)
CREATE TABLE IF NOT EXISTS wp_users (
  ID bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  user_login varchar(60) NOT NULL DEFAULT '',
  user_pass varchar(255) NOT NULL DEFAULT '',
  user_email varchar(100) NOT NULL DEFAULT '',
  user_url varchar(100) NOT NULL DEFAULT '',
  user_registered datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (ID),
  KEY user_login_key (user_login),
  KEY user_nicename_key (user_login)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Verificar permisos del usuario de WordPress
GRANT ALL PRIVILEGES ON wordpress_db.* TO 'wordpress_user'@'%' IDENTIFIED BY 'wordpress_password_123';
FLUSH PRIVILEGES;

-- Tabla de opciones de WordPress (configuración)
CREATE TABLE IF NOT EXISTS wp_options (
  option_id bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT,
  option_name varchar(191) NOT NULL DEFAULT '',
  option_value longtext NOT NULL,
  autoload varchar(20) NOT NULL DEFAULT 'yes',
  PRIMARY KEY (option_id),
  UNIQUE KEY option_name (option_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insertar configuraciones básicas de WordPress
INSERT IGNORE INTO wp_options (option_name, option_value, autoload) VALUES
('siteurl', 'http://localhost', 'yes'),
('home', 'http://localhost', 'yes'),
('admin_email', 'admin@localhost.local', 'yes');
