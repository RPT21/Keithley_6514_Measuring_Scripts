import serial
import time
from serial.serialutil import PARITY_EVEN, STOPBITS_ONE, EIGHTBITS

# Cambia el nombre del puerto según tu sistema
port = 'COM9'            # Ejemplo: COM3 en Windows, /dev/ttyUSB0 en Linux
baudrate = 9600
TIMEOUT = 2              # En segundos
parity=PARITY_EVEN
bytesize=EIGHTBITS
stopbits=STOPBITS_ONE
# with serial.Serial(port=port, baudrate=baudrate, parity=parity ,bytesize=bytesize, stopbits=stopbits, timeout=TIMEOUT) as ser:

    
def send_cmd(ser, cmd, wait=0.1):
    """Envía un comando SCPI al instrumento"""
    ser.write((cmd + '\r').encode())
    time.sleep(wait)

def query_cmd(ser, cmd, wait=0.1):
    """Envía un comando SCPI y devuelve la respuesta"""
    send_cmd(ser, cmd, wait)
    return ser.readline().decode().strip()

def main():
    with serial.Serial(port=port, baudrate=baudrate, parity=parity ,bytesize=bytesize, stopbits=stopbits, timeout=TIMEOUT) as ser:
        # Limpieza de buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # Inicialización del instrumento
        send_cmd(ser, "*CLS")                        # Clear status
        send_cmd(ser, "STAT:PRES")                   # Reset status system
        send_cmd(ser, "STAT:MEAS:ENAB 512")          # Habilita BFL (Buffer Full)
        send_cmd(ser, "*SRE 1")                      # Habilita el bit SRQ
        send_cmd(ser, "TRAC:FEED:CONT NEXT")         # Continuar en el buffer
        send_cmd(ser, "INIT")                        # Inicia la adquisición

        print("Esperando a que se active SRQ (bit 6 del status byte)...")

        # Espera a que se active el bit 6 del status byte (SRQ)
        while True:
            send_cmd(ser, "*STB?")
            response = ser.readline().decode().strip()
            try:
                status_byte = int(response)
                if status_byte & 64:  # Bit 6 (SRQ)
                    print("SRQ recibido: el instrumento tiene datos listos.")
                    break
            except ValueError:
                print(f"Respuesta inesperada: {response}")
            time.sleep(0.2)

        # Leer datos del buffer si se desea
        send_cmd(ser, ":TRAC:DATA? 1,10")
        data = ser.readline().decode().strip()
        print("Datos del buffer:", data)

if __name__ == "__main__":
    main()
