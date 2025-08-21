import streamlit as st
from datetime import datetime
import pytz
from typing import List, Dict, Tuple, Optional, Any

# --- Configurações da Página ---
# Usar st.set_page_config() como o primeiro comando do Streamlit
st.set_page_config(
    page_title="Processador de Dados Alpha7",
    page_icon="📦",
    layout="wide"
)

# --- Constantes ---
# Definir constantes torna o código mais fácil de manter
TIMEZONE = "America/Sao_Paulo"
LAYOUT_OPTIONS = {
    "Layout 1": "L1",
    "Layout 2": "L2",
    "Layout 3": "L3",
    "Layout 4": "L4",
}

# --- Funções de Lógica de Negócio ---

def parse_uploaded_file(uploaded_file: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Lê um arquivo .txt enviado, valida cada linha e extrai os dados.

    Args:
        uploaded_file: O objeto de arquivo retornado por st.file_uploader.

    Returns:
        Uma tupla contendo:
        - Uma lista de dicionários com os dados processados (ex: [{'code': '123', 'quantity': 10}]).
        - Uma lista de strings com as mensagens de erro encontradas.
    """
    processed_data = []
    errors = []
    
    if not uploaded_file:
        return [], []

    try:
        lines = uploaded_file.read().decode("utf-8").splitlines()
    except Exception as e:
        errors.append(f"Erro ao ler o arquivo: {e}")
        return [], errors

    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if not stripped_line:  # Pula linhas vazias
            continue

        parts = stripped_line.split(',')
        if len(parts) != 2:
            errors.append(f"Linha {line_num}: Formato inválido. Esperado 'CODIGO,QUANTIDADE'. Encontrado: '{line}'")
            continue

        code = parts[0].strip()
        quantity_str = parts[1].strip()

        if not code:
            errors.append(f"Linha {line_num}: O código de barras não pode estar vazio.")
            continue
        
        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                 errors.append(f"Linha {line_num}: A quantidade deve ser um número positivo. Valor: '{quantity_str}'")
                 continue
            processed_data.append({"code": code, "quantity": quantity})
        except ValueError:
            errors.append(f"Linha {line_num}: Quantidade '{quantity_str}' não é um número inteiro válido.")
            
    return processed_data, errors


def format_output_data(data: List[Dict[str, Any]], layout: str, timezone_str: str) -> str:
    """
    Formata os dados processados no layout de saída especificado.

    Args:
        data: Lista de dicionários com os dados.
        layout: O nome do layout selecionado.
        timezone_str: A string do fuso horário (ex: 'America/Sao_Paulo').

    Returns:
        Uma string única com todos os dados formatados, prontos para exibição ou download.
    """
    # 1. Ordena os dados pela quantidade (do menor para o maior)
    sorted_data = sorted(data, key=lambda x: x['quantity'])

    # 2. Obtém a data e hora atuais no fuso horário correto
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        date_str = now.strftime("%Y%m%d")
        time_str_content = now.strftime("%H%M%S")
    except pytz.UnknownTimeZoneError:
        # Fallback para UTC caso o fuso horário seja inválido
        now = datetime.utcnow()
        date_str = now.strftime("%Y%m%d")
        time_str_content = now.strftime("%H%M%S")


    # 3. Monta as linhas de resultado com base no layout
    result_lines = []
    for item in sorted_data:
        # Base da linha, comum a todos os layouts
        base_line = f"{date_str},{time_str_content},{item['code']},{item['quantity']}"
        
        # Adiciona sufixo específico do layout, se houver
        if layout != "Layout 1":
            layout_suffix = layout.replace(" ", "") # Ex: "Layout2"
            base_line += f",{layout_suffix}"
            
        result_lines.append(base_line)

    return "\n".join(result_lines)


def generate_filename(layout: str, timezone_str: str) -> str:
    """
    Gera um nome de arquivo dinâmico para o download.

    Args:
        layout: O nome do layout selecionado.
        timezone_str: A string do fuso horário.

    Returns:
        O nome do arquivo formatado.
    """
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
    except pytz.UnknownTimeZoneError:
        now = datetime.utcnow()

    date_str = now.strftime("%Y%m%d")
    time_str_filename = now.strftime("%H%M")
    
    layout_short = LAYOUT_OPTIONS.get(layout, "Layout")
    
    return f"Dados_formatados_{layout_short}_{date_str}_{time_str_filename}.txt"


# --- Interface do Usuário (Streamlit) ---

st.title("📦 Processador de Dados de Códigos de Barras")
st.subheader("Para Alpha7 V2.0")
st.markdown("---")

# --- Barra Lateral para Configurações ---
st.sidebar.header("⚙️ Configurações de Saída")
selected_layout = st.sidebar.selectbox(
    "Escolha o Layout:",
    options=list(LAYOUT_OPTIONS.keys()),
    help="Selecione o formato final do arquivo de texto."
)

# --- Área Principal ---
col1, col2 = st.columns([1, 2])

with col1:
    st.info("**Instruções:**")
    st.markdown("""
    1.  **Escolha o Layout** na barra lateral esquerda.
    2.  **Envie um arquivo `.txt`** usando o botão abaixo.
    3.  O arquivo deve ter uma entrada por linha no formato: `CODIGO,QUANTIDADE`.
    4.  Visualize o resultado e clique no botão para **baixar o arquivo formatado**.
    """)
    
    # Exemplo de formato
    st.code("0789000012345,10\n0789000067890,5\n0789000011223,25", language="text")

with col2:
    uploaded_file = st.file_uploader(
        "Envie seu arquivo .txt aqui",
        type="txt",
        label_visibility="collapsed"
    )

    if uploaded_file:
        processed_data, errors = parse_uploaded_file(uploaded_file)

        if errors:
            st.error("❌ Foram encontrados erros no arquivo:")
            with st.expander("Clique para ver os detalhes dos erros"):
                for error in errors:
                    st.write(f"- {error}")
            st.warning("Por favor, corrija o arquivo e envie novamente.")
        
        elif not processed_data:
            st.warning("⚠️ O arquivo está vazio ou não contém dados válidos no formato esperado.")

        else:
            st.success(f"✅ Arquivo processado com sucesso! {len(processed_data)} linhas válidas encontradas.")
            
            result_text = format_output_data(processed_data, selected_layout, TIMEZONE)
            download_file_name = generate_filename(selected_layout, TIMEZONE)

            st.text_area(
                f"Resultado formatado ({selected_layout}):",
                result_text,
                height=300,
                help="Este é o conteúdo do arquivo que será baixado."
            )

            st.download_button(
                label="⬇️ Baixar Resultado",
                data=result_text,
                file_name=download_file_name,
                mime="text/plain",
                use_container_width=True
            )
