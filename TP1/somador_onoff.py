import sys

def somador_onoff(texto):
    estado = False
    soma = 0
    j = 0

    while j < len(texto):
        # Verificar se o caractere é um dígito
        if texto[j].isdigit():
            valor = 0
            # Enquanto houver números consecutivos, formar o valor
            while j < len(texto) and texto[j].isdigit():
                valor = valor * 10 + int(texto[j])
                j += 1
            # Somar o valor se o estado estiver "on"
            if estado:
                soma += valor
        # Ativar o estado "on"
        elif texto[j:j+2].lower() == 'on':
            estado = True
            j += 2
        # Desativar o estado "off"
        elif texto[j:j+3].lower() == 'off':
            estado = False
            j += 3
        # Caso encontre o caractere '=', imprime o resultado
        elif texto[j] == '=':
            print(soma)
            j += 1
        # Caso contrário, ignora o caractere
        else:
            j += 1

# Processa a entrada linha por linha
for linha in sys.stdin:
    somador_onoff(linha)
