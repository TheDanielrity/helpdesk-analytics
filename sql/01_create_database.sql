-- Ejecutar fuera de una transacción explícita, con permisos CREATE DATABASE.
USE [master];
GO
IF DB_ID(N'HelpDeskAnalytics') IS NULL
BEGIN
    EXEC(N'CREATE DATABASE [HelpDeskAnalytics];');
END;
GO
