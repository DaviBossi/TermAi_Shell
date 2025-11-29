import ply.yacc as yacc

reserved = {
    'help': 'HELP',
    'exit': 'EXIT',
    'echo': 'ECHO',
    'history': 'HISTORY',
    'pwd': 'PWD',
    'ls': 'LS',
    'show': 'SHOW',
    'cd': 'CD',
    'mkdir': 'MKDIR',
    'rmdir' : 'RMDIR',
    'rm' : 'RM',
    'touch': 'TOUCH',
    'ia_mode': 'IA',
    'cls': 'CLEAR',
    'history' : 'HISTORY'
}

tokens = [
    'STRING',   # "texto com espaços"
    'FLAG',     # -a, -la, --all, etc.
    'ID',       # palavras/paths
    'NEWLINE',
] + list(reserved.values())


def ast(node_type, **kwargs):
    data = {'type': node_type}
    data.update(kwargs)
    return data

precedence = ()

def p_input_cmd_nl(p):
    'input : command NEWLINE'
    p[0] = p[1]

def p_input_cmd(p):
    'input : command'
    p[0] = p[1]

def p_input_nl(p):
    'input : NEWLINE'
    p[0] = None

def p_command(p):
    '''command : builtin
               | ia_mode'''
    p[0] = p[1]
    
# --- (NOVO) Regra Genérica para Comandos Desconhecidos ou Externos ---
def p_command_generic(p):
    '''command : ID
               | ID argseq
               | ID flagseq
               | ID flagseq argseq'''
    
    # Vamos montar a AST capturando o que veio
    flags = []
    args = []
    
    # A estrutura de p muda dependendo de qual regra foi usada:
    
    # Caso 1: ID (len=2) -> ex: "git"
    if len(p) == 2:
        pass 

    # Caso 2: ID argseq (len=3) -> ex: "git pull"
    elif len(p) == 3:
        # Precisamos checar se p[2] é lista de flags ou args
        # (Sua gramática retorna listas para argseq e flagseq)
        first_element = p[2][0] 
        if first_element.startswith('-'): # É flag
             flags = p[2]
        else: # É argumento
             args = p[2]

    # Caso 3: ID flagseq argseq (len=4) -> ex: "gcc -c main.c"
    elif len(p) == 4:
        flags = p[2]
        args = p[3]

    # O "type" da AST será o próprio nome do comando (ex: 'git', 'python', 'batata')
    p[0] = ast(p[1], flags=flags, args=args)

# --------- Builtins ----------
def p_builtin_help(p):
    'builtin : HELP'
    p[0] = ast('help')

def p_builtin_exit(p):
    'builtin : EXIT'
    p[0] = ast('exit')

def p_builtin_echo(p):
    'builtin : ECHO argseq'
    p[0] = ast('echo', args=p[2])

def p_builtin_history(p):
    'builtin : HISTORY'
    p[0] = ast('history')

def p_builtin_pwd(p):
    'builtin : PWD'
    p[0] = ast('pwd')

def p_builtin_ls_variants(p):
    '''builtin : LS
               | LS flagseq
               | LS ID
               | LS flagseq ID'''
    flags, path = [], None
    if len(p) == 2:
        pass
    elif len(p) == 3:
        if isinstance(p[2], list):
            flags = p[2]
        else:
            path = p[2]
    elif len(p) == 4:
        flags = p[2]
        path = p[3]
    p[0] = ast('ls', flags=flags, path=path)

def p_builtin_show(p):
    '''builtin : SHOW
               | SHOW ID'''
    if len(p) == 3: 
        p[0] = ast('show', path=p[2])
    else: 
        p[0] = ast('show', path=None)

def p_builtin_cd(p):
    '''builtin : CD
               | CD ID'''
    if len(p) == 3: 
        p[0] = ast('cd', path=p[2])
    else: 
        p[0] = ast('cd', path=None)

def p_builtin_mkdir(p):
    '''builtin : MKDIR
               | MKDIR ID'''
    if len(p) == 3: 
        p[0] = ast('mkdir', path=p[2])
    else: 
        p[0] = ast('mkdir', path=None) 

def p_builtin_rmdir(p):
    '''builtin : RMDIR
               | RMDIR ID'''
    if len(p) == 3:
        p[0] = ast('rmdir', path=p[2])
    else:
        p[0] = ast('rmdir', path=None)

def p_bultin_rm(p):
    '''builtin : RM
               | RM ID
               | RM STRING'''
    if len(p) == 3:
        p[0] = ast('rm', path=p[2])
    else:
        p[0] = ast('rm', path=None)
def p_builtin_touch(p):
    '''builtin : TOUCH
               | TOUCH ID'''
    if len(p) == 3 : 
        p[0] = ast('touch', path=p[2])
    else: 
        p[0] = ast('touch', path=None)
        
def p_builtin_clear(p):
    '''builtin : CLEAR'''
    p[0] = ast('clear')
    
    
# --------- IA ----------
def p_ia_mode(p):
    'ia_mode : IA'
    # Cria uma AST simples avisando que queremos entrar no modo
    p[0] = ast('ia_mode')

# --------- Sequências ----------
def p_flagseq(p):
    '''flagseq : FLAG
               | flagseq FLAG'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_argseq(p):
    '''argseq : arg
              | argseq arg'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_arg(p):
    '''arg : STRING
           | ID'''
    p[0] = p[1]

def p_error(tok):
    if tok:
        print(f"[PARSER] Erro próximo ao token {tok.type} ({tok.value!r}) na linha {tok.lineno}")
    else:
        print("[PARSER] Erro de sintaxe no final da entrada.")

parser = yacc.yacc(start='input')