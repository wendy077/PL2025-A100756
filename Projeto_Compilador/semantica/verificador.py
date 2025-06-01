# semantica/verificador.py

class TabelaSimbolos:
    def __init__(self, pai=None):
        self.tabela = {}
        self.funcoes = {}
        self.pai = pai

    def declarar(self, nome, tipo):
        if nome in self.tabela:
            raise Exception(f"Erro: variável '{nome}' já declarada")
        self.tabela[nome] = tipo

    def tipo_de(self, nome):
        if nome in self.tabela:
            tipo_ou_valor = self.tabela[nome]
            if isinstance(tipo_ou_valor, tuple):
                match tipo_ou_valor[0]:
                    case 'num': return 'REAL' if isinstance(tipo_ou_valor[1], float) else 'INTEGER'
                    case 'str': return 'STRING'
                    case 'bool': return 'BOOLEAN'
            return tipo_ou_valor
        if self.pai:
            return self.pai.tipo_de(nome)
        raise Exception(f"Erro: variável '{nome}' não declarada")

    def declarar_funcao(self, nome, tipo_ret, params):
        if nome in self.funcoes:
            raise Exception(f"Erro: função/procedimento '{nome}' já declarado")
        self.funcoes[nome] = (tipo_ret, params)

    def info_funcao(self, nome):
        if nome in self.funcoes:
            return self.funcoes[nome]
        if self.pai:
            return self.pai.info_funcao(nome)
        if nome.lower() == 'length':
            return ('INTEGER', [{'id': 's', 'type': 'STRING'}])

        raise Exception(f"Erro: função/procedimento '{nome}' não declarada")
    
    
def verificar(ast):
    if 'program' not in ast:
        raise Exception("Erro: estrutura do programa inválida")

    corpo = ast['program']['body']
    tabela = TabelaSimbolos()

    # Declarar variáveis, constantes e funções
    for decl in corpo.get('decls', []):
        if isinstance(decl, list):
            for d in decl:
                tabela.declarar(d['id'], d['type'])
        elif isinstance(decl, dict):
            if decl.get('type') in {'function', 'procedure'}:
                tabela.declarar_funcao(decl['id'], decl.get('ret'), decl.get('params', []))
            elif decl.get('type') == 'const':
                tabela.declarar(decl['id'], decl['value'])   
            elif 'id' in decl and 'type' in decl:
                tabela.declarar(decl['id'], decl['type'])  
            

    # Verificar funções/procedimentos
    for decl in corpo.get('decls', []):
        if isinstance(decl, dict) and decl.get('type') in {'function', 'procedure'}:
            verificar_subprograma(decl, tabela)
            
    # Verificar instruções principais
    for instr in corpo.get('stmts', []):
        if instr:
            verificar_stmt(instr, tabela)
            
def verificar_subprograma(decl, tabela_global):
    escopo = TabelaSimbolos(pai=tabela_global)

    for p in decl['params']:
        escopo.declarar(p['id'], p['type'])

    if decl['type'] == 'function':
        escopo.declarar(decl['id'], decl['ret'])

    for d in decl['body'].get('decls', []):
        if isinstance(d, list):
            for v in d:
                escopo.declarar(v['id'], v['type'])
        elif isinstance(d, dict) and 'id' in d and 'type' in d:
            escopo.declarar(d['id'], d['type'])

    for s in decl['body'].get('stmts', []):
        if s:
            verificar_stmt(s, escopo)


def verificar_stmt(instr, tabela):
    match instr:
        case ('assign', ('id', nome), expr):
            tipo_var = tabela.tipo_de(nome)
            tipo_expr = verificar_expr(expr, tabela)
            if tipo_var != tipo_expr:
                raise Exception(f"Erro: tipo incompatível em '{nome} := ...'. Esperado {tipo_var}, obtido {tipo_expr}")

        case ('assign', ('array', nome, idx), expr):
            tipo = tabela.tipo_de(nome)
            if not isinstance(tipo, tuple) or tipo[0] != 'array':
                raise Exception(f"Erro: '{nome}' não é um array")
            tipo_idx = verificar_expr(idx, tabela)
            if tipo_idx != 'INTEGER':
                raise Exception("Erro: índice de array deve ser INTEGER")
            tipo_expr = verificar_expr(expr, tabela)
            tipo_array = tipo[1]
            if tipo_expr != tipo_array:
                raise Exception(f"Erro: tipo do array '{nome}' é {tipo[1]}, não {tipo_expr}")

        case ('writeln', exprs):
            for e in exprs:
                verificar_expr(e, tabela)

        case ('call', 'Write', exprs):  # suporte ao Write
            for e in exprs:
                verificar_expr(e, tabela)

        case ('readln', destinos):
            for destino in destinos:
                match destino:
                    case ('id', nome):
                        tabela.tipo_de(nome)
                    case ('array', nome, idx):
                        tipo = tabela.tipo_de(nome)
                        if not isinstance(tipo, tuple) or tipo[0] != 'array':
                            raise Exception(f"Erro: '{nome}' não é um array")
                        tipo_idx = verificar_expr(idx, tabela)
                        if tipo_idx != 'INTEGER':
                            raise Exception("Erro: índice de array deve ser INTEGER")

        case ('if', cond, entao, senao):
            if verificar_expr(cond, tabela) != 'BOOLEAN':
                raise Exception("Erro: expressão do IF deve ser BOOLEAN")

            bloco_then = entao if isinstance(entao, list) else [entao]
            for stmt in bloco_then:
                verificar_stmt(stmt, tabela)

            if senao:
                bloco_else = senao if isinstance(senao, list) else [senao]
                for stmt in bloco_else:
                    verificar_stmt(stmt, tabela)

        case ('while', cond, corpo):
            if verificar_expr(cond, tabela) != 'BOOLEAN':
                raise Exception("Erro: expressão do WHILE deve ser BOOLEAN")
            verificar_stmt(corpo, tabela)

        case ('for', nome, ini, fim, direcao, corpo):
            if tabela.tipo_de(nome) != 'INTEGER':
                raise Exception("Erro: variável de controlo no FOR deve ser INTEGER")
            if verificar_expr(ini, tabela) != 'INTEGER' or verificar_expr(fim, tabela) != 'INTEGER':
                raise Exception("Erro: limites do FOR devem ser INTEGER")
            verificar_stmt(corpo, tabela)

        case ('call', nome, args):
            tipo, params = tabela.info_funcao(nome)
            if len(args) != len(params):
                raise Exception(f"Erro: chamada a '{nome}' com número errado de argumentos")
            for a, p in zip(args, params):
                tipo_arg = verificar_expr(a, tabela)
                if tipo_arg != p['type']:
                    raise Exception(f"Erro: argumento inválido para '{nome}': esperado {p['type']}, obtido {tipo_arg}")

        case list():
            for s in instr:
                if s: verificar_stmt(s, tabela)

        case _:
            raise Exception(f"Erro: instrução desconhecida {instr}")


