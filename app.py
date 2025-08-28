import streamlit as st
from datetime import datetime
import pytz
from typing import List, Dict, Tuple, Any

# --- Configurações da Página ---
st.set_page_config(
    page_title="Processador de Dados Alpha7",
    page_icon="📦",
    layout="wide"
)

# --- Constantes ---
TIMEZONE = "America/Sao_Paulo"
LAYOUT_OPTIONS = {
    "Layout Apha7": "Apha7",
    "Layout InovaFarma": "InovaFarma", # Alterado de "Layout 2"
    "Layout 3": "L3",
    "Layout 4": "L4",
}

# --- Inicialização do Estado da Sessão ---
# Usamos st.session_state para manter os dados entre os uploads de arquivos
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = []
if 'errors' not in st.session_state:
    st.session_state.errors = []
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = set()


# --- Funções de Lógica de Negócio ---

def parse_uploaded_file(uploaded_file: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Lê um arquivo .txt enviado, valida cada linha e extrai os dados."""
    processed_data = []
    errors = []
    
    if not uploaded_file:
        return [], []

    try:
        # Resetamos o ponteiro do arquivo para garantir a leitura correta
        uploaded_file.seek(0)
        lines = uploaded_file.read().decode("utf-8").splitlines()
    except Exception as e:
        errors.append(f"Erro ao ler o arquivo '{uploaded_file.name}': {e}")
        return [], errors

    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if not stripped_line:
            continue

        parts = stripped_line.split(',')
        if len(parts) != 2:
            errors.append(f"Arquivo '{uploaded_file.name}', Linha {line_num}: Formato inválido. Esperado 'CODIGO,QUANTIDADE'.")
            continue

        code = parts[0].strip()
        quantity_str = parts[1].strip()

        if not code:
            errors.append(f"Arquivo '{uploaded_file.name}', Linha {line_num}: O código de barras não pode estar vazio.")
            continue
        
        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                 errors.append(f"Arquivo '{uploaded_file.name}', Linha {line_num}: A quantidade deve ser um número positivo.")
                 continue
            processed_data.append({"code": code, "quantity": quantity})
        except ValueError:
            errors.append(f"Arquivo '{uploaded_file.name}', Linha {line_num}: Quantidade '{quantity_str}' não é um número inteiro válido.")
            
    return processed_data, errors


def format_output_data(data: List[Dict[str, Any]], layout: str, timezone_str: str) -> str:
    """Formata os dados processados no layout de saída especificado."""
    sorted_data = sorted(data, key=lambda x: x['quantity'])

    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        date_str = now.strftime("%Y%m%d")
        time_str_content = now.strftime("%H%M%S")
    except pytz.UnknownTimeZoneError:
        now = datetime.utcnow()
        date_str = now.strftime("%Y%m%d")
        time_str_content = now.strftime("%H%M%S")

    result_lines = []
    for item in sorted_data:
        # Lógica de formatação específica para cada layout
        if layout == "Layout InovaFarma":
            # Para InovaFarma, a saída é apenas CODIGO,QUANTIDADE
            line = f"{item['code']},{item['quantity']}"
            result_lines.append(line)
        else:
            # Lógica para os outros layouts
            base_line = f"{date_str},{time_str_content},{item['code']},{item['quantity']}"
            
            # Adiciona sufixo específico do layout, se houver
            if layout != "Layout Apha7":
                layout_suffix = layout.replace(" ", "")
                base_line += f",{layout_suffix}"
            
            result_lines.append(base_line)

    return "\n".join(result_lines)


def generate_filename(layout: str, timezone_str: str) -> str:
    """Gera um nome de arquivo dinâmico para o download."""
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
    except pytz.UnknownTimeZoneError:
        now = datetime.utcnow()

    date_str = now.strftime("%Y%m%d")
    time_str_filename = now.strftime("%H%M")
    
    layout_short = LAYOUT_OPTIONS.get(layout, "Layout")
    
    return f"Dados_Consolidados_{layout_short}_{date_str}_{time_str_filename}.txt"


# --- Interface do Usuário (Streamlit) ---

st.title("📦 Processador de Dados de Códigos de Barras")
st.subheader("Para Alpha7 V3.0 (Múltiplos Arquivos)")
st.markdown("---")

# --- Barra Lateral para Configurações ---
st.sidebar.header("⚙️ Configurações de Saída")
selected_layout = st.sidebar.selectbox(
    "Escolha o Layout:",
    options=list(LAYOUT_OPTIONS.keys()),
    help="Selecione o formato final do arquivo de texto consolidado."
)

# --- Área Principal ---
col1, col2 = st.columns([1, 2])

with col1:
    st.info("**Instruções:**")
    st.markdown("""
    1.  **Escolha o Layout** na barra lateral.
    2.  **Envie um ou mais arquivos** `.txt` usando o botão ao lado.
    3.  Os dados serão acumulados. Você pode enviar mais arquivos se precisar.
    4.  Quando terminar de enviar, clique em **Processar Dados Acumulados**.
    5.  Para começar do zero, clique em **Limpar e Recomeçar**.
    """)
    st.code("CODIGO_BARRAS_1,10\nCODIGO_BARRAS_2,5", language="text")

with col2:
    uploaded_files = st.file_uploader(
        "Envie um ou mais arquivos .txt aqui",
        type="txt",
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        new_files_to_process = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
        if new_files_to_process:
            with st.spinner("Lendo novos arquivos..."):
                for file in new_files_to_process:
                    data, errors = parse_uploaded_file(file)
                    st.session_state.processed_data.extend(data)
                    st.session_state.errors.extend(errors)
                    st.session_state.processed_files.add(file.name)
            st.rerun() # Atualiza a tela para mostrar o novo status

    # --- Exibe o status atual e os botões de ação ---
    total_items = len(st.session_state.processed_data)
    
    if total_items > 0:
        st.success(f"**{total_items}** itens de **{len(st.session_state.processed_files)}** arquivo(s) carregados e prontos para processar.")

    if st.session_state.errors:
        st.error("❌ Foram encontrados erros em alguns arquivos:")
        with st.expander("Clique para ver os detalhes dos erros"):
            for error in st.session_state.errors:
                st.write(f"- {error}")
        st.warning("As linhas com erro foram ignoradas. Continue ou limpe para corrigir.")
    
    # Botões de controle
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        # O botão de processar só aparece se houver dados válidos
        if st.button("🚀 Processar Dados Acumulados", disabled=not st.session_state.processed_data, use_container_width=True):
            st.session_state.run_processing = True # Flag para iniciar o processamento
    
    with btn_col2:
        if st.button("🧹 Limpar e Recomeçar", use_container_width=True):
            # Limpa todo o estado da sessão
            st.session_state.processed_data = []
            st.session_state.errors = []
            st.session_state.processed_files = set()
            if 'run_processing' in st.session_state:
                del st.session_state.run_processing
            st.rerun()

    # --- Área de Resultados (só aparece depois de clicar em "Processar") ---
    if st.session_state.get('run_processing', False):
        st.markdown("---")
        st.header("Resultado Consolidado")

        result_text = format_output_data(st.session_state.processed_data, selected_layout, TIMEZONE)
        download_file_name = generate_filename(selected_layout, TIMEZONE)

        st.text_area(
            f"Resultado formatado ({selected_layout}):",
            result_text,
            height=300,
            help="Este é o conteúdo do arquivo consolidado que será baixado."
        )

        st.download_button(
            label="⬇️ Baixar Resultado Consolidado",
            data=result_text,
            file_name=download_file_name,
            mime="text/plain",
            use_container_width=True
        )
