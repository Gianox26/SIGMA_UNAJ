-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: reportes_unaj
-- ------------------------------------------------------
-- Server version	5.5.5-10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `acciones`
--

DROP TABLE IF EXISTS `acciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `acciones` (
  `id_accion` int(11) NOT NULL AUTO_INCREMENT,
  `descripcion` text NOT NULL,
  `fecha_inicio` datetime DEFAULT current_timestamp(),
  `fecha_fin` datetime DEFAULT NULL,
  `estado` enum('pendiente','en_proceso','finalizada') NOT NULL DEFAULT 'pendiente',
  `id_incidencia` int(11) NOT NULL,
  `id_supervisor` int(11) NOT NULL,
  `id_responsable` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_accion`),
  KEY `idx_estado_accion` (`estado`),
  KEY `idx_incidencia` (`id_incidencia`),
  KEY `fk_acciones_supervisor` (`id_supervisor`),
  KEY `fk_acciones_responsable` (`id_responsable`),
  CONSTRAINT `fk_acciones_incidencia` FOREIGN KEY (`id_incidencia`) REFERENCES `incidencias` (`id_incidencia`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_acciones_responsable` FOREIGN KEY (`id_responsable`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_acciones_supervisor` FOREIGN KEY (`id_supervisor`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `acciones`
--

LOCK TABLES `acciones` WRITE;
/*!40000 ALTER TABLE `acciones` DISABLE KEYS */;
/*!40000 ALTER TABLE `acciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historial`
--

DROP TABLE IF EXISTS `historial`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historial` (
  `id_historial` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_evento` enum('creacion','cambio_estado','asignacion','comentario','cierre','reabertura') NOT NULL,
  `estado_anterior` varchar(100) DEFAULT NULL,
  `estado_nuevo` varchar(100) DEFAULT NULL,
  `descripcion` text NOT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `id_usuario` int(11) NOT NULL,
  `id_incidencia` int(11) NOT NULL,
  PRIMARY KEY (`id_historial`),
  KEY `idx_historial_incidencia` (`id_incidencia`),
  KEY `idx_historial_fecha` (`fecha`),
  KEY `fk_historial_usuario` (`id_usuario`),
  CONSTRAINT `fk_historial_incidencia` FOREIGN KEY (`id_incidencia`) REFERENCES `incidencias` (`id_incidencia`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_historial_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historial`
--

LOCK TABLES `historial` WRITE;
/*!40000 ALTER TABLE `historial` DISABLE KEYS */;
INSERT INTO `historial` VALUES (1,'creacion',NULL,'nueva','El estudiante registró una nueva incidencia en el sistema.','2026-05-16 20:40:27',11,2),(2,'creacion',NULL,'nueva','El estudiante registró una nueva incidencia en el sistema.','2026-05-16 20:43:09',11,3),(3,'creacion',NULL,'nueva','El estudiante registró una nueva incidencia en el sistema.','2026-05-18 09:37:33',12,4);
/*!40000 ALTER TABLE `historial` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `incidencias`
--

DROP TABLE IF EXISTS `incidencias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `incidencias` (
  `id_incidencia` int(11) NOT NULL AUTO_INCREMENT,
  `titulo` varchar(255) NOT NULL,
  `descripcion` text NOT NULL,
  `categoria` enum('calidad','ambiental') NOT NULL,
  `prioridad` enum('baja','media','alta','critica') NOT NULL,
  `estado` enum('nueva','en_proceso','resuelta','cerrada','reabierta') NOT NULL DEFAULT 'nueva',
  `laboratorio` varchar(255) NOT NULL,
  `fecha_reporte` datetime DEFAULT current_timestamp(),
  `evidencia_url` varchar(255) DEFAULT NULL,
  `id_usuario` int(11) NOT NULL,
  PRIMARY KEY (`id_incidencia`),
  KEY `idx_estado` (`estado`),
  KEY `idx_fecha` (`fecha_reporte`),
  KEY `idx_categoria` (`categoria`),
  KEY `idx_usuario` (`id_usuario`),
  CONSTRAINT `fk_incidencias_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `incidencias`
--

LOCK TABLES `incidencias` WRITE;
/*!40000 ALTER TABLE `incidencias` DISABLE KEYS */;
INSERT INTO `incidencias` VALUES (1,'Filtración de agua en techo del Laboratorio de Física','Durante la precipitación pluvial del 15/05/2024 se detectó filtración de agua sobre el área de equipos eléctricos del Laboratorio de Física (Pabellón Capilla). Existe riesgo de cortocircuito y daño potencial a osciloscopios y fuentes de alimentación.','ambiental','critica','nueva','Laboratorio de Física','2026-05-16 17:15:10',NULL,3),(2,'Falla una computadora','Se reporta una incidencia de calidad en Laboratorio de computo. Descripción del estudiante: falla una computadora. De acuerdo con la información registrada, la prioridad sugerida es media. Se solicita la revisión del caso por el área responsable para evaluar la situación, definir las acciones correspondientes y realizar el seguimiento dentro del sistema.','calidad','media','nueva','Laboratorio de computo','2026-05-16 20:40:27',NULL,11),(3,'Filtracion de agua del baño 2 piso','Se reporta una incidencia ambiental en Filtracion de agua del baño 2 piso. Descripción del estudiante: Filtracion de agua del baño 2 piso. De acuerdo con la información registrada, la prioridad sugerida es alta. Se solicita la revisión del caso por el área responsable para evaluar la situación, definir las acciones correspondientes y realizar el seguimiento dentro del sistema.','ambiental','alta','nueva','Filtracion de agua del baño 2 piso','2026-05-16 20:43:09',NULL,11),(4,'Filtración de agua','Se reporta una incidencia ambiental en Baño. Descripción del estudiante: Filtración de agua. De acuerdo con la información registrada, la prioridad sugerida es alta. Se solicita la revisión del caso por el área responsable para evaluar la situación, definir las acciones correspondientes y realizar el seguimiento dentro del sistema.','ambiental','alta','nueva','Baño','2026-05-18 09:37:33',NULL,12);
/*!40000 ALTER TABLE `incidencias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notificaciones`
--

DROP TABLE IF EXISTS `notificaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notificaciones` (
  `id_notificacion` int(11) NOT NULL AUTO_INCREMENT,
  `mensaje` text NOT NULL,
  `leido` tinyint(1) DEFAULT 0,
  `fecha` datetime DEFAULT current_timestamp(),
  `id_usuario` int(11) NOT NULL,
  PRIMARY KEY (`id_notificacion`),
  KEY `idx_notif_usuario` (`id_usuario`,`leido`),
  KEY `idx_notif_fecha` (`fecha`),
  CONSTRAINT `fk_notificaciones_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notificaciones`
--

LOCK TABLES `notificaciones` WRITE;
/*!40000 ALTER TABLE `notificaciones` DISABLE KEYS */;
INSERT INTO `notificaciones` VALUES (1,'Tu reporte #2 fue registrado correctamente y quedó en estado nueva.',0,'2026-05-16 20:40:27',11),(2,'Tu reporte #3 fue registrado correctamente y quedó en estado nueva.',0,'2026-05-16 20:43:09',11),(3,'Tu reporte #4 fue registrado correctamente y quedó en estado nueva.',0,'2026-05-18 09:37:33',12);
/*!40000 ALTER TABLE `notificaciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) NOT NULL,
  `apellido` varchar(255) NOT NULL,
  `correo` varchar(255) NOT NULL,
  `contraseña` varchar(255) NOT NULL,
  `rol` enum('usuario','supervisor','administrador') NOT NULL,
  `estado` tinyint(1) DEFAULT 1,
  `fecha_registro` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Edgar','Mamani Ticona','e.mamani@unaj.edu.pe','scrypt:32768:8:1$TuSaltAqui123','administrador',1,'2026-05-16 17:15:10'),(2,'Sonia','Quispe Apaza','s.quispe@unaj.edu.pe','scrypt:32768:8:1$TuSaltAqui123','supervisor',1,'2026-05-16 17:15:10'),(3,'Luis Fernando','Ccama Huanca','l.ccama@unaj.edu.pe','scrypt:32768:8:1$TuSaltAqui123','usuario',1,'2026-05-16 17:15:10'),(8,'Luis Fernando','Ccama Huanca','luis@unaj.edu.pe','scrypt:32768:8:1$12345678','usuario',1,'2026-05-16 19:55:04'),(11,'Rivaldo','Toledo Bellido','2022107002.est@unaj.edu.pe','pbkdf2:sha256:260000$32ykVjCpzJbe4DjQ$74918c656a328f28270e45c99f14a2b8564a60360421ae363474b5a53f8f62c6','usuario',1,'2026-05-16 19:59:12'),(12,'Frank Eddy','Copa Mamani','2022107001.est@unaj.edu.pe','pbkdf2:sha256:260000$NQsvgtGxnJicaiFq$77bb940167d44f073273b576bf608b64c6e37082c0288683bad60eae8694ce69','usuario',1,'2026-05-18 08:46:13'),(13,'Isaac David','Chaupaza Zapana','2022107014.est@unaj.edu.pe','pbkdf2:sha256:260000$TpIrcN9RaZDQoTpL$9000c62e432a86b27e047f1a38767d4a864a85b337c2f063b50cd94f1a57942d','usuario',1,'2026-05-18 09:32:55'),(14,'Ivan Royer','Capia Tula','2022107011.est@unaj.edu.pe','pbkdf2:sha256:260000$qNH0pXBa5KT08L3s$6f5826ba9cb79f881c69dac2e9f1dde5dc7cbc2be5d15300ac34196833b2d6da','usuario',1,'2026-05-18 09:32:55'),(15,'Yords Williams','Ccalla Mamani','2022107039.est@unaj.edu.pe','pbkdf2:sha256:260000$rRjo7PMnvCwMyL4L$629a608542088b1d25e43db2a5c765fbd0998f68bed5780a183a791dba57186d','usuario',1,'2026-05-18 09:32:55'),(16,'Enrique Solano','Chatta Añasco','2022107006.est@unaj.edu.pe','pbkdf2:sha256:260000$V4xbkI4Yc4dhdV8P$80243c5321c34fa3a314a69469cb928ffb2525a679088e1b47f80fc28629a1ec','usuario',1,'2026-05-18 09:32:55'),(17,'Yoselin Yuliana','Condori Hualla','2021207003.est@unaj.edu.pe','pbkdf2:sha256:260000$cHEKbl9W5Lumf9i6$527ad006407969b3f76cbb7fc5b438c37c2785b9f77284ddedab284525d0bacf','usuario',1,'2026-05-18 09:32:55'),(18,'Raiza Alexandra','Curro Apaza','2022107031.est@unaj.edu.pe','pbkdf2:sha256:260000$SzL9w0fAWQa5RW81$4e698f4f61ba01279106a3268e5435a0498650f3efca433c490900f3e5e0ea40','usuario',1,'2026-05-18 09:32:55'),(19,'Andre Derain','Flores Caceres','2021207022.est@unaj.edu.pe','pbkdf2:sha256:260000$floCqfti5HLtlQzp$217cf136c244037485d7bad641e0e25ecacfcf43052bead05e97d7e81c6d0e41','usuario',1,'2026-05-18 09:32:55'),(20,'Smith Clever','Givera Coila','2022107051.est@unaj.edu.pe','pbkdf2:sha256:260000$xVfTIx5kEzrZi69H$1deb7c553874602b8d59814d77200fca7f349f51d752cf055d7fa54708676800','usuario',1,'2026-05-18 09:32:55'),(21,'Aldair Piter','Ito Velarde','2022107004.est@unaj.edu.pe','pbkdf2:sha256:260000$vk0TUdLS10T6ZdsC$c387f45165657804b585ae66d95ce39f12eac94708680d57140ea9f4d14bd03c','usuario',1,'2026-05-18 09:32:55'),(22,'Johan Israel','Apaza Flores','2022107033.est@unaj.edu.pe','pbkdf2:sha256:260000$wEIRZsRXx4Lbjaya$02ad72716ef74161bd9437de21442146546d51d3eef5293ec70c2a37c80dbc4c','usuario',1,'2026-05-18 09:32:55'),(23,'David Alexander','Mestas Quispe','2022107016.est@unaj.edu.pe','pbkdf2:sha256:260000$484aA4ez9YOCerZs$94a175cea4585b12416c8f2345f15895a9550f2a74e3b4db13a05859ac363898','usuario',1,'2026-05-18 09:32:55'),(24,'Frank Justo','Polo Pariapaza','2022107038.est@unaj.edu.pe','pbkdf2:sha256:260000$ulK1sxHqIIfzDfNv$7ed1263bf9ee3e6fa41fc43798fdc981fc1c4618ed426d2a8c239e6992380e52','usuario',1,'2026-05-18 09:32:55'),(25,'Rodrigo Betuel','Quispe Charca','2022107040.est@unaj.edu.pe','pbkdf2:sha256:260000$HS36no9fSIIzXhOW$b13f4c48cb47af9f8e5ed13795ab0d33fc1a973cc9314a699269f965dc2b3c50','usuario',1,'2026-05-18 09:32:55'),(26,'Deivis Brayan','Quispe Pacompia','2022107034.est@unaj.edu.pe','pbkdf2:sha256:260000$V3Gmw0FEXJsDx0Gw$17bd86b6b04eaff6e2886f518497812005a919aa09c89f6a588c684a8404053a','usuario',1,'2026-05-18 09:32:55'),(27,'Yuri Andrea','Ramos Suca','2022107050.est@unaj.edu.pe','pbkdf2:sha256:260000$n2dbndkuiTfluFPt$69061fb3a6f306309b5857076735bc48bf16edb54964bc5bcdb033d1a88235cf','usuario',1,'2026-05-18 09:32:55'),(28,'Diego Alexander','Sonco Condori','2021207040.est@unaj.edu.pe','pbkdf2:sha256:260000$YsrcQNezQ3Kaugv2$3ec6b059e2cc4c248cfdcc714ca8cf708a2a840f0ee2499f97f5e2d4bbefc6ee','usuario',1,'2026-05-18 09:32:55'),(29,'Guimel Eliel','Ticona Quispe','2021207042.est@unaj.edu.pe','pbkdf2:sha256:260000$LyU2bFAxanYl298e$a7da8157652addc03ea507a31b6e4a04b9dc8b7fb0f1b275126c1706c390db81','usuario',1,'2026-05-18 09:32:55'),(30,'Juan Gedeon','Tito Moya','2022107005.est@unaj.edu.pe','pbkdf2:sha256:260000$D7UAXzHKrtsUuOKw$00ec33e1b0243f4849048ab6baa9307d6d4e6af2898aef5a21ae0cf4f3171526','usuario',1,'2026-05-18 09:32:55'),(31,'Jesus Abel','Valeriano Osnayo','2022107015.est@unaj.edu.pe','pbkdf2:sha256:260000$tCdMy6aV5owvWG0e$e33dfa52cbb372224db4b8de8a7cbd109bfad9b38c29f8271e8a37d2a88204aa','usuario',1,'2026-05-18 09:32:55'),(32,'Girodel Josue','Zea Paredes','2022107049.est@unaj.edu.pe','pbkdf2:sha256:260000$I4Ae0DsLbxXO4nmy$23c2fd3c65bb0808c3025cbad7b06437ecbe508226e6cc7db8c0297cc543d05d','usuario',1,'2026-05-18 09:32:55'),(33,'Nifer','Calcina Mamani','2022107037.est@unaj.edu.pe','pbkdf2:sha256:260000$PzyAJyCQhWwSyCrm$a9c964c08ab1d2f6a3933aeadab949a48bc75a2128239e3abc6d078747452678','usuario',1,'2026-05-18 09:32:55'),(34,'Cleydy Edith','Carita Laura','2022107009.est@unaj.edu.pe','pbkdf2:sha256:260000$w9orgKLT9G5CmiOQ$9e31566c0084f32c031c62cf69aa902ed2d7d64eefb0e043e9948bcb77eb2513','usuario',1,'2026-05-18 09:32:55'),(35,'Wilmer Henry','Ccallohuanca Condori','2022107022.est@unaj.edu.pe','pbkdf2:sha256:260000$EnfRlfgBzEo6OBol$5860408077263c5ab043fca180491768b9bc26edab08ffdf74aab9c1639b792a','usuario',1,'2026-05-18 09:32:55'),(36,'Yakelin Madeleine','Chipana Larico','2022107023.est@unaj.edu.pe','pbkdf2:sha256:260000$JlRjfDAzah0wEUbi$d9c5d9501073321c4cde4795c2f9fbc48a2855083abe0622455e1a10c7227799','usuario',1,'2026-05-18 09:32:55'),(37,'Hersson Arnold','Condori Quilla','2021207021.est@unaj.edu.pe','pbkdf2:sha256:260000$PrIkSDb7Rx4xRVWF$00f53f7273eb6b84de2118346015f5ab27bcc4795af86f1a300cb0466e207bc3','usuario',1,'2026-05-18 09:32:55'),(38,'Rainer Alex','Cuno Enriquez','2022107055.est@unaj.edu.pe','pbkdf2:sha256:260000$42JkLecOlczpMRP5$cbbe7172364e0d01dcc38e6cf35d41caa0244d2267a98a02b3f4f05894e478c3','usuario',1,'2026-05-18 09:32:55'),(39,'Xavier Ronaldo','Estofanero Apaza','2022107012.est@unaj.edu.pe','pbkdf2:sha256:260000$yz7qWrC523z0yS4r$76a91f0bdee569fb6c9afcff8430bcc294601384fff8e0105524b4f7bd40b4d3','usuario',1,'2026-05-18 09:32:55'),(40,'Dimas Mijael','Flores Yerba','2022107003.est@unaj.edu.pe','pbkdf2:sha256:260000$ro6R8LKjfmX80SvZ$b6f547ef798b0069b1474c5f70968b324810728072650c16283961033fc0446b','usuario',1,'2026-05-18 09:32:55'),(41,'Ruth Aydi','Hancco Poma','2022107025.est@unaj.edu.pe','pbkdf2:sha256:260000$wz8rTWFeNNFY9giT$4802a90742fa858925605f907d9135a98eab8ce2d90dcc0bc88d48793b56a648','usuario',1,'2026-05-18 09:32:55'),(42,'Rsaquel Pamela','Laura Ccama','2022107008.est@unaj.edu.pe','pbkdf2:sha256:260000$TPTZtWeIBogeDgCn$0afd863faae297713b040bc268beaf2793420a20f3cd0cfa981c28ba9a1b8fe1','usuario',1,'2026-05-18 09:32:55'),(43,'Devis Alonso','Marquez Mayta','2022107044.est@unaj.edu.pe','pbkdf2:sha256:260000$AwrdiRNPYJeh7MHL$27894df5a261683d4854490a59c9ccc50b3dfc33ac68e4be4fd93f2a6c9cafdd','usuario',1,'2026-05-18 09:32:55'),(44,'Claudia','Pocohuanca Huahuachampi','2022107036.est@unaj.edu.pe','pbkdf2:sha256:260000$jjdNgWnr3TzN4WFM$c1a74eead0cd0de2762dac6dd684e47e583785771248b753acad7e3d86593c45','usuario',1,'2026-05-18 09:32:55'),(45,'Yaren Amado','Quispe Calcina','2022107042.est@unaj.edu.pe','pbkdf2:sha256:260000$j4kIPt7LllZHhyGk$ff66fe6559a13a75ce09d14a6ae40cf1aa1c2f567984ca7552f4cbbd7d46ada1','usuario',1,'2026-05-18 09:32:55'),(46,'Leydy Milagros','Quispe Cornejo','2022107046.est@unaj.edu.pe','pbkdf2:sha256:260000$Q6fELTLrJvGNfso2$33c51962720963d096ecd15a7ad4c2af782739db4dddec6e63cb8c9f12b161aa','usuario',1,'2026-05-18 09:32:55'),(47,'Elyan Rosy','Quispe Zapana','2022107035.est@unaj.edu.pe','pbkdf2:sha256:260000$GJNzAcaOEtHiBrKd$0f67c0857123387e3b95573bffc6c9035063b01e9e988f3649314eebe3fd029d','usuario',1,'2026-05-18 09:32:55'),(48,'Delfin Estanis','Roque Mullisaca','2022107017.est@unaj.edu.pe','pbkdf2:sha256:260000$2aKdBavTiL7uEYey$31d189b5380462073c96cf4f7e1ad4b86ebf0ef66999bad3e5e5a8e8eccbcad5','usuario',1,'2026-05-18 09:32:55'),(49,'Marlon Brando','Sucasaire Mamani','2022107045.est@unaj.edu.pe','pbkdf2:sha256:260000$Jy1owawiJcz8p4Lv$71397b8705ebe4d5f2b69383ba9295d8d04b13b4ddd5a6dff66c2c5eceec37fc','usuario',1,'2026-05-18 09:32:55'),(50,'Luis Fernando','Ticona Yunganina','2022107041.est@unaj.edu.pe','pbkdf2:sha256:260000$gGDZKoKI4zsBoH8t$fb6829dcc31504919e8a4df0eb4dc0b354515f21407c16c7a35618719b910766','usuario',1,'2026-05-18 09:32:55'),(51,'Birgilio Ronald','Yanqui Escarcena','2022107013.est@unaj.edu.pe','pbkdf2:sha256:260000$ugpQWk9jb8Od9SH0$2ca80eeaca40c2dcac064b0e814561c42b3724d332286e46df7be7ec980cae1a','usuario',1,'2026-05-18 09:32:55'),(52,'Deyvi Rodrigo','Zela Sanca','2022107010.est@unaj.edu.pe','pbkdf2:sha256:260000$TXdZAfboeqSqXQb1$0d34db652dcad335e806ba58acf8849b7f8579dc1b2a1635f0a935551f5281b1','usuario',1,'2026-05-18 09:32:55');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-18  9:46:02
