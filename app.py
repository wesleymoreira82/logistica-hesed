import streamlit as st
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Configuração da Identidade Visual e Layout
st.set_page_config(page_title="Confirmação de Endereço - Loja Hesed", page_icon="🙏")

st.title("Confirmação de Entrega - Loja Hesed Imaculada")
st.write("Por caridade, preencha os dados abaixo para o reenvio do seu pedido.")

# Inicialização do estado da sessão (Session State)
if 'rua' not in st.session_state:
    st.session_state.update({
        'rua': "", 'bairro': "", 'cidade': "", 'uf': "", 'erro_cep': ""
    })

# Função para buscar o CEP via API
def buscar_cep():
    cep = st.session_state.cep_digito.replace("-", "").replace(".", "").strip()
    st.session_state.erro_cep = "" 
    
    if len(cep) == 8:
        try:
            response = requests.get(f"https://viacep.com.br/ws/{cep}/json/").json()
            if "erro" not in response:
                st.session_state.update({
                    'rua': response.get("logradouro", ""),
                    'bairro': response.get("bairro", ""),
                    'cidade': response.get("localidade", ""),
                    'uf': response.get("uf", "")
                })
            else:
                st.session_state.erro_cep = "CEP não encontrado. Por favor, verifique o número."
                st.session_state.rua = ""
        except:
            st.session_state.erro_cep = "Erro de conexão ao validar o CEP."
    elif len(cep) > 0:
        st.session_state.erro_cep = "O CEP deve ter exatamente 8 dígitos."

# 2. Entrada de Dados (Sem st.form para desativar o envio por Enter)
pedido = st.text_input("Número do Pedido")
nome = st.text_input("Nome Completo")

col_tel, col_email = st.columns(2)
with col_tel:
    telefone = st.text_input("Telefone de Contato (com DDD)")
with col_email:
    email_input = st.text_input("E-mail")

st.divider()

# Exibição do alerta de erro acima do campo de CEP
if st.session_state.erro_cep:
    st.error(st.session_state.erro_cep)

cep_input = st.text_input(
    "CEP", 
    max_chars=9, 
    key="cep_digito", 
    on_change=buscar_cep,
    help="O endereço será preenchido automaticamente ao sair deste campo."
)

# 3. Campos de Endereço
rua = st.text_input("Logradouro (Rua/Avenida)", value=st.session_state.rua)

col_num, col_comp = st.columns([1, 2])
with col_num:
    numero = st.text_input("Número")
with col_comp:
    complemento = st.text_input("Complemento (Ex: Casa 12 A)")

bairro = st.text_input("Bairro", value=st.session_state.bairro)

col_cid, col_uf = st.columns([3, 1])
with col_cid:
    cidade = st.text_input("Cidade", value=st.session_state.cidade)
with col_uf:
    uf = st.text_input("UF", value=st.session_state.uf)

st.divider()

# 4. Pré-visualização e Lógica de Envio
if not pedido or not nome or not cep_input or not numero or st.session_state.erro_cep:
    st.warning("Preencha corretamente os campos obrigatórios para liberar a confirmação.")
else:
    # Montagem do resumo formatado em linhas para cópia direta
    endereco_linha = f"{rua}, {numero}"
    if complemento:
        endereco_linha += f" ({complemento})"
    
    resumo_texto = (
        f"PEDIDO: #{pedido}\n"
        f"CLIENTE: {nome}\n"
        f"TELEFONE: {telefone}\n"
        f"E-MAIL: {email_input}\n"
        f"ENDEREÇO: {endereco_linha}\n"
        f"{bairro}\n"
        f"CIDADE: {cidade} - {uf}\n"
        f"CEP: {cep_input}"
    )

    st.subheader("Conferir Dados de Entrega")
    st.info(resumo_texto)
    
    # Botão de Envio Único
    if st.button("Confirmar e Enviar para a Loja"):
        try:
            # Conexão segura via Secrets do Streamlit
            creds_info = st.secrets["gcp_service_account"]
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            client = gspread.authorize(creds)
            
            # Abertura da planilha e envio de coluna única
            sheet = client.open("Logistica_Hesed").sheet1
            sheet.append_row([resumo_texto])
            
            st.success("Dados enviados com sucesso!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Erro técnico ao salvar: {e}")
