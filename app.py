import json
import streamlit as st
import difflib

st.set_page_config(page_title="Orientador de urgencias veterinarias", page_icon="🐾", layout="centered")

@st.cache_data
def load_kb():
    with open("knowledge_base.json", encoding="utf-8") as f:
        return json.load(f)

KB = load_kb()

# Diccionario de palabras clave que la gente usa comunmente
SYNONYMS = {
    "rasca": "prurito_intenso", "rascando": "prurito_intenso", "comezon": "prurito_intenso", "comezón": "prurito_intenso",
    "pelo": "alopecia", "pelado": "alopecia", "calvo": "alopecia",
    "vomita": "vomito_persistente", "vomito": "vomito_persistente", "vómito": "vomito_persistente",
    "diarrea": "diarrea_sangre", "popo": "diarrea_sangre", "caca": "diarrea_sangre",
    "cojea": "cojera_repentina", "pata": "cojera_repentina", "renquea": "cojera_repentina",
    "no come": "decaimiento", "no quiere comer": "decaimiento", "decaido": "decaimiento", "decaído": "decaimiento", "triste": "decaimiento",
    "respira": "disnea", "ahoga": "disnea", "asfixia": "disnea",
    "tos": "tos", "tose": "tos",
    "orina": "dificultad_orinar", "pipi": "dificultad_orinar", "hace pipi": "dificultad_orinar",
    "sangre": "sangrado", "sangra": "sangrado", "hemorragia": "sangrado", "herida": "sangrado",
    "convulsion": "convulsion", "ataque": "convulsion", "temblor": "convulsion",
    "desmaya": "colapso", "desmayo": "colapso", "no se levanta": "colapso",
    "caliente": "fiebre", "fiebre": "fiebre",
    "agua": "sed_excesiva", "sed": "sed_excesiva",
    "amarillo": "ictericia", "ojos amarillos": "ictericia",
    "veneno": "intoxicacion", "toxica": "intoxicacion", "tóxico": "intoxicacion",
    "calor": "golpe_calor", "insolación": "golpe_calor"
}

def extract_symptoms(user_text):
    if not user_text:
        return []
    
    user_text = user_text.lower()
    matched = set()
    
    # 1. Buscar coincidencias exactas de las palabras populares o médicas en el texto
    for key, data in KB["signs"].items():
        if data["popular"].lower() in user_text or data["label"].lower() in user_text:
            matched.add(key)
            
    # 2. Buscar por palabras individuales (por si escriben "rascándose" en vez de "rasca")
    words = user_text.split()
    searchable_terms = {}
    for key, data in KB["signs"].items():
        searchable_terms[data["popular"].lower()] = key
        searchable_terms[data["label"].lower()] = key
        
    for word in words:
        if len(word) > 3:
            # difflib busca palabras similares (ej: "rascando" se parece a "rasca")
            matches = difflib.get_close_matches(word, searchable_terms.keys(), n=1, cutoff=0.65)
            if matches:
                matched.add(searchable_terms[matches[0]])
                
    # 3. Buscar sinónimos comunes
    for syn, key in SYNONYMS.items():
        if syn in user_text:
            matched.add(key)

    return list(matched)

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
        
        # El motivo sigue siendo un menú para saber qué exámenes sugerir
        complaint = st.selectbox(
            "Zona principal afectada *",
            list(KB["complaints"].keys()),
            format_func=lambda x: KB["complaints"][x]["label"],
        )
        
        # AQUI ESTA EL CAMBIO: Ahora es un cuadro de texto libre
        user_symptoms_text = st.text_area(
            "Describa con sus palabras lo que le pasa a su mascota *",
            placeholder="Ejemplo: mi perro se rasca mucho, tiene el pelo pelado y le duele la barriga...",
            height=100
        )

        submitted = st.form_submit_button("Evaluar orientación")

    if submitted:
        if not user_symptoms_text.strip():
            st.error("Por favor, escriba los síntomas que observa.")
        else:
            # Extraemos los síntomas del texto
            signs = extract_symptoms(user_symptoms_text)
            
            if not signs:
                st.error("No pudimos entender los síntomas exactos. Intente usar palabras más simples (ej: 'rasca', 'vomita', 'cojea', 'sangra').")
            else:
                # Mostramos qué entendió el sistema para que el usuario confíe
                st.info(f"El sistema detectó los siguientes síntomas: {', '.join([KB['signs'][s]['popular'] for s in signs])}")

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
