#Davi Pereira Bossi - 2024014355
import tkinter as tk
from tkinter import font
import sys
import io
import sys
import os
import subprocess
import requests
from dotenv import load_dotenv
import ply.lex as lex
import ply.yacc as yacc

# ----------------------------------
# LEXER
# ----------------------------------

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
}

tokens = [
    'STRING',   # "texto com espaços"
    'FLAG',     # -a, -la, --all, etc.
    'ID',       # palavras/paths
    'NEWLINE',
] + list(reserved.values())

t_ignore = ' \t'

def t_STRING(t):
    r'"[^"\n\r]*"'
    t.value = t.value[1:-1]  # remove aspas
    return t

def t_FLAG(t):
    r'--[a-zA-Z0-9_-]+|-{1}[a-zA-Z]+'
    return t

def t_ID(t):
    r'[A-Za-z0-9._/\-]+'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

def t_error(t):
    print(f"[LEXER] Caractere inválido: {t.value[0]!r}")
    t.lexer.skip(1)

lexer = lex.lex()

# ----------------------------------
# PARSER
# ----------------------------------

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

class Executor:
    def __init__(self):
        """
        Construtor da classe Executor.
        Inicializa o objeto. Por enquanto está vazio (pass), mas futuramente 
        pode ser usado para carregar histórico de comandos, variáveis de 
        ambiente ou configurações iniciais da API de IA.
        """
        pass
    
    def execute(self, ast_node):
        """
        O 'Despachante' (Dispatcher) Central.
        Recebe a Árvore Sintática Abstrata (AST) gerada pelo Parser e decide
        dinamicamente qual método deve ser chamado para executar a ação.
        """
        # 1. Verificação de segurança: Se o usuário apertou apenas ENTER,
        # o parser retorna None. Aqui evitamos que o programa quebre.
        if ast_node is None:
            return
        
        # 2. Extrai o tipo do comando da AST (ex: 'cd', 'ls', 'mkdir')
        command_type = ast_node.get('type')
        
        # 3. Metaprogramação: Cria o nome da função que deveria existir.
        # Ex: Se command_type é 'cd', procura por 'exec_cd'.
        method_name = f'exec_{command_type}'
        
        # 4. A Mágica do 'getattr':
        # Procura dentro de 'self' (esta classe) se existe um método com o nome 'method_name'.
        # - Se achar (ex: exec_cd), coloca ele na variável 'handler'.
        # - Se NÃO achar, coloca 'self.exec_generic' na variável 'handler'.
        handler = getattr(self, method_name, self.exec_generic)
        
        try:
            # 5. Executa a função escolhida passando os dados da AST
            handler(ast_node)
        except Exception as e:
            # 6. Proteção Global: Se qualquer erro ocorrer na execução,
            # capturamos aqui para impedir que o Shell feche sozinho (crash).
            print(f"[EXEC] Erro ao executar '{command_type}': {e}")
    
    def exec_exit(self, node):
        """
        Comando Built-in: EXIT
        Encerra a execução do interpretador Python.
        """
        print("Encerrando o Shell ...............")
        sys.exit(0) # '0' informa ao sistema operacional que saiu com sucesso/sem erros.
        
    def exec_cd(self, node):
        """
        Comando Built-in: CD (Change Directory)
        Altera o diretório de trabalho do processo atual.
        É OBRIGATÓRIO ser built-in, pois se fosse rodado via subprocesso,
        ele mudaria a pasta do filho e não do pai (o TermIA).
        """
        # Pega o caminho da AST. Se não tiver argumento, assume '.' (diretório atual)
        path = node.get('path', '.')
        
        try:
            # Chama o Sistema Operacional para mudar o contexto da pasta
            os.chdir(path)
        except FileNotFoundError:
            # Trata o erro semântico: a pasta não existe
            print(f"TermIA> cd: diretório não encontrado: {path}")
        except NotADirectoryError:
            # Trata o erro semântico: o caminho existe, mas é um arquivo, não pasta
            print(f"TermIA> cd: não é um diretório: {path}")
    
    def exec_pwd(self, node):
        """
        Comando Built-in: PWD (Print Working Directory)
        Imprime o caminho absoluto de onde o shell está localizado agora.
        """
        print(os.getcwd())
        
    def exec_help(self, node):
        """(Embutido) Mostra ajuda."""
        print("--- Ajuda do TermIA ---")
        print("  help          - Mostra esta ajuda")
        print("  exit          - Sai do terminal")
        print("  cd <path>     - Muda de diretório")
        print("  pwd           - Mostra o diretório atual")
        print("  ls [-flags] [path] - Mostra todos os arquivos no diretorio atual")
        print("  mkdir <path> - Cria uma pasta com o nome desejado")
        print("  touch <path> - Cria um arquivo com o nome desejado")
        print("  echo <args...> - Printa no terminal a mensagem escrita")
        print("  show <file> - Mostra todo o conteudo de um arquivo")
        print("--- AI MODE ---")
        print(" ai_mode - Entra no modo IA, onde voce pode fazer perguntas diretamente para o gemini e receber respostas em tempo real")
    
    def exec_echo(self, node):
        """
        Comando Built-in: ECHO
        Função: Repete na saída padrão (stdout) os argumentos recebidos.
        Semelhante ao 'print' do Python, mas dentro do shell.
        """
        # node['args'] é uma lista de strings vinda da AST (ex: ['Ola', 'Mundo'])
        # O método .join junta esses itens colocando um espaço " " entre cada um.
        mensagem = " ".join(node['args'])
        
        # Envia o texto final para o stdout (que sua GUI vai capturar)
        print(mensagem)
    
    def exec_touch(self, node):
        """
        Comando Built-in: TOUCH
        Função: Cria um arquivo vazio se ele não existir, OU atualiza 
        o horário de modificação (timestamp) se ele já existir.
        Implementado em Python puro para garantir compatibilidade com Windows.
        """
        filename = node.get('path')
        
        # 1. Validação de Argumento
        if not filename:
            print("TermIA: touch: falta o nome do arquivo.")
            return

        try:
            # 2. Verifica se o arquivo já existe no disco
            if os.path.exists(filename):
                # Se existe, não altera o conteúdo. Apenas atualiza o carimbo de tempo.
                # None = usa a hora atual do sistema.
                os.utime(filename, None)
            else:
                # 3. Se não existe, cria um novo arquivo.
                # O modo 'a' (append) é usado por segurança: ele abre para escrita,
                # mas se por acaso o arquivo existir (race condition), ele não apaga nada.
                # O bloco 'with' garante que o arquivo seja fechado imediatamente após abrir.
                with open(filename, 'a'):
                    os.utime(filename, None) # Garante que o timestamp de criação seja agora.
                    
        except PermissionError:
            # Captura erro de permissão (ex: tentar criar arquivo em pasta de sistema)
            print(f"TermIA: touch: permissão negada: {filename}")
        except Exception as e:
            # Captura erros genéricos (ex: nome de arquivo inválido com caracteres proibidos)
            print(f"TermIA: erro ao executar touch: {e}")
    
    def exec_show(self, node):
        """
        Comando Built-in: SHOW (Personalizado)
        Função: Lê um arquivo de texto e exibe seu conteúdo na tela.
        Equivalente ao comando 'cat' do Linux ou 'type' do Windows.
        """
        filename = node.get('path')
        
        # 1. Validação de Argumento
        if not filename:
            print("TermIA: show: falta o nome do arquivo.")
            return

        try:
            # 2. Abertura de Arquivo
            # 'r': Read mode (apenas leitura).
            # encoding='utf-8': Essencial para ler arquivos com acentos (ç, ã, é) corretamente.
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read() # Lê o arquivo inteiro para a memória RAM
                print(content)     # Joga o conteúdo na tela
                
        except FileNotFoundError:
            # Erro semântico clássico: o usuário pediu para ler algo que não existe.
            print(f"TermIA: show: arquivo não encontrado: {filename}")
        except PermissionError:
            # O arquivo existe, mas o usuário não tem permissão de leitura.
            print(f"TermIA: show: permissão negada para ler: {filename}")
        except Exception as e:
            # Outros erros (ex: tentar ler um arquivo binário/imagem como se fosse texto)
            print(f"TermIA: erro ao ler arquivo: {e}")
    
    def exec_mkdir(self, node):
        """
        (Embutido) Cria um diretório.
        Feito em Python para garantir que funcione no Windows e Linux.
        """
        path = node.get('path')
        
        if not path:
            print("TermIA: mkdir: falta o nome do diretório.")
            return

        try:
            # os.makedirs cria a pasta (e as subpastas se necessário)
            # exist_ok=False faz dar erro se a pasta já existir (comportamento padrão do mkdir)
            os.makedirs(path, exist_ok=False)
            print(f"Diretório '{path}' criado com sucesso.") # Opcional: feedback visual
            
        except FileExistsError:
            print(f"TermIA: mkdir: não foi possível criar o diretório '{path}': O arquivo já existe.")
        except PermissionError:
            print(f"TermIA: mkdir: permissão negada para criar '{path}'.")
        except Exception as e:
            print(f"TermIA: erro desconhecido ao criar diretório: {e}")
    
    def exec_rmdir(self, node):
        """(Embutido) Remove um diretório vazio."""
        path = node.get('path')
        
        # 1. Validação básica
        if not path:
            print("TermIA: rmdir: falta o nome do diretório.")
            return

        # 2. Execução Segura
        try:
            os.rmdir(path)
            print(f"Diretório '{path}' removido.")
            
        except FileNotFoundError:
            print(f"TermIA: rmdir: falha ao remover '{path}': Diretório não encontrado.")
            
        except OSError as e:
            # Esse erro (WinError 145 ou OSError 39) acontece se a pasta NÃO estiver vazia
            print(f"TermIA: rmdir: falha ao remover '{path}': A pasta não está vazia.")
            print("Dica: O comando rmdir só remove pastas vazias por segurança.")
            
        except PermissionError:
            print(f"TermIA: rmdir: permissão negada para remover '{path}'.")
    
    def exec_rm(self, node):
        """(Embutido) Remove um arquivo (não remove pastas)."""
        filename = node.get('path')
        
        # 1. Validação básica
        if not filename:
            print("TermIA: rm: falta o nome do arquivo.")
            return

        # 2. Execução
        try:
            os.remove(filename)
            print(f"Arquivo '{filename}' removido.")
            
        except FileNotFoundError:
            print(f"TermIA: rm: não foi possível remover '{filename}': Arquivo não encontrado.")
            
        except IsADirectoryError:
            # Esse erro acontece se você tentar usar 'rm' em uma pasta
            print(f"TermIA: rm: não foi possível remover '{filename}': É um diretório.")
            print("Dica: Para remover diretórios, use o comando 'rmdir'.")
            
        except PermissionError:
            # Acontece se o arquivo estiver aberto em outro programa ou for protegido
            print(f"TermIA: rm: permissão negada para remover '{filename}'.")
            
        except Exception as e:
            print(f"TermIA: erro desconhecido no rm: {e}")
      
    def exec_ls(self, node):
        """(Embutido) Lista arquivos do diretório (Cross-platform)."""
        target_dir = node.get('path') or '.' # Se não tiver path, usa o atual '.'
        
        try:
            # Pega a lista de arquivos
            files = os.listdir(target_dir)
            
            # (Opcional) Se tiver flag '-a' ou similar, lógica de filtro aqui
            # No Linux, arquivos ocultos começam com '.'
            if not node.get('flags'): 
                 # Filtra ocultos se não tiver flags (exemplo simples)
                 files = [f for f in files if not f.startswith('.')]
            
            # Imprime os arquivos
            for f in files:
                print(f)
                
        except FileNotFoundError:
            print(f"TermIA: ls: diretório não encontrado: {target_dir}")
        except NotADirectoryError:
            print(f"TermIA: ls: '{target_dir}' não é um diretório.")
        except Exception as e:
            print(f"TermIA: erro no ls: {e}")
    
    # ----------------------------------------------
    # MODO INTERATIVO DE IA (SUB-SHELL)
    # ----------------------------------------------
    def chamar_api_ia(self, prompt):
        """
        Integração com IA via API REST (Google Gemini).
        Envia o texto do usuário para a nuvem e recebe a resposta gerada.
        """
        
        # Recupera a chave de API das variáveis de ambiente (.env).
        # Isso é crucial para segurança, evitando deixar senhas no código (Hardcoding).
        api_key = os.getenv("GEMINI_API_KEY")

        # ⚠️ ALERTA: A versão '2.5' ainda não existe publicamente.
        # Isso vai gerar um Erro 404. O correto atualmente é "gemini-1.5-flash".
        modelo = "gemini-2.5-flash" 

        # Monta a URL do endpoint da API do Google.
        # Usa f-string para inserir o modelo e a chave na URL.
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"

        # Cabeçalho padrão para informar que estamos enviando dados em JSON.
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Estrutura do corpo da requisição (Payload) exigida pela documentação do Google.
        # A estrutura é aninhada: contents -> lista -> parts -> lista -> text
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        try:
            print(f"☁️  Conectando ao Gemini ({modelo})...")
            
            # Realiza a chamada HTTP POST real.
            # O Python "congela" aqui esperando a resposta da internet.
            response = requests.post(url, headers=headers, json=payload)

            # Código 200 significa "OK" / Sucesso.
            if response.status_code == 200:
                
                # Converte a resposta bruta (bytes) para um dicionário Python.
                data = response.json()
                
                try:
                    # Navega pelo JSON de resposta para extrair apenas o texto da IA.
                    # Exemplo: {'candidates': [{'content': {'parts': [{'text': 'Olá!'}]}}]}
                    texto_resposta = data['candidates'][0]['content']['parts'][0]['text']
                    
                    return texto_resposta
                
                except (KeyError, IndexError):
                    # Proteção caso o Google mude o formato da resposta ou retorne vazio.
                    return "Erro: A API retornou uma resposta vazia."

            else:
                # Tratamento de erros HTTP (400, 401, 403, 404, 500).
                
                # Tratamento específico para Erro 404 (Not Found), comum se o nome do modelo estiver errado.
                if response.status_code == 404:
                    return "Erro 404: Modelo não encontrado."
                
                return f"Erro na API ({response.status_code}): {response.text}"

        except requests.exceptions.ConnectionError:
            # Captura falhas de rede (sem internet, DNS falhou, etc).
            return "Erro: Falha na conexão. Verifique sua internet."

        except Exception as e:
            # Captura qualquer outro erro não previsto.
            return f"Erro inesperado: {e}"
    
    def exec_generic(self, node):
        """
        O 'Goleiro' (Fallback) do Executor.
        Tenta executar qualquer comando que NÃO seja built-in (não tem um método exec_ próprio).
        Ex: git, python, gcc, node, etc.
        """

        command_name = node['type'] # O nome do comando (ex: 'git')
        
        # 1. Montagem da lista de argumentos para o subprocess.
        # O subprocess exige o formato lista: ['comando', '-flag', 'argumento']
        cmd_list = [command_name] 
        
        # Adiciona flags se existirem na AST (ex: -v, --version)
        if node.get('flags'):
            cmd_list.extend(node.get('flags'))
            
        # Adiciona argumentos se existirem (ex: commit, push)
        if node.get('args'):
            cmd_list.extend(node.get('args'))
            
        # Adiciona caminho se existir (legado de algumas regras do parser)
        if node.get('path'):
            cmd_list.append(node.get('path'))

        try:
            # 2. Execução no Sistema Operacional.
            # shell=False (padrão implícito) é usado por segurança contra Shell Injection.
            # check=True faz o Python lançar um erro se o programa retornar falha (código != 0).
            subprocess.run(cmd_list, check=True)
            
        except FileNotFoundError:
            # ERRO SEMÂNTICO CRÍTICO: O usuário digitou um comando que não existe no PC.
            # Ex: 'batata', 'lss'.
            print(f"TermIA: comando não encontrado: {command_name}")
            
        except subprocess.CalledProcessError as e:
            # O comando existe, rodou, mas falhou (ex: 'git status' fora de um repo).
            # O 'pass' significa que não imprimimos nada extra, pois o próprio comando
            # já deve ter impresso o erro no stderr.
            pass
            
        except PermissionError:
            # O arquivo existe, mas não é executável ou o usuário não tem permissão.
            print(f"TermIA: permissão negada para executar: {command_name}")

