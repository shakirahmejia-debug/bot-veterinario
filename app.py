import json
import streamlit as st

st.set_page_config(page_title="Orientador de urgencias veterinarias", page_icon="🐾", layout="centered")

@st.cache_data
def load_kb():
    with open("knowledge_base.json", encoding="utf-8") as f:
        return json.load(f)

KB = load_kb()

st.title("🐾 Orientador de urgencias veterinarias")
st.caption("Herramienta de orientación para dueños de perros y gatos. No es diagnóstico ni consulta veterinaria.")
st.warning(KB["meta"]["disclaimer"])

if "result" not in st.session_state:
    st.session_state.result = None

if st.session_state.result is None:
    with st.form("triage_form"):
        st.subheader("1. Datos del paciente")
        col1, col2 = st.columns(2)
        with col1:
            species = st.selectbox("Especie *", KB["species"])
            weight = st.number_input("Peso aproximado (kg) *", min_value=0.1, max_value=100.0, step=0.1, value=5.0)
            age = st.number_input("Edad (años) *", min_value=0, max_value=30, step=1, value=3)
        with col2:
            sex = st.selectbox("Sexo *", ["macho", "hembra"])
            repro = st.selectbox("Estado reproductivo *", ["entero", "castrado", "gestante", "lactante", "no aplica"])

        st.subheader("2. Motivo y signos")
        complaint = st.selectbox(
            "Motivo principal *",
            list(KB["complaints"].keys()),
            format_func=lambda x: KB["complaints"][x]["label"],
        )
        sign_options = list(dict.fromkeys(KB["complaints"][complaint]["signs"] + KB["red_flags_always"]))
        signs = st.multiselect(
            "Seleccione los signos que observa *",
            sign_options,
            format_func=lambda x: KB["signs"][x]["label"],
        )

        submitted = st.form_submit_button("Evaluar orientación")

    if submitted:
        if not signs:
            st.error("Debe seleccionar al menos un signo.")
        else:
            urgency = "verde"
            for s in signs:
                if KB["signs"][s]["urgency"] == "rojo":
                    urgency = "rojo"
                    break
                if KB["signs"][s]["urgency"] == "amarillo" and urgency != "rojo":
                    urgency = "amarillo"

            if species == "gato" and "gato_orina" in signs:
                urgency = "rojo"

            differentials = KB["differentials"].get(complaint, []) if urgency != "rojo" else []
            exams = KB["exams"].get(complaint, []) if urgency != "rojo" else []

            st.session_state.result = {
                "species": species, "weight": weight, "age": age, "sex": sex, "repro": repro,
                "complaint": complaint, "signs": signs, "urgency": urgency,
                "differentials": differentials, "exams": exams,
                "while": KB["while_you_go"][urgency],
            }
            st.rerun()

if st.session_state.result is not None:
    r = st.session_state.result
    st.divider()
    st.subheader("Resultado de orientación")

    urgency_color = {"rojo": "🔴", "amarillo": "🟡", "verde": "🟢"}
    st.markdown(f"### {urgency_color[r['urgency']]} Nivel de urgencia: **{r['urgency'].upper()}**")
    st.info(f"**Acción recomendada:** {KB['actions'][r['urgency']]}")

    if r["urgency"] != "rojo":
        st.markdown("#### Posibles problemas compatibles (no es diagnóstico)")
        if r["differentials"]:
            for d in r["differentials"]:
                st.markdown(f"- {d['disease']} {d['source']}")
        else:
            st.markdown("- No hay información específica para este motivo en la base. Consulte a un veterinario.")

        st.markdown("#### Exámenes que el veterinario suele solicitar para estos signos")
        if r["exams"]:
            for e in r["exams"]:
                st.markdown(f"- {e['exam']} {e['source']}")
            st.caption("Recuerde: el veterinario decide cuáles son necesarios.")
        else:
            st.markdown("- No hay información específica para este motivo en la base. Consulte a un veterinario.")
    else:
        st.markdown("#### En un caso ROJO no se muestran posibles problemas ni exámenes: la prioridad es llegar a urgencias.")

    st.markdown("#### Mientras va al veterinario")
    st.markdown("**Qué hacer:**")
    for item in r["while"]["do"]:
        st.markdown(f"- ✅ {item}")
    st.markdown("**Qué NO hacer:**")
    for item in r["while"]["dont"]:
        st.markdown(f"- ❌ {item}")
    st.markdown("**Qué llevar:**")
    for item in r["while"]["bring"]:
        st.markdown(f"- 🎒 {item}")

    st.markdown("#### Resumen para el veterinario")
    summary = KB["summary_template"].format(
        species=r["species"], weight=r["weight"], age=r["age"], sex=r["sex"],
        repro=r["repro"], complaint=KB["complaints"][r["complaint"]]["label"],
        signs=", ".join(KB["signs"][s]["label"] for s in r["signs"]),
        urgency=r["urgency"],
        differentials="; ".join(d["disease"] for d in r["differentials"]) or "no aplica (urgencia)",
        exams="; ".join(e["exam"] for e in r["exams"]) or "no aplica (urgencia)",
    )
    st.code(summary, language="text")

    st.error(KB["meta"]["anti_charlatan"])
    st.warning(KB["meta"]["disclaimer"])

    if st.button("Nueva evaluación"):
        st.session_state.result = None
        st.rerun()