# parser/pascal_parser.py
import ply.yacc as yacc
from lexer.pascal_lexer import tokens

# Precedências para evitar ambiguidade com IF/ELSE
precedence = (
    ('nonassoc', 'IFX'),
    ('nonassoc', 'ELSE'),
    ('left', 'LBRACK', 'RBRACK')
)

ast = {}

# -----------------------
# Programa principal
# -----------------------

def p_program(p):
    '''program : PROGRAM ID SEMI main_block DOT'''
    ast['program'] = {'name': p[2], 'body': p[4]}
    p[0] = ast

def p_main_block(p):
    '''main_block : decl_segment BEGIN stmt_list END
                  | BEGIN stmt_list END'''
    if len(p) == 5:
        p[0] = {'decls': p[1], 'stmts': p[3]}
    else:
        p[0] = {'decls': [], 'stmts': p[2]}

# -----------------------
# Declarações
# -----------------------

def p_decl_segment(p):
    '''decl_segment : decl_segment decl_block
                    | decl_block'''
    if len(p) == 3:
        p[0] = p[1] + p[2]
    else:
        p[0] = p[1]

def p_block(p):
    '''block : decl_segment BEGIN stmt_list END
             | BEGIN stmt_list END'''
    if len(p) == 5:
        p[0] = {'decls': p[1], 'stmts': p[3]}
    else:
        p[0] = {'decls': [], 'stmts': p[2]}

def p_decl_block_var(p):
    '''decl_block : VAR decls
                  | CONST const_decls'''
    p[0] = p[2]  

def p_const_decls(p):
    '''const_decls : const_decls const_decl
                   | const_decl'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_const_decl(p):
    '''const_decl : ID EQUAL expr SEMI'''
    p[0] = {'type': 'const', 'id': p[1], 'value': p[3]}

def p_decl_block_single(p):
    '''decl_block : decl'''
    p[0] = [p[1]]

def p_decls(p):
    '''decls : decls decl
             | decl'''
    if len(p) == 3:
        if isinstance(p[2], list):
            p[0] = p[1] + p[2]
        else:
            p[0] = p[1] + [p[2]]
    else:
        p[0] = p[1] if isinstance(p[1], list) else [p[1]]

def p_decl_var(p):
    '''decl : id_list COLON type SEMI'''
    p[0] = [{'id': i, 'type': p[3]} for i in p[1]]

def p_decl_array(p):
    '''decl : id_list COLON ARRAY LBRACK NUMBER DOTDOT NUMBER RBRACK OF type SEMI'''
    base = int(p[5])
    end = int(p[7])
    size = end - base + 1
    p[0] = [{'id': i, 'type': ('array', p[10], base, size)} for i in p[1]]

def p_decl_function(p):
    '''decl : FUNCTION ID LPAREN param_list RPAREN COLON type SEMI block SEMI'''
    p[0] = {'type': 'function', 'id': p[2], 'params': p[4], 'ret': p[7], 'body': p[9]}

def p_decl_procedure(p):
    '''decl : PROCEDURE ID LPAREN param_list RPAREN SEMI block SEMI'''
    p[0] = {'type': 'procedure', 'id': p[2], 'params': p[4], 'body': p[7]}

def p_param(p):
    '''param : id_list COLON type'''
    p[0] = [{'id': i, 'type': p[3]} for i in p[1]]

def p_param_list(p):
    '''param_list : param_list SEMI param
                  | param'''
    if len(p) == 4:
        p[0] = p[1] + p[3]
    else:
        p[0] = p[1]

def p_id_list(p):
    '''id_list : ID
               | ID COMMA id_list'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_type(p):
    '''type : INTEGER
            | REAL
            | BOOLEAN
            | STRING '''
    p[0] = p[1].upper() if isinstance(p[1], str) and p[1].lower() in ['integer', 'real', 'boolean', 'string'] else p[1]

def p_expr_bool(p):
    '''expr : TRUE
            | FALSE'''
    valor = True if p[1].lower() == 'true' else False
    p[0] = ('bool', valor)


# -----------------------
# Instruções
# -----------------------

def p_stmt_list(p):
    '''stmt_list : stmt_list stmt
                 | stmt'''
    if len(p) == 3:
        if p[2] is not None:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = p[1]
    else:
        p[0] = [p[1]] if p[1] is not None else []


