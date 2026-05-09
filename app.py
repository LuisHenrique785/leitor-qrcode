import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
from pyzbar.pyzbar import decode
from io import BytesIO
import datetime

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Leitor de QR Code",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Estilo visual ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stApp { max-width: 900px; margin: 0 auto; }

    .header-box {
        background: linear-gradient(135deg, #FFE600 0%, #FFCC00 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .header-box h1 {
        color: #1a1a2e;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
    }
    .header-box p {
        color: #444;
        margin: 4px 0 0 0;
        font-size: 0.95rem;
    }

    .result-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    .stat-row {
        display: flex;
        gap: 16px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .stat-box {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 14px 20px;
        flex: 1;
        min-width: 120px;
        text-align: center;
    }
    .stat-box .num {
        font-size: 2rem;
        font-weight: 800;
        color: #2c5ff6;
    }
    .stat-box .label {
        font-size: 0.8rem;
        color: #666;
        margin-top: 4px;
    }
    .stButton > button {
        background: #FFE600;
        color: #1a1a2e;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 12px 32px;
        font-size: 1rem;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #FFCC00;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255,200,0,0.4);
    }
    .stDownloadButton > button {
        background: #2c5ff6 !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 32px !important;
        width: 100% !important;
    }
    .upload-hint {
        font-size: 0.85rem;
        color: #888;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
    <div style="font-size:3rem;">📦</div>
    <div>
        <h1>Leitor de QR Code em PDFs</h1>
        <p>Faça upload das sacas em PDF · Extraia os QR codes · Baixe o Excel</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Upload ────────────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Selecione os arquivos PDF",
    type="pdf",
    accept_multiple_files=True,
    label_visibility="visible",
)

if uploaded_files:
    st.markdown(f'<p class="upload-hint">📄 {len(uploaded_files)} arquivo(s) selecionado(s)</p>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Processamento ─────────────────────────────────────────────────────────────
if uploaded_files and st.button("🔍  Ler QR Codes agora"):

    dados_finais = []
    erros = []

    progress_bar = st.progress(0, text="Iniciando processamento...")
    status_text = st.empty()

    for idx, arquivo in enumerate(uploaded_files):
        pct = int((idx / len(uploaded_files)) * 100)
        progress_bar.progress(pct, text=f"Processando {idx+1}/{len(uploaded_files)}: {arquivo.name}")
        status_text.caption(f"Convertendo páginas...")

        try:
            pdf_bytes = arquivo.read()
            paginas = convert_from_bytes(pdf_bytes, dpi=300)

            qr_encontrados_neste_pdf = 0
            for i, pagina in enumerate(paginas):
                codigos = decode(pagina)
                for obj in codigos:
                    try:
                        conteudo = obj.data.decode("utf-8")
                    except Exception:
                        conteudo = obj.data.decode("latin-1", errors="replace")

                    # Equivalente à fórmula =ESQUERDA(DIREITA(C;6);4)
                    codigo = conteudo[-6:-2] if len(conteudo) >= 6 else conteudo

                    dados_finais.append({
                        "Arquivo": arquivo.name,
                        "Página": i + 1,
                        "Conteúdo QR Code": conteudo,
                        "Código": codigo,
                    })
                    qr_encontrados_neste_pdf += 1

            if qr_encontrados_neste_pdf == 0:
                erros.append(f"⚠️ Nenhum QR code detectado em: **{arquivo.name}**")

        except Exception as e:
            erros.append(f"❌ Erro ao processar **{arquivo.name}**: {e}")

    progress_bar.progress(100, text="Concluído!")
    status_text.empty()

    # ── Resultado ─────────────────────────────────────────────────────────────
    if erros:
        for msg in erros:
            st.warning(msg)

    if dados_finais:
        df = pd.DataFrame(dados_finais)

        n_qr     = len(df)
        n_pdfs   = df["Arquivo"].nunique()
        n_paginas = df["Página"].nunique()

        st.markdown(f"""
        <div class="result-card">
            <div class="stat-row">
                <div class="stat-box">
                    <div class="num">{n_qr}</div>
                    <div class="label">QR Codes lidos</div>
                </div>
                <div class="stat-box">
                    <div class="num">{n_pdfs}</div>
                    <div class="label">Arquivos</div>
                </div>
                <div class="stat-box">
                    <div class="num">{n_paginas}</div>
                    <div class="label">Páginas com QR</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(df, use_container_width=True, height=400)

        # ── Exportar Excel ────────────────────────────────────────────────────
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="QR Codes")
        buffer.seek(0)

        hoje = datetime.date.today().strftime("%Y-%m-%d")
        nome_arquivo = f"qrcodes_{hoje}.xlsx"

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥  Baixar Excel com todos os QR Codes",
            data=buffer,
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.success(f"Arquivo **{nome_arquivo}** pronto para download e compartilhamento!")

    else:
        st.error("Nenhum QR code foi encontrado nos arquivos enviados. Verifique a qualidade dos PDFs.")

elif not uploaded_files:
    st.info("👆 Selecione um ou mais arquivos PDF acima para começar.")
