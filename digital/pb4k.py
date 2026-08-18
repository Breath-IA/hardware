from datetime import datetime
from pathlib import Path
import subprocess
import sys

# =========================
# Variables de configuración
# =========================
DURACION_SEGUNDOS = 15
SAMPLE_RATE = 4000
CANALES = 1
FORMATO_AUDIO = "S16_LE"
DISPOSITIVO_AUDIO = "plughw:1,0"
CARPETA_MONTAJES = Path("/media/oscar")
CARPETA_GRABACIONES = "grabaciones"

# Carpeta local de respaldo si no hay SD/USB externa montada
CARPETA_LOCAL_RESPALDO = Path(__file__).resolve().parent

FRECUENCIA_CORTE_LOWPASS = 4000  # Hz
SUFIJO_FILTRADO = "4k"


def detectar_sd_externa() -> Path | None:
    """
    Busca una memoria o microSD montada dentro de /media/oscar.
    Devuelve None si no hay ninguna unidad montada (en vez de lanzar error).
    """
    if not CARPETA_MONTAJES.exists():
        return None

    unidades = [
        ruta
        for ruta in CARPETA_MONTAJES.iterdir()
        if ruta.is_dir() and ruta.is_mount()
    ]

    if not unidades:
        return None

    if len(unidades) > 1:
        print("Se encontraron varias unidades:")
        for indice, unidad in enumerate(unidades, start=1):
            print(f"{indice}. {unidad}")
        print(f"Se utilizará la primera: {unidades[0]}")

    return unidades[0]


def obtener_carpeta_base() -> Path:
    """
    Intenta usar la SD/USB externa. Si no hay ninguna montada,
    usa la carpeta local del script como respaldo.
    """
    sd = detectar_sd_externa()
    if sd is not None:
        print(f"MicroSD/USB externa detectada: {sd}")
        return sd

    print("Aviso: no se encontró ninguna microSD o USB externa montada.")
    print(f"Se usará la carpeta local: {CARPETA_LOCAL_RESPALDO}")
    return CARPETA_LOCAL_RESPALDO


def construir_nombre_filtrado(archivo_original: Path) -> Path:
    """
    Inserta el sufijo de filtrado (ej. '_4k') justo antes de la extensión .wav.
    Ej: 2025-01-01_10-00-00.wav -> 2025-01-01_10-00-00_4k.wav
    """
    return archivo_original.with_name(
        f"{archivo_original.stem}_{SUFIJO_FILTRADO}{archivo_original.suffix}"
    )


def grabar_audio() -> Path:
    """
    Graba audio desde el INMP441 y lo guarda en la SD externa
    (o localmente si no hay ninguna disponible).
    """
    base = obtener_carpeta_base()

    carpeta_salida = base / CARPETA_GRABACIONES
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo_salida = carpeta_salida / f"{timestamp}.wav"

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
    print(f"Sample rate: {SAMPLE_RATE} Hz")
    print(f"Archivo: {archivo_salida}")

    try:
        subprocess.run(comando, check=True)
    except FileNotFoundError:
        print("Error: no se encontró el programa arecord.")
        print("Instálalo con: sudo apt install alsa-utils")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"Error durante la grabación: {error}")
        if archivo_salida.exists():
            archivo_salida.unlink()
        sys.exit(1)

    subprocess.run(["sync"], check=False)
    print("Grabación terminada correctamente.")
    print(f"Guardada en: {archivo_salida}")

    return archivo_salida


def filtrar_pasa_bajo(archivo_entrada: Path) -> Path:
    """
    Aplica un filtro pasa-bajo con frecuencia de corte FRECUENCIA_CORTE_LOWPASS
    usando ffmpeg, y guarda el resultado con el sufijo '_4k' antes de .wav.
    """
    archivo_salida = construir_nombre_filtrado(archivo_entrada)

    comando = [
        "ffmpeg",
        "-y",  # sobrescribe si ya existe
        "-i", str(archivo_entrada),
        "-af", f"lowpass=f={FRECUENCIA_CORTE_LOWPASS}",
        str(archivo_salida),
    ]

    print(f"Aplicando filtro pasa-bajo a {FRECUENCIA_CORTE_LOWPASS} Hz...")

    try:
        subprocess.run(
            comando,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("Error: no se encontró el programa ffmpeg.")
        print("Instálalo con: sudo apt install ffmpeg")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"Error durante el filtrado: {error}")
        if archivo_salida.exists():
            archivo_salida.unlink()
        sys.exit(1)

    subprocess.run(["sync"], check=False)
    print("Filtrado terminado correctamente.")
    print(f"Guardado en: {archivo_salida}")

    return archivo_salida


def grabar_y_filtrar() -> tuple[Path, Path]:
    """
    Graba el audio y a continuación aplica el filtro pasa-bajo,
    devolviendo las rutas del archivo original y del filtrado.
    """
    archivo_original = grabar_audio()
    archivo_filtrado = filtrar_pasa_bajo(archivo_original)
    return archivo_original, archivo_filtrado


if __name__ == "__main__":
    grabar_y_filtrar()
