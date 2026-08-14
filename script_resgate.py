import os
import time
import glob
import datetime
import re
import threading
import sys
import pandas as pd

import customtkinter as ctk
from selenium import webdriver
from selenium.webdriver.chrome.options import Options  # <-- IMPORTAÇÃO CORRIGIDA
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuração de Aparência do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

PASTA_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Automação Flystart - Relatórios")
        self.geometry("520x680")
        self.resizable(False, False)

        # Container Principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Título
        self.lbl_titulo = ctk.CTkLabel(
            self.main_frame, 
            text="Automação ERP Flystart", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_titulo.pack(pady=(15, 5))

        self.lbl_subtitulo = ctk.CTkLabel(
            self.main_frame, 
            text="Preencha os dados abaixo para gerar o relatório", 
            font=ctk.CTkFont(size=12)
        )
        self.lbl_subtitulo.pack(pady=(0, 15))

        # Campo Usuário / CPF
        self.entry_usuario = ctk.CTkEntry(
            self.main_frame, 
            placeholder_text="Usuário / CPF no Flystart", 
            width=360
        )
        self.entry_usuario.pack(pady=8)

        # Campo Senha
        self.entry_senha = ctk.CTkEntry(
            self.main_frame, 
            placeholder_text="Senha do Flystart", 
            show="*", 
            width=360
        )
        self.entry_senha.pack(pady=8)

        # Seleção de Empresa (Segmented Button)
        self.lbl_empresa = ctk.CTkLabel(self.main_frame, text="Selecione a Empresa:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_empresa.pack(pady=(10, 2))

        self.seg_empresa = ctk.CTkSegmentedButton(
            self.main_frame, 
            values=["ZEH MOTOCA JP", "ZEH MOTOCA NATAL"],
            width=360
        )
        self.seg_empresa.set("ZEH MOTOCA JP")
        self.seg_empresa.pack(pady=5)

        # Campo Data em Análise
        self.lbl_data = ctk.CTkLabel(self.main_frame, text="Período (Ex: 01/08/2026 - 09/08/2026):", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_data.pack(pady=(10, 2))

        self.entry_data = ctk.CTkEntry(
            self.main_frame, 
            placeholder_text="01/08/2026 - 09/08/2026", 
            width=360
        )
        self.entry_data.pack(pady=5)

        # Botão de Iniciar
        self.btn_iniciar = ctk.CTkButton(
            self.main_frame, 
            text="🚀 Iniciar Processamento", 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=360,
            command=self.iniciar_automacao_thread
        )
        self.btn_iniciar.pack(pady=(15, 10))

        # Caixa de Log/Status
        self.textbox_log = ctk.CTkTextbox(self.main_frame, width=440, height=180, font=ctk.CTkFont(size=11))
        self.textbox_log.pack(pady=10, padx=10)
        self.textbox_log.configure(state="disabled")

    def log(self, mensagem):
        """Insere mensagens no campo de texto de log da interface."""
        self.textbox_log.configure(state="normal")
        self.textbox_log.insert("end", f"{mensagem}\n")
        self.textbox_log.see("end")
        self.textbox_log.configure(state="disabled")

    def iniciar_automacao_thread(self):
        """Executa a automação em uma thread secundária para não travar a interface."""
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get().strip()
        empresa = self.seg_empresa.get()
        intervalo_datas = self.entry_data.get().strip()

        if not usuario or not senha or not intervalo_datas:
            self.log("⚠️ Por favor, preencha todos os campos obrigatórios!")
            return

        self.btn_iniciar.configure(state="disabled")
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", "end")
        self.textbox_log.configure(state="disabled")

        thread = threading.Thread(
            target=self.executar_automacao, 
            args=(usuario, senha, empresa, intervalo_datas),
            daemon=True
        )
        thread.start()

    def configurar_driver(self):
        """Configuração corrigida do Chrome Options."""
        chrome_options = Options() # <-- INSTÂNCIA CORRETA
        prefs = {
            "download.default_directory": PASTA_DOWNLOADS,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def executar_automacao(self, usuario_flystart, senha_flystart, empresa_selecionada, intervalo_datas):
        driver = None
        try:
            self.log("⏳ Iniciando navegador Chrome...")
            driver = self.configurar_driver()
            wait = WebDriverWait(driver, 25)

            self.log("1. Acessando página de login do Flystart...")
            driver.get("https://erp.flystart.com.br/flystart/app/")

            # LOGIN
            self.log("2. Preenchendo credenciais...")
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

            # SELEÇÃO DE EMPRESA
            self.log(f"3. Selecionando a empresa '{empresa_selecionada}'...")
            opcao_empresa = wait.until(EC.element_to_be_clickable((
                By.XPATH, f"//*[contains(text(), '{empresa_selecionada}')]"
            )))
            opcao_empresa.click()

            self.log("4. Selecionando perfil 'Administrador de Empresa'...")
            opcao_admin = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//*[contains(text(), 'Administrador de Empresa')]"
            )))
            opcao_admin.click()

            # NAVEGAÇÃO FINANCEIRO
            self.log("5. Carregando módulo Financeiro...")
            time.sleep(3)
            driver.get("https://erp.flystart.com.br/flystart/app/flystart/financeiro")
            time.sleep(5)

            # FILTROS
            self.log(f"6. Aplicando período: '{intervalo_datas}'...")
            try:
                campo_data = wait.until(EC.presence_of_element_located((
                    By.XPATH, "//label[contains(text(),'Data em Análise')]/following-sibling::input | //input[contains(@placeholder,'/')] | //input[contains(@value,'/')]"
                )))
                driver.execute_script("arguments[0].value = '';", campo_data)
                campo_data.send_keys(intervalo_datas)
                campo_data.send_keys(Keys.TAB)
                time.sleep(1)
            except Exception as e:
                self.log(f"⚠️ Aviso no preenchimento de data: {e}")

            self.log("7. Aplicando filtro 'PENDENTE PAGAMENTO'...")
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
                self.log(f"⚠️ Aviso no status: {e}")

            self.log("8. Executando filtro na tabela...")
            time.sleep(1)
            try:
                driver.execute_script("if (typeof filtrartabela === 'function') { filtrartabela(); } else { $('#btn_filtrar').click(); }")
            except Exception:
                btn_filtrar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Filtrar')] | //a[contains(., 'Filtrar')] | //*[@id='btn_filtrar']")))
                driver.execute_script("arguments[0].click();", btn_filtrar)

            time.sleep(6)

            # DOWNLOAD
            self.log("9. Solicitando download do arquivo Excel...")
            btn_excel = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//button[contains(., 'Excel')] | //a[contains(., 'Excel')] | //span[contains(text(), 'Excel')]"
            )))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_excel)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", btn_excel)

            self.log("Aguardando conclusão do download...")
            time.sleep(8)

        except Exception as e:
            self.log(f"❌ Erro na automação: {e}")
        finally:
            if driver:
                driver.quit()

        # PROCESSAMENTO PANDAS
        self.log("\n10. Tratando os dados do arquivo baixado...")
        self.tratar_planilha_baixada(empresa_selecionada)

        self.btn_iniciar.configure(state="normal")

    def tratar_planilha_baixada(self, empresa_selecionada):
        arquivos = (
            glob.glob(os.path.join(PASTA_DOWNLOADS, "*.xlsx")) +
            glob.glob(os.path.join(PASTA_DOWNLOADS, "*.xls")) +
            glob.glob(os.path.join(PASTA_DOWNLOADS, "*.csv"))
        )
        
        if not arquivos:
            self.log("⚠️ Nenhum arquivo encontrado na pasta Downloads.")
            return

        ultimo_arquivo = max(arquivos, key=os.path.getctime)
        self.log(f"📄 Arquivo identificado: {os.path.basename(ultimo_arquivo)}")

        try:
            if ultimo_arquivo.endswith(".csv"):
                df = pd.read_csv(ultimo_arquivo, sep=';', encoding='utf-8-sig', header=4)
            else:
                df = pd.read_excel(ultimo_arquivo, header=4)

            df = df.dropna(how='all')

            # 1. Filtrar Status Locação
            col_status_loc = [c for c in df.columns if 'status' in str(c).lower() and 'loca' in str(c).lower()]
            if col_status_loc:
                c_status = col_status_loc[0]
                df = df[~df[c_status].astype(str).str.contains(r'congelad|cancelad', case=False, na=False)]

            # 2. Limpeza Cliente
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

            # 3. Descrição
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

            # 4. Saldo + Juros
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

            # 5. Placas
            col_placa = [c for c in df.columns if 'placa' in str(c).lower()]
            if col_placa:
                df[col_placa[0]] = df[col_placa[0]].astype(str).str.replace('-', '', regex=False).str.strip()

            # 6. Data Cadastro
            col_data_cad = [c for c in df.columns if 'data' in str(c).lower() and 'cadast' in str(c).lower()]
            if col_data_cad:
                c_data = col_data_cad[0]
                df[c_data] = df[c_data].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')[0].fillna(df[c_data])

            # 7. Dias de Atraso
            col_venc = [c for c in df.columns if 'venc' in str(c).lower()]
            if col_venc:
                c_venc = col_venc[0]
                venc_dt = pd.to_datetime(df[c_venc], format='%d/%m/%Y', errors='coerce')
                hoje = pd.to_datetime(datetime.date.today())
                
                def formatar_dias(dias):
                    if pd.isna(dias) or dias <= 0:
                        return "0 DIAS"
                    dias = int(dias)
                    return f"{dias} DIA" if dias == 1 else f"{dias} DIAS"

                dias_calculados = (hoje - venc_dt).dt.days + 1
                df['Dias de Atraso'] = dias_calculados.apply(formatar_dias)

            # 8. Colunas Finais
            colunas_finais = []
            padroes_desejados = [
                (r'^id$', 'Id'),
                (r'^tipo$', 'Tipo'),
                (r'cliente', 'Cliente/Fornecedor'),
                (r'descri', 'Descrição'),
                (r'placa', 'Placa'),
                (r'saldo', 'Saldo'),
                (r'data.*cadast', 'Data cadastro'),
                (r'dias de atraso', 'Dias de Atraso'),
                (r'whatsapp', 'WhatsApp')
            ]

            for padrao, nome_padrao in padroes_desejados:
                encontrada = [c for c in df.columns if re.search(padrao, str(c), re.IGNORECASE)]
                if encontrada:
                    colunas_finais.append(encontrada[0])

            df = df[colunas_finais]

            # 9. Salvar
            data_hoje = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            prefixo_empresa = "NATAL" if "NATAL" in empresa_selecionada else "JP"
            caminho_tratado = os.path.join(PASTA_DOWNLOADS, f"relatorio_{prefixo_empresa}_tratado_{data_hoje}.xlsx")
            
            with pd.ExcelWriter(caminho_tratado, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Relatório Tratado')

            self.log("\n✅ Processo concluído com sucesso!")
            self.log(f"📂 Arquivo gerado em:\n{caminho_tratado}")
            os.startfile(caminho_tratado)

        except PermissionError:
            self.log("❌ ERRO: A planilha já está aberta no Excel. Feche-a e tente novamente.")
        except Exception as e:
            self.log(f"❌ Erro ao tratar planilha: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
