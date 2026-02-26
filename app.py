import streamlit as st
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Identidade Visual
st.set_page_config(page_title="Confirmação de Endereço - Loja Hesed", page_icon="#")
st.title("Confirmação de Entrega - Loja Hesed Imaculada")

# Estado da sessão para o CEP
if 'rua' not in st.session_state:
    st.session_state.update({'rua': "", 'bairro': "", 'cidade': "", 'uf': "", 'erro_cep': ""})

def buscar_cep():
    cep = st.session_state.cep_digito.replace("-", "").replace(".", "").strip()
    st.session_state.erro_cep = "" 
    if len(cep) == 8:
        try:
            res = requests.get(f"https://viacep.com.br/ws/{cep}/json/").json()
            if "erro" not in res:
                st.session_state.update({'rua': res.get("logradouro", ""), 'bairro': res.get("bairro", ""), 
                                       'cidade': res.get("localidade", ""), 'uf': res.get("uf", "")})
            else:
                st.session_state.erro_cep = "CEP não encontrado."
        except:
            st.session_state.erro_cep = "Erro na busca do CEP."

# 2. Campos de Entrada
pedido = st.text_input("Número do Pedido")
nome = st.text_input("Nome Completo")
col1, col2 = st.columns(2)
with col1: telefone = st.text_input("Telefone")
with col2: email = st.text_input("E-mail")

st.divider()
if st.session_state.erro_cep: st.error(st.session_state.erro_cep)
cep_input = st.text_input("CEP", max_chars=9, key="cep_digito", on_change=buscar_cep)
rua = st.text_input("Logradouro", value=st.session_state.rua)
c_n, c_c = st.columns([1, 2])
with c_n: numero = st.text_input("Número")
with c_c: complemento = st.text_input("Complemento")
bairro = st.text_input("Bairro", value=st.session_state.bairro)
c_ci, c_uf = st.columns([3, 1])
with c_ci: cidade = st.text_input("Cidade", value=st.session_state.cidade)
with c_uf: uf = st.text_input("UF", value=st.session_state.uf)

# 3. Resumo e Envio
if pedido and nome and cep_input and numero and not st.session_state.erro_cep:
    end_formatado = f"{rua}, {numero}" + (f" ({complemento})" if complemento else "")
    resumo = (f"PEDIDO: #{pedido}\nCLIENTE: {nome}\nTELEFONE: {telefone}\n"
              f"E-MAIL: {email}\nENDERECO: {end_formatado}\n{bairro}\n"
              f"CIDADE: {cidade} - {uf}\nCEP: {cep_input}")
    
    st.subheader("Conferir Dados")
    st.info(resumo)
    
    if st.button("Confirmar e Enviar para a Loja"):
        try:
            # Conexão segura via Secrets
            creds_info = st.secrets["gcp_service_account"]
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            client = gspread.authorize(creds)
            
            # Abertura da planilha e envio de coluna única
            sheet = client.open("Logistica_Hesed").sheet1
            sheet.append_row([resumo])
            
            st.success("Dados enviados com sucesso!")
            st.balloons()
        except Exception as e:
            st.error(f"Erro de autenticação: {e}")
