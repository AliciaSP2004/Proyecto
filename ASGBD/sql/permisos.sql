-- Otorgar permisos a usuario asier sobre la base de datos valles_db
GRANT ALL PRIVILEGES ON *.* TO 'asier'@'%' IDENTIFIED BY 'usuario@1';
GRANT ALL PRIVILEGES ON *.* TO 'asier'@'localhost' IDENTIFIED BY 'usuario@1';
FLUSH PRIVILEGES;