def verificar_expr(expr, tabela):
    match expr:
        case ('num', v):
            return 'REAL' if isinstance(v, float) else 'INTEGER'
        
        case ('str', _):
            return 'STRING'
        
        case ('id', nome):
            tipo = tabela.tipo_de(nome)
            return tipo
        
        case ('bool', _):
            return 'BOOLEAN'
        
        case ('array', nome, idx):
            tipo = tabela.tipo_de(nome)

            # Acesso a strings como arrays
            if tipo == 'STRING':
                tipo_idx = verificar_expr(idx, tabela)
                if tipo_idx != 'INTEGER':
                    raise Exception("Erro: índice de string deve ser INTEGER")
                return 'STRING'
            
            if not isinstance(tipo, tuple) or tipo[0] != 'array':
                raise Exception(f"Erro: '{nome}' não é um array")
            tipo_idx = verificar_expr(idx, tabela)
            if tipo_idx != 'INTEGER':
                raise Exception("Erro: índice de array deve ser INTEGER")

            if isinstance(idx, tuple) and idx[0] == 'num':
                valor_idx = idx[1]
                inicio = tipo[2]
                fim = tipo[2] + tipo[3] - 1
                if not (inicio <= valor_idx <= fim):
                    raise Exception(f"Erro: índice {valor_idx} fora dos limites [{inicio}..{fim}] de '{nome}'")
            return tipo[1]
        
        case ('div', e1, e2):
            t1 = verificar_expr(e1, tabela)
            t2 = verificar_expr(e2, tabela)
            if t1 == t2 == 'INTEGER':
                return 'INTEGER'
            raise Exception(f"Erro: operador 'div' requer INTEGER, obtido {t1} e {t2}")

        case ('mod', e1, e2):
            t1 = verificar_expr(e1, tabela)
            t2 = verificar_expr(e2, tabela)
            if t1 == t2 == 'INTEGER':
                return 'INTEGER'
            raise Exception(f"Erro: operador 'mod' requer INTEGER, obtido {t1} e {t2}")

        case ('not', e):
            if verificar_expr(e, tabela) != 'BOOLEAN':
                raise Exception("Erro: operador 'not' requer BOOLEAN")
            return 'BOOLEAN'
        
        case (op, e1, e2) if op in {'+', '-', '*', '/'}:
            t1 = verificar_expr(e1, tabela)
            t2 = verificar_expr(e2, tabela)
            if t1 == t2 == 'INTEGER':
                return 'INTEGER'
            if (t1, t2) in [('INTEGER', 'REAL'), ('REAL', 'INTEGER'), ('REAL', 'REAL')]:
                return 'REAL'
            raise Exception(f"Erro: operador '{op}' requer INTEGER ou REAL, obtido {t1} e {t2}")
        
        case (op, e1, e2) if op in {'=', '<>', '<', '<=', '>', '>='}:
            t1 = verificar_expr(e1, tabela)
            t2 = verificar_expr(e2, tabela)
            if t1 != t2:
                raise Exception(f"Erro: comparação entre tipos diferentes: {t1} e {t2}")
            return 'BOOLEAN'
        
        case (op, e1, e2) if op in {'and', 'or'}:
            t1 = verificar_expr(e1, tabela)
            t2 = verificar_expr(e2, tabela)
            if t1 == t2 == 'BOOLEAN':
                return 'BOOLEAN'
            raise Exception(f"Erro: operador lógico '{op}' requer BOOLEAN, obtido {t1} e {t2}")
        
        case ('call', nome, args):
            tipo_ret, params = tabela.info_funcao(nome)
            if len(args) != len(params):
                raise Exception(f"Erro: chamada a '{nome}' com número errado de argumentos")
            for a, p in zip(args, params):
                tipo_arg = verificar_expr(a, tabela)
                if tipo_arg != p['type']:
                    raise Exception(f"Erro: argumento inválido para '{nome}': esperado {p['type']}, obtido {tipo_arg}")
            if tipo_ret is None:
                raise Exception(f"Erro: '{nome}' é procedimento, não retorna valor")
            return tipo_ret
        
        case _:
            raise Exception(f"Erro: expressão inválida {expr}")