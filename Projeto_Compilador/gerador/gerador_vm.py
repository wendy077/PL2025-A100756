# gerador/gerador_vm.py

class GeradorVM:
    def __init__(self):
        self.codigo = []        # Lista com código gerado
        self.vars = {}        # Nome de variável -> endereço
        self.arrays = {}      # Nome do array -> informações de base/start/size
        self.next_addr = 0      # Endereço seguinte disponível
        self.funcoes = {}     # Nome -> AST da função
        self.tipos = {}        # Nome -> tipo da variável
        self.label_count = 0   # Contador para labels únicos

    def _registar_variavel_global(self, d):
        tipo = d['type']
        if isinstance(tipo, tuple) and tipo[0] == 'array':
            tamanho = tipo[3]
            self.codigo.append(f"PUSHI {tamanho}")
            self.codigo.append("ALLOCN")
            self.codigo.append(f"STOREG {self.next_addr}")
            self.arrays[d['id']] = {
                'base': self.next_addr,
                'start': tipo[2],
                'size': tamanho
            }
        self.vars[d['id']] = self.next_addr
        self.tipos[d['id']] = tipo if isinstance(tipo, str) else tipo[0].upper()
        self.next_addr += 1

    def gerar(self, ast):
        if 'program' not in ast:
            raise Exception("Erro: AST inválida")

        corpo = ast['program']['body']

        # Declarações
        for decls in corpo.get('decls', []):
            if isinstance(decls, dict) and decls.get('type') in {'function', 'procedure'}:
                self.funcoes[decls['id']] = decls

                if decls['type'] == 'function':
                    self.vars[decls['id']] = self.next_addr
                    self.tipos[decls['id']] = decls['ret']
                    self.next_addr += 1
                continue  # ignora

            if isinstance(decls, list):
                for d in decls:
                    if d.get('type') == 'const':
                        self.vars[d['id']] = self.next_addr
                        v = d['value']
                        match v[0]:
                            case 'num':
                                self.codigo.append(f'PUSHF {v[1]}' if isinstance(v[1], float) else f'PUSHI {v[1]}')
                                self.tipos[d['id']] = 'REAL' if isinstance(v[1], float) else 'INTEGER'
                            case 'str':
                                self.codigo.append(f'PUSHS "{v[1]}"')
                                self.tipos[d['id']] = 'STRING'
                            case 'bool':
                                self.codigo.append(f'PUSHI {1 if v[1] else 0}')
                                self.tipos[d['id']] = 'BOOLEAN'
                            case _:
                                raise Exception(f"Valor inválido em const: {v}")
                        self.codigo.append(f'STOREG {self.next_addr}')
                        self.next_addr += 1
                    else:
                        self._registar_variavel_global(d)
                        
            elif isinstance(decls, dict):
                if decls.get('type') == 'const':
                    self.vars[decls['id']] = self.next_addr
                    v = decls['value']
                    match v[0]:
                        case 'num':
                            self.codigo.append(f'PUSHF {v[1]}' if isinstance(v[1], float) else f'PUSHI {v[1]}')
                            self.tipos[decls['id']] = 'REAL' if isinstance(v[1], float) else 'INTEGER'
                        case 'str':
                            self.codigo.append(f'PUSHS "{v[1]}"')
                            self.tipos[decls['id']] = 'STRING'
                        case 'bool':
                            self.codigo.append(f'PUSHI {1 if v[1] else 0}')
                            self.tipos[decls['id']] = 'BOOLEAN'
                        case _:
                            raise Exception(f"Valor inválido em const: {v}")
                    self.codigo.append(f'STOREG {self.next_addr}')
                    self.next_addr += 1
                else:
                    self._registar_variavel_global(decls)


        # Corpo principal
        self.codigo.insert(0, 'START')
        for stmt in corpo.get('stmts', []):
            if stmt:
                self.gen_stmt(stmt)

        self.codigo.append('STOP')

        # Funções e procedimentos
        for nome, decl in self.funcoes.items():
            self.gen_func(decl)

        return self.codigo

    def coerce_real(self, t1, t2):
        if t1 == 'INTEGER' and t2 == 'REAL':
            self.codigo.insert(-2, 'ITOF;')
        elif t2 == 'INTEGER' and t1 == 'REAL':
            self.codigo.insert(-1, 'ITOF;')

    def tipo_expr(self, expr):
        match expr:
            case ('num', v):
                return 'REAL' if isinstance(v, float) else 'INTEGER'
            case ('str', _):  
                return 'STRING'
            case ('id', nome):
                if nome in self.tipos:
                    return self.tipos[nome]
                raise Exception(f"Erro: tipo de variável '{nome}' desconhecido")
            case ('+', e1, e2) | ('-', e1, e2) | ('*', e1, e2) | ('/', e1, e2):
                t1 = self.tipo_expr(e1)
                t2 = self.tipo_expr(e2)
                if t1 == t2:
                    return t1
                if {'REAL', 'INTEGER'} == {t1, t2}:
                    return 'REAL'
            case _:
                return 'INTEGER'

    def gen_func(self, decl):
        lbl_inicio = f"FN{decl['id']}"
        self.codigo.append(f'{lbl_inicio}:')
        old_vars = self.vars.copy()
        local_base = self.next_addr

        for p in decl['params']:
            self.vars[p['id']] = self.next_addr
            self.tipos[p['id']] = p['type'] 
            self.next_addr += 1

        for d in decl['body'].get('decls', []):
            if isinstance(d, list):
                for v in d:
                    self.vars[v['id']] = self.next_addr
                    self.tipos[v['id']] = v['type']  
                    self.next_addr += 1

            elif isinstance(d, dict) and 'id' in d and 'type' in d:
                    self.vars[d['id']] = self.next_addr
                    self.tipos[d['id']] = d['type']
                    self.next_addr += 1

        for stmt in decl['body'].get('stmts', []):
            if stmt:
                self.gen_stmt(stmt)

        self.codigo.append("RETURN")
        self.vars = old_vars

    def gen_stmt(self, stmt):
        match stmt:
            case ('assign', ('id', nome), expr):
                self.gen_expr(expr)
                self.codigo.append(f'STOREG {self.vars[nome]}')

            case ('assign', ('array', nome, idx_expr), valor_expr):
                tipo = self.arrays[nome]
                self.gen_expr(valor_expr)                  # valor
                self.codigo.append(f'PUSHG {tipo["base"]}')  # base
                self.gen_expr(idx_expr)                    # índice
                if tipo["start"] != 0:
                    self.codigo.append(f'PUSHI {tipo["start"]}')
                    self.codigo.append('SUB')              
                self.codigo.append('STOREN')

            case ('writeln', exprs):
                for e in exprs:
                    tipo = self.tipo_expr(e)
                    self.gen_expr(e)
                    if tipo == 'INTEGER':
                        self.codigo.append('STRI')
                        self.codigo.append('WRITES')
                    elif tipo == 'REAL':
                        self.codigo.append('WRITEF')
                    elif tipo == 'STRING':
                        self.codigo.append('WRITES')
                self.codigo.append('WRITELN')

            case ('call', 'Write', exprs):
                for e in exprs:
                    tipo = self.tipo_expr(e)
                    self.gen_expr(e)
                    if tipo == 'INTEGER':
                        self.codigo.append('WRITEI')
                    elif tipo == 'REAL':
                        self.codigo.append('WRITEF')
                    elif tipo == 'STRING':
                        self.codigo.append('WRITES')

            case ('readln', destinos):
                for destino in destinos:
                    match destino:
                        case ('id', nome):
                            self.codigo.append('READ')
                            tipo = self.tipos[nome]
                            if tipo == 'INTEGER':
                                self.codigo.append('ATOI')
                            elif tipo == 'REAL':
                                self.codigo.append('ATOF')
                            self.codigo.append(f'STOREG {self.vars[nome]}')
                            
                        case ('array', nome, idx_expr):
                            tipo = self.arrays[nome] 
                            self.codigo.append(f'PUSHG {tipo["base"]}')
                            self.gen_expr(idx_expr)
                            if tipo["start"] != 0:
                                self.codigo.append(f'PUSHI {tipo["start"]}')
                                self.codigo.append('SUB')
                                self.codigo.append('READ')
                                self.codigo.append('ATOI')
                                self.codigo.append('STOREN')

            case ('call', 'Read', nomes):
                for nome in nomes:
                    self.codigo.append('READ')
                    self.codigo.append('ATOI')
                    self.codigo.append(f'STOREG {self.vars[nome]}')

            case ('if', cond, entao, senao):
                self.gen_expr(cond)
                lbl_else = self.nova_label()
                lbl_fim = self.nova_label()
                self.codigo.append(f'JZ {lbl_else}')

                then_block = entao if isinstance(entao, list) else [entao]
                for stmt in then_block:
                    self.gen_stmt(stmt)

                self.codigo.append(f'JUMP {lbl_fim}')
                self.codigo.append(f'{lbl_else}:')

                if senao:
                    else_block = senao if isinstance(senao, list) else [senao]
                    for stmt in else_block:
                        self.gen_stmt(stmt)

                self.codigo.append(f'{lbl_fim}:')

            case ('while', cond, corpo):
                lbl_ini = self.nova_label()
                lbl_fim = self.nova_label()
                self.codigo.append(f'{lbl_ini}:')
                self.gen_expr(cond)
                self.codigo.append(f'JZ {lbl_fim}')
                self.gen_stmt(corpo)
                self.codigo.append(f'JUMP {lbl_ini}')
                self.codigo.append(f'{lbl_fim}:')

            case ('for', nome, ini, fim, direcao, corpo):
                addr = self.vars[nome]
                lbl_ini = self.nova_label()
                lbl_fim = self.nova_label()

                self.gen_expr(ini)
                self.codigo.append(f'STOREG {addr}')

                self.codigo.append(f'{lbl_ini}:')
                self.codigo.append(f'PUSHG {addr}')
                self.gen_expr(fim)
                if direcao.lower() == 'to':
                    self.codigo.append('INFEQ')     
                else:
                    self.codigo.append('SUPEQ')     

                self.codigo.append(f'JZ {lbl_fim}')

                self.gen_stmt(corpo)

                self.codigo.append(f'PUSHG {addr}')
                self.codigo.append('PUSHI 1')
                self.codigo.append('ADD' if direcao.lower() == 'to' else 'SUB')
                self.codigo.append(f'STOREG {addr}')
                self.codigo.append(f'JUMP {lbl_ini}')
                self.codigo.append(f'{lbl_fim}:')

            case ('call', nome, args):
                func = self.funcoes[nome]
                
                param_base = self.next_addr

                for i, a in enumerate(args):
                    self.gen_expr(a)
                    param_addr = param_base + i
                    self.codigo.append(f'STOREG {param_addr}')

                self.codigo.append(f'PUSHA FN{nome}')
                self.codigo.append('CALL')

                if 'ret' in func:
                    self.codigo.append(f'PUSHG {self.vars[nome]}')

            case list():
                for s in stmt:
                    if s:
                        self.gen_stmt(s)

            case _:
                raise Exception(f"Erro: instrução desconhecida {stmt}")

    def gen_expr(self, expr):
        match expr:
            case ('num', valor):
                if isinstance(valor, float):
                    self.codigo.append(f'PUSHF {valor}')
                else:
                    self.codigo.append(f'PUSHI {valor}')

            case ('str', texto):
                if len(texto) == 1:
                    self.codigo.append(f'PUSHI {ord(texto)}')  
                else:
                    self.codigo.append(f'PUSHS "{texto}"')

            case ('id', nome):
                self.codigo.append(f'PUSHG {self.vars[nome]}')

            case ('bool', valor):
                if valor is True:
                    self.codigo.append('PUSHI 1')
                else:
                    self.codigo.append('PUSHI 0')

            case ('array', nome, idx_expr):
                if nome in self.arrays:
                    tipo = self.arrays[nome]
                    self.codigo.append(f'PUSHG {tipo["base"]}')  
                    self.gen_expr(idx_expr)                    
                    if tipo["start"] != 0:
                        self.codigo.append(f'PUSHI {tipo["start"]}')
                        self.codigo.append('SUB')
                    self.codigo.append('LOADN')

                elif nome in self.vars and self.tipo_expr(('id', nome)) == 'STRING':
                        self.gen_expr(('id', nome))      
                        self.gen_expr(idx_expr)          
                        self.codigo.append('PUSHI 1')
                        self.codigo.append('SUB')         
                        self.codigo.append('CHARAT')     
                else:
                    raise Exception(f"Erro: '{nome}' não é array nem string indexável")
                
            case ('not', e):
                self.gen_expr(e)
                self.codigo.append('NOT')

            case ('+', e1, e2):
                t1 = self.tipo_expr(e1)
                t2 = self.tipo_expr(e2)
                self.gen_expr(e1)
                self.gen_expr(e2)
                if t1 == t2 == 'STRING':
                    self.codigo.append('CONCAT')
                elif {'REAL', 'INTEGER'} == {t1, t2} or t1 == t2 == 'REAL':
                    self.coerce_real(t1, t2)
                    self.codigo.append('FADD')
                else:
                    self.codigo.append('ADD')

            case ('-', e1, e2):
                t1 = self.tipo_expr(e1)
                t2 = self.tipo_expr(e2)
                self.gen_expr(e1)
                self.gen_expr(e2)
                if {'REAL', 'INTEGER'} == {t1, t2} or t1 == t2 == 'REAL':
                    self.coerce_real(t1, t2)
                    self.codigo.append('FSUB')
                else:
                    self.codigo.append('SUB')

            case ('*', e1, e2):
                t1 = self.tipo_expr(e1)
                t2 = self.tipo_expr(e2)
                self.gen_expr(e1)
                self.gen_expr(e2)
                if {'REAL', 'INTEGER'} == {t1, t2} or t1 == t2 == 'REAL':
                    self.coerce_real(t1, t2)
                    self.codigo.append('FMUL')
                else:
                    self.codigo.append('MUL')

            case ('/', e1, e2):
                t1 = self.tipo_expr(e1)
                t2 = self.tipo_expr(e2)
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.coerce_real(t1, t2)
                self.codigo.append('FDIV')

            case ('=', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('EQUAL')  

            case ('<>', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('EQUAL')
                self.codigo.append('NOT')

            case ('<', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('INF')    

            case ('<=', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('INFEQ')

            case ('>', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('SUP')    

            case ('>=', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('SUPEQ')  

            case ('and', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('AND')

            case ('or', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('OR')

            case ('div', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('DIV')

            case ('mod', e1, e2):
                self.gen_expr(e1)
                self.gen_expr(e2)
                self.codigo.append('MOD')

            case ('call', 'length', [arg]):
                self.gen_expr(arg)
                self.codigo.append('STRLEN')  

            case ('call', nome, args):
                func = self.funcoes[nome]
                
                param_base = self.next_addr

                for i, a in enumerate(args):
                    self.gen_expr(a)
                    param_addr = param_base + i
                    self.codigo.append(f'STOREG {param_addr}')

                self.codigo.append(f'PUSHA FN{nome}')
                self.codigo.append('CALL')

                if 'ret' in func:
                    self.codigo.append(f'PUSHG {self.vars[nome]}')  

            case _:
                raise Exception(f"Erro: expressão desconhecida {expr}")


    def nova_label(self):
        lbl = f"L{self.label_count}"
        self.label_count += 1
        return lbl