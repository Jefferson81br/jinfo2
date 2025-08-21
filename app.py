import streamlit as st
from datetime import datetime
import pytz

st.title("Processador de Dados de Códigos de Barras Para Alpha7 V1.2")
st.markdown("---")

# Campo de seleção para o layout
selected_layout = st.selectbox(
    "Escolha o Layout de Saída:",
    ("Layout Alpha7", "Layout 2", "Layout 3", "Layout 4")
)

uploaded_file = st.file_uploader("Envie um arquivo .txt (formato: CODIGO,QUANTIDADE por linha)", type="txt")

if uploaded_file:
    lines = uploaded_file.read().decode("utf-8").splitlines()
    processed_data = []
    errors = []

    # Define o fuso horário para UTC-3
    brazil_tz = pytz.timezone('America/Sao_Paulo')

    for line_num, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line:
            continue

        parts = stripped_line.split(',')
        if len(parts) == 2:
            code = parts[0].strip()
            try:
                quantity = int(parts[1].strip())
                processed_data.append({"code": code, "quantity": quantity})
            except ValueError:
                errors.append(f"Linha {line_num + 1}: Quantidade '{parts[1].strip()}' não é um número válido.")
        else:
            errors.append(f"Linha {line_num + 1}: Formato inválido. Esperado 'CODIGO,QUANTIDADE'.")

    if errors:
        st.error("Foram encontrados os seguintes erros no arquivo:")
        for error in errors:
            st.write(f"- {error}")
        st.warning("Por favor, corrija o arquivo e tente novamente.")
    elif not processed_data:
        st.warning("O arquivo enviado não contém dados válidos no formato 'CODIGO,QUANTIDADE'.")
    else:
        # Ordena os dados pela quantidade (do menor para o maior)
        sorted_data = sorted(processed_data, key=lambda x: x['quantity'])

        # Obtém a data e hora atual no fuso horário UTC-3
        now_utc_minus_3 = datetime.now(brazil_tz)
        
        # String da data (para conteúdo e nome do arquivo)
        date_str = now_utc_minus_3.strftime("%Y%m%d")
        
        # String da hora COMPLETA (para o conteúdo do arquivo: HHMMSS)
        time_str_content = now_utc_minus_3.strftime("%H%M%S")
        
        # String da hora RESUMIDA (para o nome do arquivo: HHMM)
        time_str_filename = now_utc_minus_3.strftime("%H%M") 

        result_lines = []

        # Lógica para formatação de acordo com o layout selecionado
        for item in sorted_data:
            line = f"{date_str},{time_str_content},{item['code']},{item['quantity']}"
            
            if selected_layout == "Layout 2":
                line += ",Layout2"
            elif selected_layout == "Layout 3":
                line += ",Layout3"
            elif selected_layout == "Layout 4":
                line += ",Layout4"

            result_lines.append(line)

        result_text = "\n".join(result_lines)

        st.success("Dados processados com sucesso!")
        st.text_area("Resultado formatado:", result_text, height=300)

        # Constrói o nome do arquivo dinamicamente com o layout escolhido
        layout_short = selected_layout.replace(" ", "")
        download_file_name = f"Dados_formatados_{layout_short}_{date_str}_{time_str_filename}.txt"

        st.download_button(
            label="Baixar resultado formatado",
            data=result_text,
            file_name=download_file_name,
            mime="text/plain"
        )


