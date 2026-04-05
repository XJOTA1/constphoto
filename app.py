import streamlit as st
from PIL import Image
import os
import zipfile
import io
import pytesseract
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Escáner de Constancias", 
    page_icon="📄", 
    layout="centered"
)

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
    /* Estilo para los botones */
    div.stButton > button:first-child {
        border-radius: 10px;
        font-weight: bold;
    }
    
    /* Forzar que la cámara se vea más grande en celulares */
    [data-testid="stCameraInput"] {
        width: 100% !important;
    }
    
    [data-testid="stCameraInput"] video {
        width: 100% !important;
        height: auto !important;
        max-height: 70vh !important; /* Evita que ocupe más del 70% del alto de la pantalla */
        border-radius: 10px; /* Le da un borde redondeado más estético */
    }
    
    /* Achicar un poco los márgenes laterales en celulares para ganar espacio */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Crear directorio para guardar temporalmente los escaneos si no existe
SAVE_DIR = "constancias_guardadas"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# --- ENCABEZADO ---
st.title("📸 Escáner Inteligente de Constancias")
st.write("Tomá una foto del papel. El sistema intentará detectar el Nombre y Apellido automáticamente.")

# --- 1. CÁMARA ---
foto = st.camera_input("Escanear documento")

if foto is not None:
    # Cargar la imagen en memoria
    image = Image.open(foto)
    
    # --- 2. OCR: EXTRAER TEXTO ---
    with st.spinner("Analizando documento..."):
        # Extrae el texto de la imagen.
        texto_extraido = pytesseract.image_to_string(image, lang='spa')
    
    # --- 3. BUSCAR LA FRASE EXACTA ---
    # Busca la frase y captura todo lo que haya después de los dos puntos hasta que termine el renglón
    match_datos = re.search(r'NOMBRE Y APELLIDO DEL COLABORADOR[:\s]*([^\n]+)', texto_extraido, re.IGNORECASE)
    
    # Si encuentra el texto, lo limpia de espacios en blanco al principio o al final
    nombre_detectado = match_datos.group(1).strip() if match_datos else ""

    if not nombre_detectado:
        st.warning("⚠️ No se pudo detectar el nombre automáticamente. Por favor, ingresalo a mano.")
    else:
        st.success("✅ ¡Datos detectados!")

    # --- 4. FORMULARIO DE CONFIRMACIÓN ---
    st.write("Verificá que el dato sea correcto antes de guardar:")
    
    # Campo de texto precompletado con lo que encontró el OCR
    nombre_completo = st.text_input("Nombre y Apellido del Colaborador", value=nombre_detectado).strip()

    # Botón explícito para guardar
    if st.button("Guardar Constancia PDF"):
        if not nombre_completo:
            st.error("Falta completar el Nombre y Apellido.")
        else:
            # Convertir a RGB por si la imagen tiene canal Alfa (transparencia que PDF no soporta)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # Limpiamos el nombre completo para que sirva como nombre de archivo sin errores
            nombre_limpio = nombre_completo.replace(" ", "_").lower()
            filename = f"{nombre_limpio}_constancia.pdf"
            filepath = os.path.join(SAVE_DIR, filename)
            
            # Guardar como PDF
            image.save(filepath, "PDF", resolution=100.0)
            st.success(f"✅ ¡Excelente! Documento guardado como: **{filename}**")

st.divider()

# --- SECCIÓN DE DESCARGAS ---
st.subheader("⬇️ Archivos Guardados")

# Leer archivos disponibles en la carpeta
archivos_guardados = [f for f in os.listdir(SAVE_DIR) if f.endswith('.pdf')]

if archivos_guardados:
    # 1. Opción: Descargar TODOS en un ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for f in archivos_guardados:
            zip_file.write(os.path.join(SAVE_DIR, f), f)
    
    st.download_button(
        label="📦 Descargar la totalidad de archivos (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="todas_las_constancias.zip",
        mime="application/zip",
        type="primary" # Lo resalta estéticamente
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("**O descargar de forma específica:**")
    
    # 2. Opción: Descargar uno específico al costado de cada uno
    for f in archivos_guardados:
        col_nombre, col_boton = st.columns([3, 1])
        with col_nombre:
            st.markdown(f"📄 `{f}`")
        with col_boton:
            with open(os.path.join(SAVE_DIR, f), "rb") as pdf_file:
                st.download_button(
                    label="Descargar",
                    data=pdf_file,
                    file_name=f,
                    mime="application/pdf",
                    key=f  # Clave única para que Streamlit no se confunda de botón
                )
else:
    st.info("Aún no hay constancias escaneadas en el sistema.")
