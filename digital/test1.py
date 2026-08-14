from datetime import datetime
from pathlib import Path
import subprocess
import sys

# =========================
# Variables de configuración
# =========================
DURACION_SEGUNDOS = 25
SAMPLE_RATE = 4000
CANALES = 1
FORMATO_AUDIO = "S16_LE"

# Cambia este valor según el resultado de: arecord -l
DISPOSITIVO_AUDIO = "plughw:1,0"


def grabar_audio() -> Path:
    """Graba audio y devuelve la ruta del archivo generado."""

    carpeta_script = Path(__file__).resolve().parent
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo_salida = carpeta_script / f"{timestamp}.wav"

    comando = [
        "arecord",
        "-D", DISPOSITIVO_AUDIO,
        "-d", str(DURACION_SEGUNDOS),
        "-r", str(SAMPLE_RATE),
        "-c", str(CANALES),
        "-f", FORMATO_AUDIO,
        "-t", "wav",
        str(archivo_salida),
    ]

    print(f"Grabando durante {DURACION_SEGUNDOS} segundos...")
    print(f"Archivo: {archivo_salida.name}")

    try:
        subprocess.run(comando, check=True)
    except FileNotFoundError:
        print("Error: no se encontró el comando 'arecord'.")
        print("Instálalo con: sudo apt install alsa-utils")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"Error al grabar audio: {error}")
        print("Comprueba el dispositivo ejecutando: arecord -l")
        sys.exit(1)

    print(f"Grabación terminada: {archivo_salida}")
    return archivo_salida


if __name__ == "__main__":
    grabar_audio()
