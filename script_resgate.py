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
    
    print("\nExemplo de formato de data: 01/08/2026 - 09/08/2026")
    data_analise = input("Digite o período da 'Data em Análise': ").strip()
    
    return usuario, senha, data_analise

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
    usuario_flystart, senha_flystart, intervalo_datas = solicitar_dados_usuario()

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

        # --- SELEÇÃO DE EMPRESA E PERFIL ---
        print("3. Selecionando a empresa 'ZEH MOTOCA JP'...")
        opcao_zeh_jp = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'ZEH MOTOCA JP')]")))
        opcao_zeh_jp.click()

        print("4. Selecionando o perfil 'Administrador de Empresa'...")
        opcao_admin = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Administrador de Empresa')]")))
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
            df = pd.read_csv(ultimo_arquivo, sep=';', encoding='utf-8-sig', skiprows=6)
        else:
            df = pd.read_excel(ultimo_arquivo, skiprows=6)

        df = df.dropna(how='all')

        # 1. FILTRAR E EXCLUIR LINHAS CANCELADAS E CONGELADAS (STATUS)
        termo_exclusao = r'cancelad|congelad'
        cols_status = [c for c in df.columns if 'status' in str(c).lower() or 'aprovad' in str(df[c].astype(str)).lower()]
        
        if cols_status:
            for col in cols_status:
                df = df[~df[col].astype(str).str.contains(termo_exclusao, case=False, na=False)]
        else:
            ultima_coluna = df.columns[-1]
            df = df[~df[ultima_coluna].astype(str).str.contains(termo_exclusao, case=False, na=False)]

        # 2. TRATAR SALDO (MULTIPLICAR POR 1.13 E FORMATAR EM R$)
        col_saldo_candidates = [c for c in df.columns if 'saldo' in str(c).lower() or 'valor' in str(c).lower()]
        col_saldo_nome = col_saldo_candidates[0] if col_saldo_candidates else df.columns[9]

        df = df[~df[col_saldo_nome].astype(str).str.contains("Total", case=False, na=False)]

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

        df[col_saldo_nome] = df[col_saldo_nome].apply(converter_saldo_com_juros)
        df.rename(columns={col_saldo_nome: 'Saldo com Juros (13%)'}, inplace=True)

        # 3. EXCLUIR COLUNAS DESNECESSÁRIAS
        colunas_para_remover = [
            'Empresa', 'Parcela', 'Saldo', 'Nº documento', 'Status', 
            'Vencimento', 'Ultimo pagamento', 'Banco', 'Forma de pagamento', 
            'Vendedor', 'E-mail', 'Link boleto', 'Unnamed: 14', 'Unnamed: 15'
        ]
        cols_existentes = [c for c in colunas_para_remover if c in df.columns]
        df.drop(columns=cols_existentes, inplace=True, errors='ignore')

        # 4. LIMPEZA ADICIONAL
        if 'Cliente' in df.columns:
            df['Cliente'] = df['Cliente'].astype(str).apply(lambda x: re.sub(r'\(.*?\)', '', x))
            df['Cliente'] = df['Cliente'].str.replace('|', '', regex=False).str.strip()
            df.drop_duplicates(subset=['Cliente'], keep='first', inplace=True)

        col_desc = [c for c in df.columns if 'descri' in str(c).lower()]
        if col_desc:
            c_nome = col_desc[0]
            df[c_nome] = df[c_nome].astype(str).str.replace('CG 160', 'HONDA', regex=False)
            df[c_nome] = df[c_nome].astype(str).str.replace('YBR 150', 'YAMAHA', regex=False)

        if 'Placa' in df.columns:
            df['Placa'] = df['Placa'].astype(str).str.replace('-', '', regex=False).str.strip()

        # 5. SALVAR ARQUIVO FINAL
        data_hoje = datetime.date.today().strftime("%d-%m-%Y")
        caminho_tratado = os.path.join(PASTA_DOWNLOADS, f"relatorio_final_tratado_{data_hoje}.xlsx")
        
        with pd.ExcelWriter(caminho_tratado, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório Tratado')

        print("\n✅ Tratamento concluído com sucesso!")
        print(f"📂 Arquivo gerado em: {caminho_tratado}")
        os.startfile(caminho_tratado)

    except Exception as e:
        print(f"❌ Erro ao processar a planilha: {e}")

# ==========================================
# PONTO DE ENTRADA DO SCRIPT (EXECUÇÃO)
# ==========================================
if __name__ == "__main__":
    automatizar_flystart_e_processar_planilha()