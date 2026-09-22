import re
from datetime import datetime

import streamlit as st
from supabase import Client, create_client

# --------------------------------------------------------------------------
# CONFIGURACION
# --------------------------------------------------------------------------
st.set_page_config(page_title="Recolector (Audios)", page_icon="", layout="centered")

TABLE_NAME = "AudioLinks"

CATEGORIA_OPCIONES = ["Informativos", "Culturales", "Musicales", "Otro"]
CATEGORIA_PLACEHOLDER = "Selecciona una categoría"

TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}$")  # formato m:ss o mm:ss


def tiempo_a_segundos(tiempo: str) -> int:
    """Convierte 'm:ss' o 'mm:ss' a segundos totales (int), para columnas int4."""
    minutos, segundos = tiempo.strip().split(":")
    return int(minutos) * 60 + int(segundos)


@st.cache_resource
def get_supabase_client():
    """Crea el cliente de Supabase usando credenciales en st.secrets."""
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)


supabase: Client | None = get_supabase_client()

# --------------------------------------------------------------------------
# ESTILOS (tema oscuro + acento morado, inspirado en el mockup)
# --------------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@200..700&display=swap" rel="stylesheet">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@200..700&display=swap');

    html, body, [class*="css"], .stApp, .stApp * {
        font-family: 'Oswald', sans-serif !important;
    }
    .stApp {
        background-color: #121014;
        color: #f5f5f7;
        --primary-color: #601BFA;
    }
    :root {
        --primary-color: #601BFA;
    }
    section.main > div {
        padding-top: 1.5rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"].st-key-panel_form,
    div[data-testid="stVerticalBlockBorderWrapper"].st-key-panel_list {
        background-color: #1c1a20;
        border: 1px solid #2e2b34 !important;
        border-radius: 16px !important;
        padding: 0.2rem 0.6rem 0.6rem 0.6rem;
    }
    .st-key-panel_form h3,
    .st-key-panel_list h3 {
        margin-top: 0.6rem;
        margin-bottom: 1rem;
        font-size: 1.05rem;
        color: #ffffff;
    }
    div[data-testid="stTextInput"] label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #cfcbd6;
    }
    div[data-testid="stTextInput"] input {
        background-color: #232028 !important;
        border: 1px solid #3a3742 !important;
        border-radius: 8px !important;
        color: #f5f5f7 !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #601BFA !important;
        border-radius: 8px !important;
        box-shadow: 0 0 0 1px #601BFA !important;
        outline: none !important;
    }
    div[data-testid="stTextInput"] > div:focus-within,
    div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stTextInputRootElement"]:focus-within {
        border-color: #601BFA !important;
        border-radius: 8px !important;
        box-shadow: 0 0 0 1px #601BFA !important;
        outline: none !important;
    }
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInputRootElement"] {
        border-radius: 8px !important;
        overflow: hidden;
    }
    div[data-testid="stTextInput"] *:focus,
    div[data-testid="stTextInput"] *:focus-visible {
        outline: none !important;
    }
    div[data-testid="stSelectbox"] label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #cfcbd6;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #232028 !important;
        border: 1px solid #3a3742 !important;
        border-radius: 8px !important;
        color: #f5f5f7 !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within > div {
        border-color: #601BFA !important;
        box-shadow: 0 0 0 1px #601BFA !important;
    }
    div[data-testid="stSelectbox"] svg {
        fill: #cfcbd6 !important;
    }
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #3a3742;
        background-color: #232028;
        color: #f5f5f7;
        font-weight: 600;
    }
    .stButton > button:hover {
        border-color: #601BFA;
        color: #601BFA;
    }
    .stButton > button:disabled {
        opacity: 0.4;
    }
    .entry-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: #232028;
        border: 1px solid #322f39;
        border-radius: 8px;
        padding: 0.55rem 0.9rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
        color: #601BFA;
    }
    .st-key-enviar_btn button {
        background-color: transparent;
        border: 1px solid #4ade80 !important;
        color: #4ade80;
        border-radius: 10px;
        padding: 0.5rem 1.6rem;
        font-weight: 700;
    }
    .st-key-enviar_btn button:hover {
        background-color: rgba(74, 222, 128, 0.1);
        border-color: #4ade80 !important;
        color: #4ade80 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Recolector (Audios)")

if supabase is None:
    st.warning(
        "No se encontraron credenciales de Supabase. Configura `SUPABASE_URL` y "
        "`SUPABASE_KEY` en `.streamlit/secrets.toml` para poder enviar datos.",
        icon="⚠️",
    )

# --------------------------------------------------------------------------
# ESTADO
# --------------------------------------------------------------------------
if "entries" not in st.session_state:
    st.session_state.entries = []  # lista de dicts pendientes de enviar
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
for key, default in [
    ("url_input", ""),
    ("titulo_input", ""),
    ("in_input", ""),
    ("out_input", ""),
    ("categoria_input", CATEGORIA_PLACEHOLDER),
]:
    st.session_state.setdefault(key, default)


def campos_completos() -> bool:
    textos = [
        st.session_state.url_input,
        st.session_state.titulo_input,
        st.session_state.in_input,
        st.session_state.out_input,
    ]
    categoria_ok = st.session_state.categoria_input in CATEGORIA_OPCIONES
    return all(t.strip() for t in textos) and categoria_ok


def formatos_validos() -> bool:
    return bool(
        TIME_PATTERN.match(st.session_state.in_input.strip())
        and TIME_PATTERN.match(st.session_state.out_input.strip())
    )


def limpiar_formulario():
    st.session_state.url_input = ""
    st.session_state.titulo_input = ""
    st.session_state.in_input = ""
    st.session_state.out_input = ""
    st.session_state.categoria_input = CATEGORIA_PLACEHOLDER
    st.session_state.edit_index = None


def agregar_o_actualizar_entrada():
    entry = {
        "url": st.session_state.url_input.strip(),
        "titulo": st.session_state.titulo_input.strip(),
        "in": st.session_state.in_input.strip(),
        "out": st.session_state.out_input.strip(),
        "categoria": st.session_state.categoria_input.strip(),
    }
    if st.session_state.edit_index is not None:
        st.session_state.entries[st.session_state.edit_index] = entry
    else:
        st.session_state.entries.append(entry)
    limpiar_formulario()


def cargar_para_edicion(i: int):
    entry = st.session_state.entries[i]
    st.session_state.edit_index = i
    st.session_state.url_input = entry["url"]
    st.session_state.titulo_input = entry["titulo"]
    st.session_state.in_input = entry["in"]
    st.session_state.out_input = entry["out"]
    st.session_state.categoria_input = entry["categoria"]


def eliminar_entrada(i: int):
    st.session_state.entries.pop(i)
    if st.session_state.edit_index == i:
        limpiar_formulario()


def enviar_a_supabase():
    if supabase is None:
        st.error("No se configuraron las credenciales de Supabase.")
        return
    if not st.session_state.entries:
        return
    ahora = datetime.now().isoformat(timespec="seconds")  # fecha y hora exacta del envío
    try:
        registros = [
            {
                **entry,
                "in": tiempo_a_segundos(entry["in"]),
                "out": tiempo_a_segundos(entry["out"]),
                "fecha": ahora,
            }
            for entry in st.session_state.entries
        ]
        supabase.table(TABLE_NAME).insert(registros).execute()
        st.session_state.enviado_ok = len(st.session_state.entries)
        st.session_state.entries = []
    except Exception as exc:  # noqa: BLE001
        st.session_state.enviado_error = str(exc)


# --------------------------------------------------------------------------
# PANEL 1: FORMULARIO DE INGRESO
# --------------------------------------------------------------------------
with st.container(border=True, key="panel_form"):
    st.markdown("### Ingresa los datos:" if st.session_state.edit_index is None else "### Editando registro:")

    st.text_input("URL:", key="url_input")
    st.text_input("TITULO:", key="titulo_input")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("IN:", key="in_input", placeholder="0:00")
    with c2:
        st.text_input("OUT:", key="out_input", placeholder="0:00")
    st.selectbox(
        "CATEGORIA:",
        options=[CATEGORIA_PLACEHOLDER] + CATEGORIA_OPCIONES,
        key="categoria_input",
    )

    campos_ok = campos_completos()
    if campos_ok and not formatos_validos():
        st.caption("⚠️ IN y OUT deben tener formato m:ss (ej. 1:23)")
        campos_ok = False

    label_boton = "Guardar cambios" if st.session_state.edit_index is not None else "Agregar a la lista"
    colA, colB = st.columns([1, 1])
    with colA:
        st.button(
            label_boton, on_click=agregar_o_actualizar_entrada, disabled=not campos_ok, use_container_width=True
        )
    with colB:
        if st.session_state.edit_index is not None:
            st.button("Cancelar edición", on_click=limpiar_formulario, use_container_width=True)

# --------------------------------------------------------------------------
# PANEL 2: LISTA DE AUDIOS PENDIENTES
# --------------------------------------------------------------------------
with st.container(border=True, key="panel_list"):
    st.markdown("### Lista de audios")

    if not st.session_state.entries:
        st.caption("Aún no hay registros agregados.")
    else:
        for i, entry in enumerate(st.session_state.entries):
            row_col, edit_col, del_col = st.columns([6, 1.3, 0.6])
            with row_col:
                st.markdown(
                    f'<div class="entry-row">'
                    f'{i + 1}. {entry["titulo"]}  IN:{entry["in"]}  OUT:{entry["out"]}'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with edit_col:
                st.button(
                    "Editar", key=f"edit_{i}", on_click=cargar_para_edicion, args=(i,), use_container_width=True
                )
            with del_col:
                st.button("🗑️", key=f"del_{i}", on_click=eliminar_entrada, args=(i,), use_container_width=True)

# --------------------------------------------------------------------------
# BOTON ENVIAR
# --------------------------------------------------------------------------
_, send_col = st.columns([3, 1])
with send_col:
    with st.container(key="enviar_btn"):
        st.button(
            "Enviar",
            on_click=enviar_a_supabase,
            disabled=(len(st.session_state.entries) == 0 or supabase is None),
            use_container_width=True,
        )

if st.session_state.get("enviado_ok"):
    st.success(f"Se enviaron {st.session_state.enviado_ok} registro(s) correctamente.")
    del st.session_state["enviado_ok"]
if st.session_state.get("enviado_error"):
    st.error(f"Error al enviar a Supabase: {st.session_state.enviado_error}")
    del st.session_state["enviado_error"]