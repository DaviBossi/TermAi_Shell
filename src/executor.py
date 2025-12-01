import subprocess
import os
import sys
import requests
import datetime

class ClearScreenSignal(Exception):
    """Sinal para a GUI limpar a tela"""
    pass

class Executor:
    def __init__(self):
        """
        Construtor da classe Executor.
        Inicializa o objeto. Por enquanto está vazio (pass), mas futuramente 
        pode ser usado para carregar histórico de comandos, variáveis de 
        ambiente ou configurações iniciais da API de IA.
        """
        
        #Inicializa o historico
        self.history = []
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
        
        command_flag =" " if ast_node.get('flags') == None else ast_node.get('flags')
        
        command_path =" " if ast_node.get('path') == None else ast_node.get('path')
        
        full_command = f"{command_type} {command_flag} {command_path}"
        
        self.history.append(full_command)
        
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
        print("  rmdir <path> - Exclui uma pasta")
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
        """
        (Embutido) Lista arquivos com suporte a flags:
         -a : Mostra ocultos
         -r : Inverte a ordem
         -l : Mostra detalhes (tamanho e data)
        """
        target_dir = node.get('path') or '.'
        flags_list = node.get('flags') or [] # Ex: ['-l', '-a'] ou ['-la']
        
        # 1. Detectar quais opções estão ativas
        # Juntamos todas as flags em uma única string para facilitar a busca
        # Ex: ['-l', '-a'] vira "-l-a". Ex: ['-la'] vira "-la"
        flags_str = "".join(flags_list)
        
        show_all = 'a' in flags_str   # Flag -a
        reverse  = 'r' in flags_str   # Flag -r
        long_fmt = 'l' in flags_str   # Flag -l

        try:
            # Pega todos os arquivos
            files = os.listdir(target_dir)
            
            # LÓGICA DO -a (ALL)
            # Se NÃO tiver a flag -a, filtramos tirando os que começam com '.'
            if not show_all:
                files = [f for f in files if not f.startswith('.')]
            
            # Ordenação Padrão (Alfabética)
            files.sort()

            # LÓGICA DO -r (REVERSE)
            if reverse:
                files.reverse() # Inverte a lista
            
            # LÓGICA DO -l (LONG FORMAT)
            if long_fmt:
                for filename in files:
                    full_path = os.path.join(target_dir, filename)
                    
                    # Pega estatísticas do arquivo (tamanho, data, etc)
                    stats = os.stat(full_path)
                    
                    # Tamanho em Bytes
                    size = stats.st_size
                    
                    # Data de modificação (convertendo timestamp para texto legível)
                    mod_time = datetime.datetime.fromtimestamp(stats.st_mtime)
                    date_str = mod_time.strftime('%Y-%m-%d %H:%M')
                    
                    # Identifica se é pasta <DIR> ou arquivo
                    tipo = "<DIR>" if os.path.isdir(full_path) else "     "
                    
                    # Imprime formatado (alinhado em colunas)
                    # {:<10} significa "ocupe 10 espaços alinhado à esquerda"
                    print(f"{date_str}  {tipo}  {size:<10} {filename}")
            
            else:
                # Se não for modo longo, imprime simples
                for f in files:
                    print(f)
                
        except FileNotFoundError:
            print(f"TermIA: ls: diretório não encontrado: {target_dir}")
        except NotADirectoryError:
            print(f"TermIA: ls: '{target_dir}' não é um diretório.")
        except Exception as e:
            print(f"TermIA: erro no ls: {e}")
            
    def exec_clear(self, node):
        """(Embutido) Lança um sinal para a GUI limpar o texto."""
        # Não fazemos a limpeza aqui, apenas pedimos para a GUI fazer.
        raise ClearScreenSignal()
    
    def exec_history(self,node):
        
        if not self.history:
            print("Historico vazio")
            return

        print("=== Histórico de Comandos ===")
        
        for i,cmd in enumerate(self.history):
            print(cmd)
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
