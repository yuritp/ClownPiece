import logging
import sys


def setup_logging():
    """Configura el sistema de logging para todo el proyecto."""

    # Formato del log: [HORA] [NIVEL] [NOMBRE_DEL_MODULO] Mensaje
    log_format = "[%(asctime)s] [%(levelname)-8s] [%(name)-20s] %(message)s"

    # Configuración básica del logger
    logging.basicConfig(
        level=logging.INFO,  # Nivel mínimo de logs a mostrar (INFO, DEBUG, WARNING, etc.)
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout  # Envía los logs a la consola
    )

    # Silenciar logs de librerías muy "ruidosas"
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    log = logging.getLogger(__name__)
    log.info("Sistema de logging configurado exitosamente.")