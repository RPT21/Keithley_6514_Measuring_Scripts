import serial
import time
from serial.serialutil import PARITY_EVEN, STOPBITS_ONE, EIGHTBITS
import csv

# Cambia el nombre del puerto según tu sistema
port = 'COM9'            # Ejemplo: COM3 en Windows, /dev/ttyUSB0 en Linux
baudrate = 9600
TIMEOUT = 2              # En segundos
parity=PARITY_EVEN
bytesize=EIGHTBITS
stopbits=STOPBITS_ONE
# with serial.Serial(port=port, baudrate=baudrate, parity=parity ,bytesize=bytesize, stopbits=stopbits, timeout=TIMEOUT) as ser:

verbose = False

def send_cmd(ser, cmd, wait=0.1):
    """Envía comando SCPI"""
    ser.write((cmd + '\r').encode())
    time.sleep(wait)

def query_cmd(ser, cmd, wait=0.1):
    """Envía comando SCPI y devuelve respuesta"""
    send_cmd(ser, cmd, wait)
    return ser.readline().decode().strip()

def wait_for_srq(ser):
    """Espera a que bit 6 del status byte esté activo (SRQ)"""
    while True:
        send_cmd(ser, "*STB?")
        try:
            stb = int(ser.readline().decode().strip())
            if stb & 64:
                return
        except ValueError:
            continue
        time.sleep(0.2)

def main():
    with serial.Serial(port=port, baudrate=baudrate, parity=parity ,bytesize=bytesize, stopbits=stopbits, timeout=TIMEOUT) as ser:
        
        # Limpieza inicial
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        print("Inicializando Keithley 6514...")

        # Reseteo general y configuración
        send_cmd(ser, "*RST")                            # Reset completo
        send_cmd(ser, "STAT:PRES;*CLS")                  # Limpiar sistema de estado
        send_cmd(ser, "STAT:MEAS:ENAB 512")              # Habilitar BFL (bit 9 del ESR)
        send_cmd(ser, "*SRE 1")                          # Habilitar SRQ por STB bit 0
        send_cmd(ser, "CURR:NPLC 0.1")
        send_cmd(ser, "DISP:DIG 4.5")

        # Configuración del buffer
        send_cmd(ser, "TRIG:COUN 1970")                    # Número de medidas
        send_cmd(ser, "TRAC:POIN 1970")                    # Tamaño del buffer
        send_cmd(ser, "TRAC:FEED SENS;FEED:CONT NEXT")   # Fuente = medidas sin procesar

        # Iniciar adquisición
        send_cmd(ser, "INIT")

        print("Esperando a que se llene el buffer (SRQ)...")
        wait_for_srq(ser)
        print("SRQ recibido, leyendo estado...")

        # Leer estado del subsistema de medidas
        meas_status = query_cmd(ser, "STAT:MEAS?")
        print("STAT:MEAS? =", meas_status)

        # Leer datos del buffer
        print("Leyendo TRAC:DATA...")
        send_cmd(ser, "TRAC:DATA?")
        # reading_data = ser.readline().decode().strip()
        reading_data = ser.readall().decode().strip()

        try:
            values = [float(x) for x in reading_data.split(',')]
            
            if verbose:
                print("Mediciones:")
                for i, v in enumerate(values, 1):
                    print(f"{i}: {v:.3e} A")
                
        except ValueError:
            print("Error al procesar los datos:", reading_data)

        # Si quieres repetir, reactiva el modo NEXT
        print("\nPara repetir, reactiva el buffer con: FEED:CONT NEXT")
        send_cmd(ser, "FEED:CONT NEXT")

        return values

if __name__ == "__main__":
    values = main()
    read, timestamp, status = values[0::3], values[1::3], values[2::3]
    
    with open('CSV_File.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Escribir encabezados (opcional)
        writer.writerow(['Time (s)', 'Current (A)'])
        
        # Escribir filas combinando las dos listas
        for timestamp_val, current_val in zip(timestamp, read):
            writer.writerow([timestamp_val, current_val])
    
   