def p_compound_stmt(p):
    '''compound_stmt : BEGIN stmt_list END'''
    p[0] = p[2]

def p_stmt(p):
    '''stmt : assign_stmt
            | writeln_stmt
            | readln_stmt
            | if_stmt
            | while_stmt
            | for_stmt
            | call_stmt
            | compound_stmt
            | SEMI'''
    p[0] = p[1] if p[1] != ';' else None


def p_assign_stmt(p):
    '''assign_stmt : lvalue ASSIGN expr
                   | lvalue ASSIGN expr SEMI'''
    p[0] = ('assign', p[1], p[3])


def p_lvalue_id(p):
    '''lvalue : ID'''
    p[0] = ('id', p[1])

def p_lvalue_array(p):
    '''lvalue : ID LBRACK expr RBRACK'''
    p[0] = ('array', p[1], p[3])

def p_lvalue_list(p):
    '''lvalue_list : lvalue
                   | lvalue COMMA lvalue_list'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]


def p_writeln_stmt(p):
    '''writeln_stmt : WRITELN LPAREN expr_list RPAREN
                    | WRITELN LPAREN expr_list RPAREN SEMI'''
    p[0] = ('writeln', p[3])


def p_readln_stmt(p):
    '''readln_stmt : READLN LPAREN lvalue_list RPAREN
                   | READLN LPAREN lvalue_list RPAREN SEMI'''
    p[0] = ('readln', p[3])


def p_if_stmt(p):
    '''if_stmt : IF expr THEN stmt %prec IFX
               | IF expr THEN stmt ELSE stmt'''

    # Garante que `then` e `else` sempre sejam listas de instruções
    then_part = p[4] if isinstance(p[4], list) else [p[4]]
    else_part = p[6] if len(p) == 7 and isinstance(p[6], list) else [p[6]] if len(p) == 7 else None

    p[0] = ('if', p[2], then_part, else_part)


def p_while_stmt(p):
    '''while_stmt : WHILE expr DO stmt'''
    p[0] = ('while', p[2], p[4])


def p_for_stmt(p):
    '''for_stmt : FOR ID ASSIGN expr direction expr DO stmt'''
    p[0] = ('for', p[2], p[4], p[6], p[5], p[8])

def p_direction(p):
    '''direction : TO
                 | DOWNTO'''
    p[0] = p[1]


def p_call_stmt(p):
    '''call_stmt : ID LPAREN expr_list RPAREN
                 | ID LPAREN expr_list RPAREN SEMI'''
    p[0] = ('call', p[1], p[3])


# -----------------------
# Expressões
# -----------------------
def p_expr_list(p):
    '''expr_list : expr
                 | expr COMMA expr_list'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_expr_binop(p):
    '''expr : expr PLUS expr
            | expr MINUS expr
            | expr MULT expr
            | expr DIVIDE expr
            | expr DIV expr
            | expr MOD expr
            | expr EQUAL expr
            | expr NEQ expr
            | expr LT expr
            | expr LE expr
            | expr GT expr
            | expr GE expr
            | expr AND expr
            | expr OR expr'''
    p[0] = (p[2].lower(), p[1], p[3])

def p_expr_parens(p):
    '''expr : LPAREN expr RPAREN'''
    p[0] = p[2]

def p_expr_not(p):
    '''expr : NOT expr'''
    p[0] = ('not', p[2])

def p_expr_number(p):
    '''expr : NUMBER'''
    p[0] = ('num', p[1])

def p_expr_string(p):
    '''expr : STRLIT'''
    p[0] = ('str', p[1])

def p_expr_id(p):
    '''expr : ID'''
    p[0] = ('id', p[1])

def p_expr_array_access(p):
    '''expr : ID LBRACK expr RBRACK'''
    p[0] = ('array', p[1], p[3])

def p_expr_call(p):
    '''expr : ID LPAREN expr_list RPAREN'''
    p[0] = ('call', p[1], p[3])

# -----------------------
# Erros
# -----------------------
def p_error(p):
    if p:
        print(f"Erro de sintaxe em '{p.value}' na linha {p.lineno}")
    else:
        print("Erro de sintaxe: fim inesperado")

# -----------------------
# Parser builder
# -----------------------
parser = yacc.yacc(debug=True, write_tables=False)

def parse(data):
    global ast
    ast = {}
    
    return parser.parse(data)
    