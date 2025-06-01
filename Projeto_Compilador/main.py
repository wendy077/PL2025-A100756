# main.py

import sys
from parser.pascal_parser import parse
from semantica.verificador import verificar
from gerador.gerador_vm import GeradorVM
import os

def compilar(ficheiro_entrada):
    with open(ficheiro_entrada, 'r', encoding='utf-8') as f:
        codigo = f.read()
    
    # Etapa 1: Parser
    ast = parse(codigo)

    # Etapa 2: Verificador semântico
    verificar(ast)

    # Etapa 3: Geração de código VM
    gerador = GeradorVM()
    codigo_vm = gerador.gerar(ast)

    # Escreve para ficheiro .vm
    ficheiro_saida = os.path.splitext(ficheiro_entrada)[0] + '.vm'
    with open(ficheiro_saida, 'w', encoding='utf-8') as f:
        for linha in codigo_vm:
            f.write(linha + '\n')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python main.py <ficheiro.pas>")
        sys.exit(1)

    ficheiro_entrada = sys.argv[1]
    try:
        compilar(ficheiro_entrada)
    except Exception as e:
        print(f"❌ Erro na compilação: {e}")
