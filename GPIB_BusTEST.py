import pyvisa
import time

# Crear ResourceManager
rm = pyvisa.ResourceManager()
lib = rm.visalib

# Abrir conexión con el Keithley (ajusta la dirección GPIB)
keithley = rm.open_resource("GPIB0::14::INSTR")
keithley.timeout = 10000

# Treure el mode remot
# keithley.control_ren(6)

# Configurar terminadores
#keithley.read_termination = '\n'
#keithley.write_termination = '\n'


def wait_for_srq(inst):
    """Espera a que bit 6 del status byte esté activo (SRQ)"""
    while True:
        try:
            stb = inst.stb  # Status Byte
            if stb & 64:
                return
        except Exception:
            continue
        
        

# Reseteo y configuración inicial
keithley.write("*RST")
keithley.write("STAT:PRES;*CLS")
keithley.write("STAT:MEAS:ENAB 512")
keithley.write("*SRE 1")


# ### Configurar medicion de corriente


# Seleccionamos la funcion corriente
keithley.write('SENS:FUNC "CURR"')   # Medir corriente (puedes usar 'VOLT', 'RES', etc.)
keithley.write("CONF:CURR")

# Desactivamos el zero check and zero correction para mas velocidad pero menos precision
keithley.write("SYST:ZCH OFF")
keithley.write("SYST:ZCOR OFF")

# Desactivamos el auto zero para augmentar la velocidad pero menos precision
keithley.write("SYST:AZER OFF")

# Ponemos el rango fijo (si no esta fijo hay trompicones por el cambio de rango entre mediciones)
keithley.write("CURR:RANG:AUTO OFF")
keithley.write("CURR:RANG 200E-6")

# Establecemos el tiempo de integracion
keithley.write("CURR:NPLC 0.01")  # 1 ciclo de red = equilibrio entre precisión y velocidad, minimo 0.01

# Desactivamos media y desviacion estandard
keithley.write("MED OFF")
keithley.write("AVER OFF")

# --- Configuración del Trigger ---
keithley.write(":ARM:SOUR BUS")        # Trigger ARM proviene del bus GPIB
keithley.write(":ARM:COUN 1")        # Adquisición infinita
keithley.write(":TRIG:COUN 1")         # Una medida por trigger


# Ajustamos los digitos de la pantalla y la desactivamos para augmentar el sampling rate
keithley.write("DISP:DIG 4.5")
keithley.write("DISP:ENAB ON")


# Iniciar adquisición
keithley.write("INIT")                 # Armar el sistema de trigger (queda esperando triggers)

# Configuramos el Buffer
# keithley.write("TRIG:COUN INF")
# keithley.write("TRAC:POIN 2500")
# keithley.write("TRAC:FEED SENS;FEED:CONT NEXT")


# En mode TALK no respon, s'ha de enviar això:
# keithley.write(":SYST:LOC")  # vuelve a LOCAL y luego podrás poner REMOTE
# keithley.write(":SYST:REM")  # vuelve a REMOTE, listo para recibir comandos

# No es pot enviar un READ? dos vegades, ja que sino interrumpeix el query


print("Keithley armado y esperando triggers por bus GPIB...")

try:
    while True:
        # Enviar trigger hardware (GET) por el bus GPIB
        # Recordem que perque ens respongui al trigger
        # la maquina ha d'estar en la capa ARM, no en IDLE (trigger model)
        code = keithley.assert_trigger()
        
        # Leer el valor medido (el 6514 lo devuelve tras cada trigger)
        # Recordem que la màquina ha d'estar en IDLE state per enviar les dades
        value = keithley.write(":FETCh?")
        
        # El GPIB proporciona un status byte en el bus de control que podem llegir
        # per saber quan ha acabat l'instrument la mesura.
        wait_for_srq(keithley)
        
        # Leer el valor medido (el 6514 lo devuelve tras cada trigger)
        # Recordem que la màquina ha d'estar en IDLE state per enviar les dades
        value = keithley.read()
        print("Medida:", value)
        
        # Ajusta el intervalo entre triggers según tu aplicación
        time.sleep(2)

except KeyboardInterrupt:
    print("Parando adquisición...")
    keithley.write("ABOR")  # Detener la adquisición
    keithley.close()
    
except Exception as e:
    print("Error:", e)
    keithley.write("ABOR")  # Detener la adquisición
    keithley.close()
