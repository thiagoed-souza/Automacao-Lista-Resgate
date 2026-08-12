import os
import time
import glob
import datetime
import re
import getpass
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PASTA_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

def solicitar_dados_usuario():
    print("=== AUTENTICAÇÃO E CONFIGURAÇÃO DA CONSULTA ===")
    usuario = input("Digite seu usuário/CPF no Flystart: ").strip()
    senha = getpass.getpass("Digite sua senha do Flystart (não aparecerá na tela): ").strip()
    
    print("\n--- SELEÇÃO DE EMPRESA ---")
    print("1 - ZEH MOTOCA JP")
    print("2 - ZEH MOTOCA NATAL")
    opcao_empresa = input("Escolha a empresa (1 ou 2): ").strip()
    
    if opcao_empresa == "2":
        empresa_nome = "ZEH MOTOCA NATAL"
    else:
        empresa_nome = "ZEH MOTOCA JP"

    print("\nExemplo de formato de data: 01/08/2026 - 09/08/2026")
    data_analise = input("Digite o período da 'Data em Análise': ").strip()
    
    return usuario, senha, empresa_nome, data_analise

def configurar_driver():
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": PASTA_DOWNLOADS,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": PASTA_DOWNLOADS
    })
    return driver

def automatizar_flystart_e_processar_planilha():
    usuario_flystart, senha_flystart, empresa_selecionada, intervalo_datas = solicitar_dados_usuario()

    driver = configurar_driver()
    wait = WebDriverWait(driver, 25)

    try:
        print("\n1. Acessando a página de login do Flystart...")
        driver.get("https://erp.flystart.com.br/flystart/app/")

        # --- LOGIN ---
        print("2. Preenchendo credenciais...")
        campo_usuario = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@placeholder='Digite seu usuário' or @name='usuario' or @id='usuario'] | //input[@type='text' or @type='email']"
        )))
        campo_usuario.clear()
        campo_usuario.send_keys(usuario_flystart)

        campo_senha = driver.find_element(By.XPATH, "//input[@type='password' or @placeholder='Digite sua senha']")
        campo_senha.clear()
        campo_senha.send_keys(senha_flystart)

        btn_login = driver.find_element(By.XPATH, "//button[contains(., 'Entrar')] | //button[@type='submit']")
        btn_login.click()

        # --- SELEÇÃO DE EMPRESA ---
        print(f"3. Selecionando a empresa '{empresa_selecionada}'...")
        opcao_empresa = wait.until(EC.element_to_be_clickable((
            By.XPATH, f"//*[contains(text(), '{empresa_selecionada}')]"
        )))
        opcao_empresa.click()

        print("4. Selecionando o perfil 'Administrador de Empresa'...")
        opcao_admin = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//*[contains(text(), 'Administrador de Empresa')]"
        )))
        opcao_admin.click()

        # --- NAVEGAÇÃO DIRETA AO FINANCEIRO ---
        print("5. Carregando módulo Financeiro...")
        time.sleep(3)
        driver.get("https://erp.flystart.com.br/flystart/app/flystart/financeiro")
        time.sleep(5)

        # --- FILTROS ---
        print(f"6. Preenchendo a Data em Análise com: '{intervalo_datas}'...")
        try:
            campo_data = wait.until(EC.presence_of_element_located((
                By.XPATH, "//label[contains(text(),'Data em Análise')]/following-sibling::input | //input[contains(@placeholder,'/')] | //input[contains(@value,'/')]"
            )))
            driver.execute_script("arguments[0].value = '';", campo_data)
            campo_data.send_keys(intervalo_datas)
            campo_data.send_keys(Keys.TAB)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Aviso ao preencher data: {e}")

        print("7. Aplicando o filtro 'PENDENTE PAGAMENTO'...")
        try:
            input_status = wait.until(EC.presence_of_element_located((By.ID, "statusconta-selectized")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_status)
            driver.execute_script("arguments[0].click();", input_status)
            time.sleep(0.5)
            input_status.send_keys(Keys.BACKSPACE)
            input_status.send_keys(Keys.BACKSPACE)
            input_status.send_keys("PENDENTE PAGAMENTO")
            time.sleep(1.5)
            input_status.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"⚠️ Aviso no status da conta: {e}")

        print("8. Clicando no botão 'Filtrar'...")
        time.sleep(1)
        try:
            driver.execute_script("if (typeof filtrartabela === 'function') { filtrartabela(); } else { $('#btn_filtrar').click(); }")
        except Exception:
            btn_filtrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Filtrar')] | //a[contains(., 'Filtrar')] | //*[@id='btn_filtrar']")))
            driver.execute_script("arguments[0].click();", btn_filtrar)

        print("Aguardando carregamento dos registros...")
        time.sleep(6)

        # --- DOWNLOAD ---
        print("9. Baixando planilha em Excel...")
        btn_excel = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//button[contains(., 'Excel')] | //a[contains(., 'Excel')] | //span[contains(text(), 'Excel')]"
        )))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_excel)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", btn_excel)

        print(f"Aguardando o arquivo em: {PASTA_DOWNLOADS}...")
        time.sleep(8)

    except Exception as e:
        print(f"\n❌ Ocorreu um erro durante a automação: {e}")
    finally:
        driver.quit()

    # --- TRATAMENTO DOS DADOS (PANDAS) ---
    print("\n10. Tratando a planilha baixada...")
    arquivos = (
        glob.glob(os.path.join(PASTA_DOWNLOADS, "*.xlsx")) +
        glob.glob(os.path.join(PASTA_DOWNLOADS, "*.xls")) +
        glob.glob(os.path.join(PASTA_DOWNLOADS, "*.csv"))
    )
    
    if not arquivos:
        print(f"⚠️ Atenção: Nenhum arquivo encontrado em '{PASTA_DOWNLOADS}'.")
        return

    ultimo_arquivo = max(arquivos, key=os.path.getctime)
    print(f"📄 Arquivo encontrado: {os.path.basename(ultimo_arquivo)}")

    try:
        if ultimo_arquivo.endswith(".csv"):
            df = pd.read_csv(ultimo_arquivo, sep=';', encoding='utf-8-sig', header=4)
        else:
            df = pd.read_excel(ultimo_arquivo, header=4)

        df = df.dropna(how='all')

        # -------------------------------------------------------------
        # 1. FILTRAR "Status Locação": REMOVER CONGELADOS E CANCELADOS
        # -------------------------------------------------------------
        col_status_loc = [c for c in df.columns if 'status' in str(c).lower() and 'loca' in str(c).lower()]
        if col_status_loc:
            c_status = col_status_loc[0]
            df = df[~df[c_status].astype(str).str.contains(r'congelad|cancelad', case=False, na=False)]

        # -------------------------------------------------------------
        # 2. LIMPEZA DO NOME DO CLIENTE
        # -------------------------------------------------------------
        col_cliente = [c for c in df.columns if 'cliente' in str(c).lower()]
        if col_cliente:
            c_cli = col_cliente[0]
            def limpar_cliente(texto):
                if pd.isna(texto):
                    return ""
                txt = str(texto)
                txt = re.sub(r'^\s*\[\d+\]\s*-\s*', '', txt)
                txt = re.sub(r'^\s*\(\d+\)\s*-\s*', '', txt)
                txt = re.sub(r'^\s*\d+\s*-\s*', '', txt)
                txt = txt.split('|')[0]
                return txt.strip()

            df[c_cli] = df[c_cli].apply(limpar_cliente)
            df.drop_duplicates(subset=[c_cli], keep='first', inplace=True)

        # -------------------------------------------------------------
        # 3. TRATAR DESCRIÇÃO: YAMAHA E HONDA
        # -------------------------------------------------------------
        col_desc = [c for c in df.columns if 'descri' in str(c).lower()]
        if col_desc:
            c_desc = col_desc[0]
            def tratar_descricao(texto):
                if pd.isna(texto):
                    return ""
                txt = str(texto).strip()
                txt_upper = txt.upper()

                if 'INFRAÇÃO' in txt_upper or 'INFRACAO' in txt_upper or 'MULTA' in txt_upper:
                    return txt

                if any(k in txt_upper for k in ['YBR', 'FACTOR', 'YAMAHA']):
                    return 'YAMAHA'

                if any(k in txt_upper for k in ['CG', 'START', '160', 'HONDA']):
                    return 'HONDA'

                return 'HONDA'

            df[c_desc] = df[c_desc].apply(tratar_descricao)

        # -------------------------------------------------------------
        # 4. TRATAR SALDO (MULTIPLICAR POR 1.13 / 13% DE JUROS)
        # -------------------------------------------------------------
        col_saldo = [c for c in df.columns if 'saldo' in str(c).lower()]
        if col_saldo:
            c_sal = col_saldo[0]
            df = df[~df[c_sal].astype(str).str.contains("Total", case=False, na=False)]

            def converter_saldo_com_juros(valor):
                if pd.isna(valor):
                    return "R$ 0,00"
                try:
                    val_str = str(valor).replace("R$", "").strip()
                    if "," in val_str and "." in val_str:
                        val_str = val_str.replace(".", "").replace(",", ".")
                    elif "," in val_str:
                        val_str = val_str.replace(",", ".")
                    
                    v_float = float(val_str)
                    v_com_juros = v_float * 1.13
                    return f"R$ {v_com_juros:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except (ValueError, TypeError):
                    return valor

            df[c_sal] = df[c_sal].apply(converter_saldo_com_juros)

        # -------------------------------------------------------------
        # 5. REMOVER HÍFEN DAS PLACAS
        # -------------------------------------------------------------
        col_placa = [c for c in df.columns if 'placa' in str(c).lower()]
        if col_placa:
            df[col_placa[0]] = df[col_placa[0]].astype(str).str.replace('-', '', regex=False).str.strip()

        # -------------------------------------------------------------
        # 6. FORMATAR "Data cadastro" (DEIXAR APENAS DD/MM/AAAA)
        # -------------------------------------------------------------
        col_data_cad = [c for c in df.columns if 'data' in str(c).lower() and 'cadast' in str(c).lower()]
        if col_data_cad:
            c_data = col_data_cad[0]
            df[c_data] = df[c_data].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')[0].fillna(df[c_data])

        # -------------------------------------------------------------
        # 7. MANTER APENAS AS 8 COLUNAS DESEJADAS
        # -------------------------------------------------------------
        colunas_finais = []
        padroes_desejados = [
            (r'^id$', 'Id'),
            (r'^tipo$', 'Tipo'),
            (r'cliente', 'Cliente/Fornecedor'),
            (r'descri', 'Descrição'),
            (r'placa', 'Placa'),
            (r'saldo', 'Saldo'),
            (r'data.*cadast', 'Data cadastro'),
            (r'whatsapp', 'WhatsApp')
        ]

        for padrao, nome_padrao in padroes_desejados:
            encontrada = [c for c in df.columns if re.search(padrao, str(c), re.IGNORECASE)]
            if encontrada:
                colunas_finais.append(encontrada[0])

        df = df[colunas_finais]

        # -------------------------------------------------------------
        # 8. SALVAR O ARQUIVO FINAL
        # -------------------------------------------------------------
        data_hoje = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        prefixo_empresa = "NATAL" if "NATAL" in empresa_selecionada else "JP"
        caminho_tratado = os.path.join(PASTA_DOWNLOADS, f"relatorio_{prefixo_empresa}_tratado_{data_hoje}.xlsx")
        
        try:
            with pd.ExcelWriter(caminho_tratado, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Relatório Tratado')

            print("\n✅ Tratamento concluído com sucesso!")
            print(f"📂 Arquivo gerado em: {caminho_tratado}")
            os.startfile(caminho_tratado)
        except PermissionError:
            print("\n❌ ERRO DE PERMISSÃO: O arquivo de destino está aberto no Excel!")
            print("👉 Por favor, feche a planilha no Excel e rode o script novamente.")

    except Exception as e:
        print(f"❌ Erro ao processar a planilha: {e}")

# ==========================================
# PONTO DE ENTRADA DO SCRIPT
# ==========================================
if __name__ == "__main__":
    automatizar_flystart_e_processar_planilha()