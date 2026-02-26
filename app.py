import streamlit as st
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Configuracao da Identidade Visual
st.set_page_config(page_title="Confirmacao de Endereco - Loja Hesed", page_icon="🙏")

st.title("Confirmacao de Entrega - Loja Hesed Imaculada")
st.write("Por caridade, preencha os dados abaixo para o reenvio do seu pedido.")

# Inicializacao do estado da sessao
if 'rua' not in st.session_state:
    st.session_state.rua = ""
    st.session_state.bairro = ""
    st.session_state.cidade = ""
    st.session_state.uf = ""
    st.session_state.erro_cep = ""

# Funcao para buscar o CEP
def buscar_cep():
    cep = st.session_state.cep_digito.replace("-", "").replace(".", "").strip()
    st.session_state.erro_cep = "" 
    
    if len(cep) == 8:
        try:
            response = requests.get(f"https://viacep.com.br/ws/{cep}/json/").json()
            if "erro" not in response:
                st.session_state.rua = response.get("logradouro", "")
                st.session_state.bairro = response.get("bairro", "")
                st.session_state.cidade = response.get("localidade", "")
                st.session_state.uf = response.get("uf", "")
            else:
                st.session_state.erro_cep = "CEP nao encontrado. Por favor, verifique o numero."
                st.session_state.rua = ""
        except:
            st.session_state.erro_cep = "Erro de conexao ao validar o CEP."

# 2. Entrada de Dados
pedido = st.text_input("Numero do Pedido")
nome = st.text_input("Nome Completo")

col_tel, col_email = st.columns(2)
with col_tel:
    telefone = st.text_input("Telefone de Contato (com DDD)")
with col_email:
    email_input = st.text_input("E-mail")

st.divider()

if st.session_state.erro_cep:
    st.error(st.session_state.erro_cep)

cep_input = st.text_input("CEP", max_chars=9, key="cep_digito", on_change=buscar_cep)

rua = st.text_input("Logradouro (Rua/Avenida)", value=st.session_state.rua)

col_num, col_comp = st.columns([1, 2])
with col_num:
    numero = st.text_input("Numero")
with col_comp:
    complemento = st.text_input("Complemento (Ex: Casa 12 A)")

bairro = st.text_input("Bairro", value=st.session_state.bairro)

col_cid, col_uf = st.columns([3, 1])
with col_cid:
    cidade = st.text_input("Cidade", value=st.session_state.cidade)
with col_uf:
    uf = st.text_input("UF", value=st.session_state.uf)

st.divider()

# 3. Pre-visualizacao e Envio Único
if not pedido or not nome or not cep_input or not numero or st.session_state.erro_cep:
    st.warning("Preencha os campos obrigatorios para liberar a confirmacao.")
else:
    # Montagem do resumo formatado incluindo E-mail
    endereco_linha = f"{rua}, {numero}"
    if complemento:
        endereco_linha += f" ({complemento})"
    
    # Criando o bloco de texto formatado
    resumo_texto = (
        f"PEDIDO: #{pedido}\n"
        f"CLIENTE: {nome}\n"
        f"TELEFONE: {telefone}\n"
        f"E-MAIL: {email_input}\n"
        f"ENDERECO: {endereco_linha}\n"
        f"{bairro}\n"
        f"CIDADE: {cidade} - {uf}\n"
        f"CEP: {cep_input}"
    )

    st.subheader("Conferir Dados de Entrega")
    st.info(resumo_texto)
    
    if st.button("Confirmar e Enviar para a Loja"):
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
            client = gspread.authorize(creds)
            sheet = client.open("Logistica_Hesed").sheet1
            
            # Envia o resumo completo para a Coluna A da planilha
            sheet.append_row([resumo_texto])
            
            st.success("Dados enviados com sucesso!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Erro tecnico ao salvar: {e}")