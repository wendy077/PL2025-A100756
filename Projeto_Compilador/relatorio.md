# Relatório   
## Compilador para Pascal Standard

### Projeto de Processamento de Linguagens — 2025

---

## Introdução

O objetivo deste projeto foi o desenvolvimento de um *compilador para a linguagem Pascal Standard*, capaz de analisar, interpretar e traduzir código fonte Pascal para um formato intermediário e, por fim, gerar código executável para uma máquina virtual (VM) disponibilizada no contexto da UC.

O trabalho envolveu várias etapas essenciais de construção de compiladores:
- *Análise Léxica* (tokenização do código),
- *Análise Sintática* (validação da estrutura gramatical),
- *Análise Semântica* (verificação de tipos, declarações e coerência),
- *Geração de Código* (tradução dirigida pela sintaxe para a VM).

Além disso, o projeto incluiu a criação de uma *bateria de testes*, assegurando que todos os exemplos fornecidos no enunciado são processados corretamente pelo compilador. Foi ainda desenvolvido um “extra”, demonstrando extensibilidade da arquitetura.

---

## Arquitetura do Compilador

O projeto está dividido em quatro componentes principais:

- *Analisador Léxico* (pascal_lexer.py)
- *Analisador Sintático* (pascal_parser.py)
- *Analisador Semântico* (verificador.py)
- *Gerador de Código para VM* (gerador_vm.py)

Abaixo é detalhado o papel de cada componente e como estes interagem entre si.

---

## 1. Analisador Léxico (pascal_lexer.py)

O *analisador léxico* (lexer) é responsável por converter o texto fonte Pascal numa sequência de tokens, abstraindo comentários, espaços e outros elementos irrelevantes para a gramática.

- *Implementação*: Utiliza a biblioteca ply.lex, que facilita a especificação dos tokens através de expressões regulares e funções de ação.
- *Tokens Reconhecidos*:  
  - Palavras-chave (e.g., program, var, begin, end, if, then, else, while, for, procedure, function, etc.)
  - Identificadores, literais inteiros e string, operadores aritméticos e lógicos, delimitadores e símbolos especiais.
- *Funções Especiais*:  
  - Ignora espaços, tabulações e comentários.
  - Gera mensagens de erro para símbolos não reconhecidos, aumentando a robustez do compilador.
- *Exemplo de Fluxo*:  
  Ao receber o código:

  pascal
  var x: integer;
  

  o lexer gera a sequência:  

    pascal
    [VAR, ID('x'), ':', INTEGER, ';']
    

## 2. Analisador Sintático (pascal_parser.py)

O *analisador sintático* (parser) interpreta a sequência de tokens gerada pelo lexer, validando se está em conformidade com a gramática do Pascal Standard.

- *Implementação*:  
    - Utiliza a biblioteca ply.yacc, permitindo a definição das regras de produção da gramática de Pascal de forma clara e próxima do formalismo BNF.
- *Construção da Árvore Sintática*:  
  - As regras do parser constroem uma *Árvore Sintática Abstrata* (AST - Abstract Syntax Tree), que representa a estrutura lógica do programa.
- *Tratamento de Erros Sintáticos*:  
  - O parser é capaz de detetar e reportar erros sintáticos de forma informativa, indicando a linha e o tipo de erro detetado.
- *Exemplo*:  
  - Ao receber tokens de um comando if, valida a estrutura if <condição> then <bloco> [else <bloco>] e constrói o nó correspondente na AST.
- *Suporte à Recursividade e Aninhamento*:  
  - A implementação lida com comandos aninhados e recursivos (e.g., ciclos dentro de ciclos, funções dentro de procedimentos, etc.).
- *Saída*:  
  - A AST produzida é usada nas fases seguintes (análise semântica e geração de código).

---

## 3. Analisador Semântico (verificador.py)

Este módulo efetua a *análise semântica* do programa.

- *Verificação de Declarações*:  
  - Garante que todas as variáveis são declaradas antes de serem usadas.
  - Confirma que tipos estão corretamente atribuídos e utilizados.
- *Verificação de Tipos*:  
  - Operações aritméticas e lógicas são verificadas quanto à coerência dos operandos.
- *Contextos de Variáveis e Funções*:  
  - Mantém tabelas de símbolos para controlar escopos de variáveis, procedimentos e funções.
- *Gestão de Erros Semânticos*:  
  - Erros como uso de variáveis não declaradas, atribuição de tipos incompatíveis, ou chamadas de funções incorretas são reportados de forma clara.
- *Suporte a Escopos*:  
  - Implementa uma pilha de contextos para tratar variáveis locais, globais, parâmetros de funções e procedimentos.

