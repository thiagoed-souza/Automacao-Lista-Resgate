# 🚀 Automação de Relatórios - ERP Flystart

Aplicação desktop para **extração e tratamento automatizado de relatórios financeiros** do ERP Flystart. 

Substitui o processo manual de navegação, aplicação de filtros, exportação e formatação de planilhas de cobrança em **um único clique**.

---

## 🎯 O que a ferramenta faz?

* **Automação Web:** Acessa o ERP, realiza o login, seleciona a unidade (**JP** ou **NATAL**) e extrai as contas pendentes do período selecionado.
* **Limpeza de Dados:** Trata o nome dos clientes (remove IDs e prefixos) e padroniza dados de veículos e placas.
* **Cálculo de Juros e Atraso:** Aplica automaticamente a taxa de 13% sobre o saldo e calcula a quantidade exata de dias em atraso.
* **Relatório Pronto para Uso:** Gera uma planilha `.xlsx` limpa e formatada na pasta **Downloads**, abrindo o arquivo automaticamente ao finalizar.

---

## 💻 Como Usar

### 📦 Opção 1: Executável (`.exe`) — *Recomendado*

> Não requer Python instalado. Funciona em qualquer máquina com o Google Chrome.

1. Baixe o arquivo executável na pasta do projeto ou na seção de *Releases*.
2. Abra o arquivo **`Automação Flystart.exe`**.
3. Preencha as informações da tela:
   * **Usuário / CPF** e **Senha** do Flystart
   * **Unidade** (`ZEH MOTOCA JP` ou `ZEH MOTOCA NATAL`)
   * **Período** (Ex: `01/08/2026 - 09/08/2026`)
4. Clique em **🚀 Iniciar Processamento**.

---

### 🛠️ Opção 2: Código Fonte (Python)

Caso deseje executar ou modificar o código fonte:

1. **Instale as dependências:**
   ```bash
   pip install customtkinter selenium pandas openpyxl
