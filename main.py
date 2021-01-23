import os
import speedtest

st = speedtest.Speedtest()
retrieving_data = True

def simple_test():
    os.system('cls')
    print('REALIZANDO TEST SIMPLE, AGUARDE PORFAVOR...\n')
    print(f'Su velocidad de descarga es de {st.download()//10**6} Mbps.\n')

def full_test():
    os.system('cls')
    print('REALIZANDO TEST FULL, AGUARDE PORFAVOR...\n')
    print(f'Su velocidad de descarga es de {st.download()//10**6} Mbps.')
    print(f'Su velocidad de carga es de {st.upload()//10**6} Mbps.')
    print(f'Su ping es de {st.results.ping} ms.\n')

def testing():
    print('\n        SPEEDTESTER\n\n¿Qué test desea realizar?')
    test = str(input('  simple (1) / full (2)\n\n'))

    while retrieving_data:
        if test in ['simple', 'Simple', 'SIMPLE', '1']:
            simple_test()
            break
        elif test in ['full', 'Full', 'FULL', '2']:
            full_test()
            break
        else:
            os.system('cls')
            print('Selecciona una opción correcta:')
            test = str(input('  simple (1) / full (2)\n\n'))
    
    print('---------------------------------------')
    print('Muchas gracias por utilizar SpeedTester.\nPresione cualquier tecla para finalizar.')
    print('---------------------------------------')
    input()

testing()