# ----------------------------------
# REPL simples (parsing -> AST)
# ----------------------------------

class TermIAGUI:
    def __init__(self, parser, lexer, executor):
        self.parser = parser
        self.lexer = lexer
        self.executor = executor
        self.is_ia_mode = False # Para controlar se estamos no "sub-shell" da IA

        # --- Configuração da Janela ---
        self.root = tk.Tk()
        self.root.title("TermIA - Terminal Inteligente")
        self.root.geometry("800x600")
        self.root.configure(bg="black")

        # Configuração de Fonte (Estilo Console)
        self.console_font = font.Font(family="Consolas", size=10) # Consolas, Courier ou Lucida Console

        # --- Área de Saída (Onde aparece o texto) ---
        self.output_area = tk.Text(
            self.root, 
            bg="black", 
            fg="white", 
            insertbackground="white",
            font=self.console_font,
            state="disabled", # Começa bloqueado para edição
            wrap="word"
        )
        self.output_area.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Tag para colorir coisas diferentes (opcional)
        self.output_area.tag_config("prompt", foreground="#00ff00") # Verde hacker
        self.output_area.tag_config("error", foreground="red")
        self.output_area.tag_config("ia", foreground="cyan")

        # --- Área de Entrada (Onde você digita) ---
        self.input_entry = tk.Entry(
            self.root, 
            bg="#1e1e1e", # Um cinza bem escuro para diferenciar levemente
            fg="white", 
            insertbackground="white",
            font=self.console_font,
            bd=0 # Sem borda
        )
        self.input_entry.pack(fill="x", padx=5, pady=5)
        self.input_entry.bind("<Return>", self.process_input) # Liga o ENTER à função
        self.input_entry.focus_set() # Já começa focado para digitar

        # --- Mensagem Inicial ---
        self.write_to_console("Bem-vindo ao TermIA [Versão 1.0]\n", "prompt")
        self.write_to_console("Copyright (c) 2025 Universidade Federal de Itajubá.\n\n")
        self.update_prompt()

    def start(self):
        """Inicia o loop da interface gráfica"""
        self.root.mainloop()

    def write_to_console(self, text, tag=None):
        """Escreve texto na área de saída e rola para baixo"""
        self.output_area.configure(state="normal") # Destrava
        self.output_area.insert("end", text, tag)
        self.output_area.see("end") # Rola para o final
        self.output_area.configure(state="disabled") # Trava de novo

    def update_prompt(self):
        """Mostra o prompt atual"""
        if self.is_ia_mode:
            self.write_to_console("TermIA-GPT> ", "ia")
        else:
            path = os.getcwd()
            self.write_to_console(f"TermIA {path}> ", "prompt")

    def process_input(self, event):
        """Ocorre quando aperta ENTER"""
        command_text = self.input_entry.get() # Pega o texto
        self.input_entry.delete(0, "end")     # Limpa o input

        # Escreve o comando que o usuário digitou na tela (para ficar no histórico)
        self.write_to_console(command_text + "\n")

        # Se estiver vazio, só mostra o prompt de novo
        if not command_text.strip():
            self.update_prompt()
            return

        # --- Lógica de Captura do Print ---
        # Aqui fazemos a mágica: Desviamos o sys.stdout para uma variável
        # Assim, tudo que seu Executor der 'print', nós pegamos.
        
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        try:
            # 1. TRATAMENTO DO MODO IA (Estado)
            if self.is_ia_mode:
                if command_text.strip().lower() in ['sair', 'exit', 'voltar']:
                    self.is_ia_mode = False
                    print("Saindo do modo IA...")
                else:
                    # Chama direto a API
                    resp = self.executor.chamar_api_ia(command_text)
                    print(f"🤖 IA: {resp}")
            
            # 2. TRATAMENTO NORMAL (Parser -> Executor)
            else:
                # Pequeno ajuste manual para detectar entrada no modo IA
                # (já que o parser funciona melhor com comandos completos)
                if command_text.strip().lower() == 'ia_mode':
                    self.is_ia_mode = True
                    print("="*40)
                    print("🤖 MODO IA ATIVADO (GUI)")
                    print("Digite 'sair' para voltar.")
                    print("="*40)
                    print("Faça perguntas livremente e receba respostas em tempo real.")
                    print("="*40)
                else:
                    # Adiciona \n para o lexer funcionar (fix do newline)
                    line_to_parse = command_text
                    if not line_to_parse.endswith("\n"):
                        line_to_parse += "\n"
                    
                    ast_node = self.parser.parse(line_to_parse, lexer=self.lexer)
                    self.executor.execute(ast_node)

        except Exception as e:
            print(f"Erro Crítico: {e}")
        
        finally:
            # Recupera o que foi impresso
            sys.stdout = old_stdout # Devolve o controle para o terminal real
            output_content = buffer.getvalue()
            
            # Escreve na tela preta
            self.write_to_console(output_content)
            
            # Prepara para o próximo comando
            self.update_prompt()

if __name__ == "__main__":
    # Carrega variáveis de ambiente (segurança)
    load_dotenv() 

    # Instancia o Executor
    executor_instance = Executor()
    
    # Inicia a Interface Gráfica em vez do repl()
    app = TermIAGUI(parser, lexer, executor_instance)
    app.start()
