🚀 Flystart Financial Automation
Ferramenta desktop para automação de extração e tratamento de relatórios financeiros do ERP Flystart.

Substitui o processo manual de login, aplicação de filtros, download e formatação de planilhas de cobrança em um único clique.

🎯 O que o projeto resolve?
Elimina o trabalho manual: Realiza o login no ERP, seleciona a empresa (JP ou Natal), filtra contas em aberto por período e baixa o relatório.

Higieniza os dados: Limpa nomes de clientes (remove IDs e códigos soltos) e padroniza marcas de veículos e placas.

Calcula valores e juros: Aplica automaticamente a taxa de 13% sobre os saldos pendentes e calcula os dias exatos de atraso.

Gera relatório pronto pra cobrança: Exporta uma planilha .xlsx enxuta contendo apenas as colunas úteis e abre o arquivo ao finalizar.

💻 Como Usar
Opção 1: Usando o Executável (.exe) — Recomendado para usuários
Acesse a pasta dist (ou o local onde o .exe está salvo).

Dê um duplo clique no arquivo Automação Flystart.exe.

Preencha seus dados de acesso, selecione a unidade, insira o período e clique em 🚀 Iniciar Processamento.

Nota: Não é necessário ter o Python instalado para rodar o executável. Apenas certifique-se de ter o Google Chrome instalado na máquina.

Opção 2: Rodando via Código (Python) — Para desenvolvedores
Instale as dependências:

Bash
pip install customtkinter selenium pandas openpyxl
Execute o script:

Bash
python app.py
(Opcional) Como compilar um novo .exe:
Caso faça alterações no código e queira gerar um novo executável com PyInstaller:

Bash
pip install pyinstaller
pyinstaller --noconsole --onefile app.py
📌 Colunas do Relatório Gerado
O arquivo final é salvo na pasta Downloads e aberto automaticamente no Excel com as seguintes colunas:

ID | Tipo | Cliente/Fornecedor | Descrição | Placa | Saldo (+13%) | Data cadastro | Dias de Atraso | WhatsApp
