CREATE SCHEMA IF NOT EXISTS emision_licencias;
USE emision_licencias;

CREATE TABLE Persona (
    id_persona INT AUTO_INCREMENT PRIMARY KEY,
    cui VARCHAR(13) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL
);

CREATE TABLE Tipo_Licencia (
    id_tipo_licencia INT AUTO_INCREMENT PRIMARY KEY,
    letra VARCHAR(2) NOT NULL UNIQUE,
    descripcion VARCHAR(100)
);

CREATE TABLE Licencia (
    id_licencia INT AUTO_INCREMENT PRIMARY KEY,
    id_persona INT NOT NULL,
    id_tipo_licencia INT NOT NULL,
    fecha_primera_emision DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    FOREIGN KEY (id_persona) REFERENCES Persona(id_persona),
    FOREIGN KEY (id_tipo_licencia) REFERENCES Tipo_Licencia(id_tipo_licencia)
);

CREATE TABLE Tramite (
    id_tramite INT AUTO_INCREMENT PRIMARY KEY,
    id_licencia INT NOT NULL,
    tipo_tramite ENUM('Primera Vez', 'Renovacion') NOT NULL,
    fecha_tramite DATE NOT NULL,
    anios_vigencia INT NOT NULL CHECK (anios_vigencia >= 1 AND anios_vigencia <= 5),
    monto_pagado DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (id_licencia) REFERENCES Licencia(id_licencia)
);

CREATE TABLE Requisitos_Primera_Vez (
    id_tramite INT PRIMARY KEY,
    examen_teorico BOOLEAN NOT NULL DEFAULT FALSE,
    examen_practico BOOLEAN NOT NULL DEFAULT FALSE,
    examen_vista BOOLEAN NOT NULL DEFAULT FALSE,
    carta_padre_menor BOOLEAN NULL,
    FOREIGN KEY (id_tramite) REFERENCES Tramite(id_tramite)
);

INSERT INTO Tipo_Licencia (letra, descripcion) VALUES 
('A', 'Vehiculos de carga pesada'),
('B', 'Vehiculos de carga liviana'),
('C', 'Vehiculos particulares'),
('M', 'Motocicletas');

INSERT INTO Persona (cui, nombre, apellido, fecha_nacimiento) VALUES 
('1234567890101', 'Juan', 'Perez', '2000-05-15'),
('9876543210101', 'Maria', 'Gomez', '2008-10-20');

INSERT INTO Licencia (id_persona, id_tipo_licencia, fecha_primera_emision, fecha_vencimiento) VALUES 
(1, 3, '2023-05-10', '2026-05-15');

INSERT INTO Tramite (id_licencia, tipo_tramite, fecha_tramite, anios_vigencia, monto_pagado) VALUES 
(1, 'Primera Vez', '2023-05-10', 1, 100.00);

INSERT INTO Requisitos_Primera_Vez (id_tramite, examen_teorico, examen_practico, examen_vista, carta_padre_menor) VALUES 
(1, TRUE, TRUE, TRUE, NULL);

INSERT INTO Tramite (id_licencia, tipo_tramite, fecha_tramite, anios_vigencia, monto_pagado) VALUES 
(1, 'Renovacion', '2024-05-10', 3, 300.00);

SELECT 
    p.nombre, p.apellido, tl.letra, 
    t.tipo_tramite, t.fecha_tramite, t.anios_vigencia, t.monto_pagado
FROM Persona p
JOIN Licencia l ON p.id_persona = l.id_persona
JOIN Tramite t ON l.id_licencia = t.id_licencia
JOIN Tipo_Licencia tl ON l.id_tipo_licencia = tl.id_tipo_licencia
WHERE p.cui = '1234567890101';

SELECT 
    p.nombre, p.apellido, req.examen_teorico, req.examen_practico, req.examen_vista, req.carta_padre_menor
FROM Requisitos_Primera_Vez req
JOIN Tramite t ON req.id_tramite = t.id_tramite
JOIN Licencia l ON t.id_licencia = l.id_licencia
JOIN Persona p ON l.id_persona = p.id_persona;

SELECT 
    p.nombre, p.apellido, p.fecha_nacimiento, l.fecha_vencimiento
FROM Licencia l
JOIN Persona p ON l.id_persona = p.id_persona
WHERE MONTH(l.fecha_vencimiento) = MONTH(CURRENT_DATE());
