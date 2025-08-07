import pyvisa
import time
import csv
import matplotlib.pyplot as plt

# Cambia la dirección GPIB según tu configuración
GPIB_ADDRESS = 'GPIB0::14::INSTR'  # GPIB0 es el bus, 14 es la dirección del Keithley
number_of_samples = 2500

# Configura el tamaño del buffer y el tiempo de espera entre lecturas
BUFFER_SIZE = 2500
READ_INTERVAL = 0.5  # segundos

verbose = False

def send_cmd(inst, cmd, wait=0.1):
    """Envía comando SCPI"""
    inst.write(cmd)
    time.sleep(wait)

def query_cmd(inst, cmd, wait=0.1):
    """Envía comando SCPI y devuelve respuesta"""
    time.sleep(wait)
    return inst.query(cmd).strip()

def wait_for_srq(inst):
    """Espera a que bit 6 del status byte esté activo (SRQ)"""
    while True:
        try:
            stb = inst.stb  # Status Byte
            if stb & 64:
                return
        except Exception:
            continue
        time.sleep(0.2)

def main():
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(GPIB_ADDRESS)

    # Establecer timeout en milisegundos
    inst.timeout = 5000  # 5 segundos

    print("Inicializando Keithley 6514...")

    # Reseteo y configuración inicial
    send_cmd(inst, "*RST")
    send_cmd(inst, "STAT:PRES;*CLS")
    send_cmd(inst, "STAT:MEAS:ENAB 512")
    send_cmd(inst, "*SRE 1")
    
    
    
    ### ---------------------------------------------------------------------------------------------------- ###
    
    
    # ### Configurar medicion de corriente
    
    
    # Seleccionamos la funcion corriente
    send_cmd(inst, 'SENS:FUNC "CURR"')
    send_cmd(inst, "CONF:CURR")
    
    # Desactivamos el zero check and zero correction para mas velocidad pero menos precision
    send_cmd(inst, "SYST:ZCH OFF")
    send_cmd(inst, "SYST:ZCOR OFF")
    
    # Desactivamos el auto zero para augmentar la velocidad pero menos precision
    send_cmd(inst, "SYST:AZER OFF")
    
    # Ponemos el rango fijo (si no esta fijo hay trompicones por el cambio de rango entre mediciones)
    send_cmd(inst, "CURR:RANG:AUTO OFF")
    send_cmd(inst, "CURR:RANG 200E-6")
    
    # Establecemos el tiempo de integracion
    send_cmd(inst, "CURR:NPLC 0.01")  # 1 ciclo de red = equilibrio entre precisión y velocidad, minimo 0.01
    
    
    send_cmd(inst, "MED OFF")
    send_cmd(inst, "AVER OFF")
    
    
    
    ### ---------------------------------------------------------------------------------------------------- ###
    
    
    # ### Configurar medicion de voltaje
    
    
    # # Seleccionamos la funcion corriente
    # send_cmd(inst, 'SENS:FUNC "VOLT"')
    # send_cmd(inst, "CONF:VOLT")
    
    # # Desactivamos el zero check and zero correction para mas velocidad pero menos precision
    # send_cmd(inst, "SYST:ZCH OFF")
    # send_cmd(inst, "SYST:ZCOR OFF")
    
    # # Desactivamos el auto zero para augmentar la velocidad pero menos precision
    # send_cmd(inst, "SYST:AZER ON")
    
    # # Ponemos el rango fijo (si no esta fijo hay trompicones por el cambio de rango entre mediciones)
    # send_cmd(inst, "VOLT:RANG:AUTO OFF")
    # send_cmd(inst, "VOLT:RANG 200")
    
    # # Establecemos el tiempo de integracion
    # send_cmd(inst, "VOLT:NPLC 0.01")  # 1 ciclo de red = equilibrio entre precisión y velocidad, minimo 0.01
    
    
    # send_cmd(inst, "MED OFF")
    # send_cmd(inst, "AVER OFF")


    ### ---------------------------------------------------------------------------------------------------- ###


    ### ---------------------------------------------------------------------------------------------------- ###
    # Mirar lo del zero correction previ a les mesures !!!
    ### ---------------------------------------------------------------------------------------------------- ###
    
    
    ### Configurar medicion de carga
    
    
    # # Seleccionamos la funcion corriente
    # send_cmd(inst, 'SENS:FUNC "CHAR"')
    # send_cmd(inst, "CONF:CHAR")
    
    # # Desactivamos el zero check and zero correction para mas velocidad pero menos precision
    # send_cmd(inst, "SYST:ZCH OFF")
    # send_cmd(inst, "SYST:ZCOR OFF")
    
    # # Desactivamos el auto zero para augmentar la velocidad pero menos precision
    # send_cmd(inst, "SYST:AZER OFF")
    
    # # Ponemos el rango fijo (si no esta fijo hay trompicones por el cambio de rango entre mediciones)
    # send_cmd(inst, "CHAR:RANG:AUTO OFF")
    # send_cmd(inst, "CHAR:RANG 200E-9")
    
    # # Establecemos el tiempo de integracion
    # send_cmd(inst, "CHAR:NPLC 0.01")  # 1 ciclo de red = equilibrio entre precisión y velocidad, minimo 0.01



    ### ---------------------------------------------------------------------------------------------------- ###
    
    

    # Ajustamos los digitos de la pantalla y la desactivamos para augmentar el sampling rate
    send_cmd(inst, "DISP:DIG 4.5")
    send_cmd(inst, "DISP:ENAB ON")

    # Configuramos el Buffer
    send_cmd(inst, "TRIG:COUN INF")
    send_cmd(inst, f"TRAC:POIN {BUFFER_SIZE}")
    send_cmd(inst, "TRAC:FEED SENS;FEED:CONT NEXT")
    
    # input("Waiting to start press enter")

    # Iniciar adquisición
    send_cmd(inst, "INIT")
    
    time.sleep(0.5)
    
    # input("After init, press key to continue")

    print("Adquisición iniciada. Pulsa Ctrl+C para detenerla.")

    last_index = 0
    inst.timeout = 10000

    try:
        while True:
            # Consultar cuántos datos hay disponibles en el buffer
            print("Query how much points are in the buffer...")
            points = int(query_cmd(inst, ":TRAC:POIN?"))
            print("Points:", points[0])

            if points > last_index:
                # Leer solo los datos nuevos
                new_data = query_cmd(inst, f":TRAC:DATA? {last_index + 1},{points}")
                values = [float(x) for x in new_data.strip().split(",")]

                # Guardar en el CSV y mostrar por pantalla
                for i, val in enumerate(values, start=last_index + 1):
                    writer.writerow([i, val])
                    print(f"Medición {i}: {val}")

                file.flush()
                last_index = points

            time.sleep(READ_INTERVAL)

    except KeyboardInterrupt:
        print("Adquisición detenida por el usuario.")
        send_cmd(inst, ":ABOR")  # Detiene la adquisición

if __name__ == "__main__":
    values = main()

    # Separar los datos en lecturas, timestamps y estados si están intercalados
    read, timestamp, status = values[0::3], values[1::3], values[2::3]

    with open('CSV_File.csv', mode='w', newline='') as file:
        writer = csv.writer(file)

        # Escribir encabezados
        writer.writerow(['Time (s)', 'Current (A)'])

        # Escribir filas
        for timestamp_val, current_val in zip(timestamp, read):
            writer.writerow([timestamp_val, current_val])
            
            
    plt.figure(0)
    plt.plot(timestamp, read)

