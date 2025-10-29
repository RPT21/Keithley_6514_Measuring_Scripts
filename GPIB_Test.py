import pyvisa
import time
import csv
import matplotlib.pyplot as plt
import numpy as np

# Cambia la dirección GPIB según tu configuración
GPIB_ADDRESS = 'GPIB0::14::INSTR'  # GPIB0 es el bus, 14 es la dirección del Keithley
number_of_samples = 2500

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

def main(measure):
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
    
    
    ### Configurar medicion de corriente
    
    if measure == "current":
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
    
    elif measure == "voltage":
        # Seleccionamos la funcion corriente
        send_cmd(inst, 'SENS:FUNC "VOLT"')
        send_cmd(inst, "CONF:VOLT")
        
        # Desactivamos el zero check and zero correction para mas velocidad pero menos precision
        send_cmd(inst, "SYST:ZCH OFF")
        send_cmd(inst, "SYST:ZCOR OFF")
        
        # Desactivamos el auto zero para augmentar la velocidad pero menos precision
        send_cmd(inst, "SYST:AZER OFF")
        
        # Ponemos el rango fijo (si no esta fijo hay trompicones por el cambio de rango entre mediciones)
        send_cmd(inst, "VOLT:RANG:AUTO OFF")
        send_cmd(inst, "VOLT:RANG 200")
        
        # Establecemos el tiempo de integracion
        send_cmd(inst, "VOLT:NPLC 0.01")  # 1 ciclo de red = equilibrio entre precisión y velocidad, minimo 0.01
        
        
        send_cmd(inst, "MED OFF")
        send_cmd(inst, "AVER OFF")


    ### ---------------------------------------------------------------------------------------------------- ###


    ### ---------------------------------------------------------------------------------------------------- ###
    # Mirar lo del zero correction previ a les mesures !!!
    ### ---------------------------------------------------------------------------------------------------- ###
    
    
    ### Configurar medicion de carga
    
    elif measure == "charge":
        # Seleccionamos la funcion corriente
        send_cmd(inst, 'SENS:FUNC "CHAR"')
        send_cmd(inst, "CONF:CHAR")
        
        # Desactivamos el zero check and zero correction para mas velocidad pero menos precision
        send_cmd(inst, "SYST:ZCH OFF")
        send_cmd(inst, "SYST:ZCOR OFF")
        
        # Desactivamos el auto zero para augmentar la velocidad pero menos precision
        send_cmd(inst, "SYST:AZER OFF")
        
        # Ponemos el rango fijo (si no esta fijo hay trompicones por el cambio de rango entre mediciones)
        send_cmd(inst, "CHAR:RANG:AUTO OFF")
        send_cmd(inst, "CHAR:RANG 200E-9")
        
        # Establecemos el tiempo de integracion
        send_cmd(inst, "CHAR:NPLC 0.01")  # 1 ciclo de red = equilibrio entre precisión y velocidad, minimo 0.01



    ### ---------------------------------------------------------------------------------------------------- ###
    
    else:
        raise Exception("Error invalid measure parameter")

    # Ajustamos los digitos de la pantalla y la desactivamos para augmentar el sampling rate
    send_cmd(inst, "DISP:DIG 4.5")
    send_cmd(inst, "DISP:ENAB OFF")

    # Configuramos el Buffer
    send_cmd(inst, f"TRIG:COUN {number_of_samples}")
    send_cmd(inst, f"TRAC:POIN {number_of_samples}")
    send_cmd(inst, "TRAC:FEED SENS;FEED:CONT NEXT")

    # Iniciar adquisición
    send_cmd(inst, "INIT")  

    print("Esperando a que se llene el buffer (SRQ)...")
    wait_for_srq(inst)
    print("SRQ recibido, leyendo estado...")

    meas_status = query_cmd(inst, "STAT:MEAS?")
    print("STAT:MEAS? =", meas_status)

    print("Leyendo TRAC:DATA...")
    reading_data = query_cmd(inst, "TRAC:DATA?")

    try:
        values = [float(x) for x in reading_data.split(',')]

        if verbose:
            print("Mediciones:")
            for i, v in enumerate(values, 1):
                print(f"{i}: {v:.3e} A")

    except ValueError:
        print("Error al procesar los datos:", reading_data)
        values = []

    # print("\nPara repetir, reactiva el buffer con: FEED:CONT NEXT")
    # send_cmd(inst, "FEED:CONT NEXT")

    inst.close()
    return values

if __name__ == "__main__":
    
    measure = "current" # It can be current, voltage, charge
    param_name = {"voltage":"Voltage (V)", "current":"Current (A)", "charge":"Coulombs (uC)"}
    
    values = main(measure)

    # Separar los datos en lecturas, timestamps y estados si están intercalados
    read, timestamp, status = values[0::3], values[1::3], values[2::3]
    
    diff_time = timestamp[1] - timestamp[0]
    timestamp_aux = np.linspace(0, diff_time * 2499, 2500)

    with open('CSV_File.csv', mode='w', newline='') as file:
        writer = csv.writer(file)

        # Escribir encabezados
        writer.writerow(['Time (s)', param_name[measure]])

        # Escribir filas
        for timestamp_val, current_val in zip(timestamp_aux, read):
            writer.writerow([timestamp_val, current_val])

# %%

    plt.figure()
    plt.plot(timestamp_aux, read)
    plt.xlabel("Time (s)")
    plt.ylabel(param_name[measure])
    plt.tight_layout()
    plt.show()
    
    

