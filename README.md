# TermIA - Terminal Inteligente Integrado com IA 🤖💻

Projeto Final de Compiladores - Universidade Federal de Itajubá (UNIFEI)

**Autor:** Davi Pereira Bossi (2024014355)

O **TermIA** é um interpretador de comandos (Shell) desenvolvido em Python que combina conceitos fundamentais de Teoria dos Compiladores com a modernidade da **Inteligência Artificial Generativa**.

Diferente de um terminal comum, o TermIA possui um modo dedicado `(ia_mode)` onde o usuário pode conversar diretamente com o modelo **Google Gemini 2.5**, recebendo respostas e assistências de código em tempo real, tudo dentro de uma interface gráfica customizada que simula um console clássico.

# 📑 Índice

- Funcionalidades
- Arquitetura do Projeto (Como Funciona?)
- Comandos Suportados
- Pré-requisitos e Instalação
- Configuração da API
- Tecnologias Utilizadas

# 🚀 Funcionalidades

- **Interface Gráfica (GUI):** Uma janela estilo "Hacker/Console" feita com Tkinter, com redirecionamento de saída padrão (stdout) para exibição na interface.
- **Manipulação de Arquivos e Diretórios:** Comandos como `ls`, `cd`, `mkdir`, `touch`, `rm`, `rmdir`.
- **Análise Léxica e Sintática:** Uso da biblioteca `PLY` para processar comandos baseados em uma gramática formal.
- **Modo IA Integrado:** Um sub-shell interativo conectado à API do Google Gemini para perguntas e respostas.
- **Portabilidade:** Comandos internos implementados em Python puro, garantindo funcionamento em Windows e Linux.

# 🧠 Arquitetura do Projeto (Como Funciona?)

Este projeto aplica o pipeline clássico de um compilador/interpretador. Abaixo está a explicação didática de cada etapa:

1. Lexer (Analisador Léxico)
É a primeira etapa. O código recebe a string digitada pelo usuário e a quebra em "tokens" (palavras com significado).

Entrada: `ls -la home`

Saída: `[TOKEN_LS, TOKEN_FLAG('-la'), TOKEN_ID('home')]`

2. Parser (Analisador Sintático)
Recebe os tokens e verifica se eles obedecem às regras gramaticais definidas (Gramática Livre de Contexto). Se a frase fizer sentido, ele constrói uma **Árvore Sintática Abstrata (AST).**

Regra: `COMANDO -> LS FLAG ID`

AST Gerada: `{'type': 'ls', 'flags': ['-la'], 'path': 'home'}`

3. Executor (Dispatcher)
Atua como o "cérebro" operacional. Ele recebe a AST e decide quem deve executar a ação.

**Comandos Built-in:** Se for `cd`, `exit` ou `ia_mode`, o próprio Python executa a ação internamente (para alterar o estado do shell).

4. Interface Gráfica (O Truque do `sys.stdout`)
Para criar a experiência de terminal, o projeto intercepta tudo o que seria impresso no console (print) redirecionando o `sys.stdout` para um buffer de memória, que é então lido e inserido na janela do Tkinter.

# 💻 Comandos Suportados

**Comandos de Sistema (Built-in)**

| Comando | Descrição | Exemplo |
| :--- | :--- | :--- |
| `ls` | Lista arquivos e pastas (suporta flags). | `ls` ou `ls -a` |
| `cd` | Muda o diretório atual. | `cd Documents` |
| `pwd` | Mostra o caminho atual. | `pwd` |
| `mkdir` | Cria uma nova pasta. | `mkdir projeto` |
| `rmdir` | Remove uma pasta vazia. | `rmdir lixo` |
| `touch` | Cria um arquivo vazio ou atualiza data. | `touch main.py` |
| `rm` | Remove um arquivo. | `rm arquivo.txt` |
| `show` | Exibe o conteúdo de um arquivo (igual cat). | `show notas.txt` |
| `echo` | Imprime texto na tela. | `echo Olá Mundo` |
| `help` | Mostra a lista de ajuda. | `help` |
| `exit` | Fecha o terminal. | `exit` |

**Inteligência Artificial**

| Comando | Descrição | 
| :--- | :--- |
| ia_mode | Entra no Modo Interativo. O prompt muda e tudo que for digitado é enviado para o Google Gemini. Digite `sair` para voltar.

# 🛠 Pré-requisitos e Instalação

Você precisará do **Python 3.8+** instalado.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/SEU_USUARIO/TermIA.git
   cd TermIA
2. **Crie um ambiente virtual (Opcional, mas recomendado):**
   ```bash
   python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
3. **Instale as dependências:**
   ```bash
   pip install ply requests python-dotenv

**Nota:** O `tkinter` geralmente já vem instalado com o Python. Caso dê erro, instale-o via gerenciador de pacotes do seu SO.

# 🔑 Configuração da API

Para usar o `ia_mode`, você precisa de uma chave gratuita do Google Gemini.

1. Acesse o [Google Ai Studio](https://aistudio.google.com/app/api-keys).
2. Crie uma nova API Key.
3. Na raiz do projeto, crie um arquivo chamado .env.
4. Cole sua chave no arquivo `.env` seguindo este formato (sem aspas):
    ```bash
    GEMINI_API_KEY=AIzaSySuaChaveGiganteAqui12345

# 🧪 Como Rodar

Após configurar o ambiente e a chave:
  ```bash
python termai.py
```
*(Substitua termia.py pelo nome do seu arquivo principal, caso seja diferente)*

Uma janela preta se abrirá. Digite `help` para começar!

# 🛠 Tecnologias Utilizadas

- [Python](https://www.python.org/): Linguagem Base.
- [PLY(Python Lex-Yacc](https://github.com/dabeaz/ply): Implementação de Lexer e Parser.
- [Tkinter](https://docs.python.org/3/library/tkinter.html): Biblioteca padrão de GUI do Python.
- [Requests](https://pypi.org/project/requests/): Para comunicação HTTP com a API.
- [Google Gemini API](https://ai.google.dev/): Modelo de linguagem para o assistente inteligente.

# 👨‍💻 Autor

Desenvolvido com ☕ e código por **Davi Pereira Bossi**. Projeto acadêmico para a disciplina de Compiladores.
