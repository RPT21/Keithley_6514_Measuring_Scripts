import pyvisa
import time
import csv

# Configura aquí la dirección de tu instrumento
GPIB_ADDRESS = "GPIB0::14::INSTR"  # Cambia si usas USB o es otro número

# Configura el tamaño del buffer y el tiempo de espera entre lecturas
BUFFER_SIZE = 2500
READ_INTERVAL = 0.5  # segundos
OUTPUT_CSV = "mediciones_keithley.csv"

# Inicializa conexión
rm = pyvisa.ResourceManager()
keithley = rm.open_resource(GPIB_ADDRESS)
keithley.read_termination = '\n'
keithley.timeout = 5000  # ms

# Inicializa archivo CSV
with open(OUTPUT_CSV, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Índice', 'Medición (valor)'])  # Encabezado

    # Configuración del Keithley 6514
    keithley.write("*RST")
    keithley.write(":TRAC:CLE")
    keithley.write(f":TRAC:POIN {BUFFER_SIZE}")
    keithley.write(":TRAC:FEED SENSE")           # Guardar valor medido
    keithley.write(":TRAC:FEED:CONT NEXT")       # Añadir al buffer en orden
    keithley.write(":TRIG:COUN INF")             # Medir indefinidamente
    keithley.write(":TRIG:SOUR IMM")             # Trigger inmediato
    keithley.write(":ARM:SOUR IMM")              # Armado inmediato
    keithley.write(":INIT")                      # Iniciar adquisición

    print("Adquisición iniciada. Pulsa Ctrl+C para detenerla.")

    last_index = 0

    try:
        while True:
            # Consultar cuántos datos hay disponibles en el buffer
            points = int(keithley.query(":TRAC:POIN?"))

            if points > last_index:
                # Leer solo los datos nuevos
                new_data = keithley.query(f":TRAC:DATA? {last_index + 1},{points}")
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
        keithley.write(":ABOR")  # Detiene la adquisición