---

## 4. Gerador de Código para VM (gerador_vm.py)

O *gerador de código* converte a árvore sintática e as informações semânticas validadas para instruções da máquina virtual (VM).

- *Geração Direta de Código*:  
  - Tradução das estruturas de controlo (if, while, for), atribuições, chamadas de função, etc., para o conjunto de instruções suportado pela VM.
- *Gestão de Registos e Stack*:  
  - Manipulação eficiente da stack para chamadas e retornos de funções/procedures, passagem de parâmetros e avaliação de expressões.
- *Output*:  
  - Gera ficheiros de texto com o código da VM, pronto para ser executado na plataforma online indicada no enunciado.
- *Integração com a Análise Semântica*:  
  - O código gerado reflete as garantias semânticas verificadas previamente (tipos corretos, variáveis declaradas, etc).

---

## Decisões de Implementação

Durante o desenvolvimento, foram tomadas várias decisões importantes:


- *Árvore Sintática Intermédia*:  
  - A escolha de usar uma AST intermedia permite mais flexibilidade, tornando possível implementar futuras otimizações e extensões sem alterar a análise sintática.
- *Separação de Módulos*:  
  - Cada componente (lexer, parser, verificador, gerador) está num ficheiro próprio, promovendo modularidade, facilidade de manutenção e expansão.
- *Erros Detalhados*:  
  - Mensagens de erro léxicas, sintáticas e semânticas são detalhadas, facilitando o debugging e o uso pedagógico do compilador.
- *Cobertura Total de Exemplos*:  
  - Todos os exemplos do enunciado foram usados como testes de aceitação e estão garantidos a funcionar 100%, garantindo conformidade com os requisitos.

---

## Testes

O projeto inclui uma *pasta de exemplos* com duas categorias:

- *exemplos/enunciado/*:  
  - Todos os exemplos fornecidos no enunciado (Olá Mundo, Maior de 3, Fatorial, Números Primos, Soma de Array, Conversão Binária-Decimal, Função BinToInt) foram compilados com sucesso, tanto na análise sintática como na execução na VM.
- *exemplos/outros/** 
  - Inclui ficheiros  desenvolvidos para testar funcionalidades adicionais, explorando construções do Pascal que não estavam presentes nos exemplos do enunciado:
  
  **analise_numero.pas**  
    - Exemplo que inclui a definição e chamada de um `procedure` próprio, obrigando o compilador a suportar a análise e geração de código para procedimentos (incluindo declaração, chamada, escopo de variáveis e parâmetros).
  
  **const.pas**  
    - Exemplo que utiliza a declaração da palavra-chave `const`, obrigando o analisador léxico, sintático e semântico a reconhecer e tratar constantes, garantindo a correta associação de valores constantes e o seu uso em expressões e atribuições.

  Desta forma, os testes extra mostram a extensibilidade da arquitetura do compilador, indo além dos requisitos mínimos do enunciado.

- *Automação*:
  - O projeto inclui o script `run.sh`, que automatiza a execução de todos os exemplos das duas pastas. Assim, a validação dos exemplos é feita de forma prática e reprodutível, permitindo testar rapidamente o funcionamento do compilador após qualquer alteração ao código.  

- *Cobertura*:  
  Os testes cobrem:
  - Declarações e inicializações de variáveis,
  - Estruturas de controlo (if, while, for),
  - Procedimentos e funções,
  - Entrada/saída,
  - Operações sobre arrays e strings.

---

## Conclusão

O compilador desenvolvido cumpre todos os requisitos definidos no enunciado, nomeadamente:

- *Corretude*: Todos os programas Pascal do enunciado são processados e executados corretamente na VM.
- *Estrutura e Modularidade*: O código encontra-se bem organizado, com separação clara entre as fases do compilador.
- *Funcionalidade e Eficiência*: Suporta todas as construções essenciais da linguagem Pascal Standard, sendo facilmente extensível.
- *Testabilidade*: Todos os exemplos fornecidos e testes extra passam sem erros, demonstrando robustez e cobertura do compilador.

O projeto demonstra ainda potencial para futuras extensões e otimizações. O(s) ficheiro(s) extra em exemplos/outros/ exemplificam como novas funcionalidades podem ser facilmente integradas refletindo boas práticas de processamento de linguagens e demonstrando a extensibilidade da arquitetura.

Em suma, o grupo consolidou os conceitos teóricos e práticos desenvolvidos ao longo do tempo nesta unidade curricular e considera que desenvolveu um trabalho competente e de acordo com os objetivos propostos.