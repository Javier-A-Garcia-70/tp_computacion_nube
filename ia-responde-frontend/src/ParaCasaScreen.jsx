import { useState, useEffect } from "react";
import AppHeader from "./AppHeader";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

import T from "./theme";
const COLORS = T;

// ── UI helpers ────────────────────────────────────────────────────────────────

function Label({ children }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 700, color: COLORS.textMuted,
      textTransform: "uppercase", letterSpacing: ".05em",
      marginBottom: 4, marginTop: 12,
    }}>
      {children}
    </div>
  );
}

function Card({ children, style }) {
  return (
    <div style={{
      background: COLORS.card, borderRadius: 12,
      padding: 16, marginTop: 14,
      border: `1px solid ${COLORS.border}`,
      ...style,
    }}>
      {children}
    </div>
  );
}

function ActionBtn({ onClick, loading, children }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        width: "100%", padding: "12px",
        background: loading ? COLORS.border : COLORS.accent,
        color: "#fff", border: "none", borderRadius: 10,
        fontSize: 14, fontWeight: 600,
        cursor: loading ? "not-allowed" : "pointer",
        marginTop: 12, opacity: loading ? 0.7 : 1,
      }}
    >
      {loading ? "Generando..." : children}
    </button>
  );
}

function SectionTab({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1, padding: "10px 4px",
        fontSize: 11, fontWeight: active ? 700 : 400,
        color: active ? COLORS.accent : COLORS.textMuted,
        background: active ? COLORS.accentSoft : "transparent",
        border: "none",
        borderBottom: active ? `2px solid ${COLORS.accent}` : "2px solid transparent",
        cursor: "pointer", transition: "all .2s",
      }}
    >
      {children}
    </button>
  );
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        width: "100%", padding: "10px 12px",
        borderRadius: 8, border: `1px solid ${COLORS.border}`,
        background: COLORS.card, color: COLORS.text,
        fontSize: 13, marginTop: 4,
      }}
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function ErrorMsg({ msg }) {
  return msg ? (
    <div style={{ color: COLORS.danger, fontSize: 12, marginTop: 8 }}>{msg}</div>
  ) : null;
}

// ── Sección: De qué trata ─────────────────────────────────────────────────────

function SeccionDéQueTrata({ textoId }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/para-casa/de-que-trata`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_id: textoId }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <div style={{ fontSize: 13, color: COLORS.textMuted, marginTop: 8 }}>
        Un resumen claro y simple para entender el libro en 2 minutos.
      </div>
      <ActionBtn onClick={generar} loading={loading}>¿De qué trata?</ActionBtn>
      <ErrorMsg msg={error} />
      {result && (
        <Card>
          <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.accent, marginBottom: 8 }}>
            {result.titulo_informal}
          </div>
          <Label>De qué trata</Label>
          <div style={{ fontSize: 13, color: COLORS.text, lineHeight: 1.7 }}>{result.de_que_trata}</div>

          <Label>Personajes principales</Label>
          {result.personajes_principales?.map((p, i) => (
            <div key={i} style={{ fontSize: 13, color: COLORS.text, marginBottom: 6 }}>
              <strong>{p.nombre}:</strong> {p.quien_es}
            </div>
          ))}

          <Label>Cómo termina</Label>
          <div style={{ fontSize: 13, color: COLORS.text, lineHeight: 1.7, fontStyle: "italic" }}>
            {result.como_termina}
          </div>
        </Card>
      )}
    </div>
  );
}

// ── Sección: Preguntas para charlar ──────────────────────────────────────────

function SeccionPreguntas({ textoId }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/para-casa/preguntas-charla`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_id: textoId }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <div style={{ fontSize: 13, color: COLORS.textMuted, marginTop: 8 }}>
        4 preguntas para charlar con tu hijo sobre el libro, sin que parezca un examen.
      </div>
      <ActionBtn onClick={generar} loading={loading}>Generar preguntas</ActionBtn>
      <ErrorMsg msg={error} />
      {result && (
        <div>
          {result.preguntas?.map((p, i) => (
            <Card key={i}>
              <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.accent, marginBottom: 6 }}>
                {i + 1}. {p.pregunta}
              </div>
              <div style={{ fontSize: 12, color: COLORS.textMuted, lineHeight: 1.5 }}>
                {p.por_que_sirve}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Sección: Glosario ─────────────────────────────────────────────────────────

function SeccionGlosario({ textoId }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/para-casa/glosario`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_id: textoId }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <div style={{ fontSize: 13, color: COLORS.textMuted, marginTop: 8 }}>
        Palabras difíciles del libro explicadas de forma simple para ayudar a tu hijo.
      </div>
      <ActionBtn onClick={generar} loading={loading}>Ver glosario</ActionBtn>
      <ErrorMsg msg={error} />
      {result && (
        <Card>
          {result.palabras?.map((p, i) => (
            <div key={i} style={{
              marginBottom: 14,
              paddingBottom: 14,
              borderBottom: i < result.palabras.length - 1 ? `1px solid ${COLORS.border}` : "none",
            }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: COLORS.accent }}>{p.palabra}</div>
              <div style={{ fontSize: 13, color: COLORS.text, marginTop: 2, lineHeight: 1.5 }}>
                {p.definicion_simple}
              </div>
              <div style={{ fontSize: 12, color: COLORS.textMuted, marginTop: 4, fontStyle: "italic" }}>
                En el libro: {p.en_el_libro}
              </div>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

// ── Sección: Datos curiosos ───────────────────────────────────────────────────

function SeccionDatosCuriosos({ textoId }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/para-casa/datos-curiosos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_id: textoId }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <div style={{ fontSize: 13, color: COLORS.textMuted, marginTop: 8 }}>
        Datos del autor y la época para hacer la lectura más entretenida.
      </div>
      <ActionBtn onClick={generar} loading={loading}>Ver datos curiosos</ActionBtn>
      <ErrorMsg msg={error} />
      {result && (
        <div>
          {result.datos?.map((d, i) => (
            <Card key={i} style={{ borderLeft: `4px solid ${COLORS.accent}` }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: COLORS.accent, marginBottom: 6 }}>
                {d.titulo}
              </div>
              <div style={{ fontSize: 13, color: COLORS.text, lineHeight: 1.6 }}>{d.dato}</div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Pantalla principal ────────────────────────────────────────────────────────

const SECCIONES = [
  { id: "trata",    label: "De qué trata" },
  { id: "preguntas",label: "Preguntas" },
  { id: "glosario", label: "Glosario" },
  { id: "curiosos", label: "Curiosidades" },
];

export default function ParaCasaScreen({ user, onOpenMenu }) {
  const [seccion,  setSeccion]  = useState("trata");
  const [textoId,  setTextoId]  = useState("");
  const [textos,   setTextos]   = useState([]);

  useEffect(() => {
    fetch(`${API}/textos`)
      .then(r => r.json())
      .then(data => { setTextos(data.textos); })
      .catch(() => {});
  }, []);

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "100%", background: COLORS.bg,
      fontFamily: "'Inter', sans-serif",
    }}>
      <AppHeader title="Para Casa" user={user} onOpenMenu={onOpenMenu} />

      {/* Selector de texto */}
      <div style={{ padding: "12px 16px 0", flexShrink: 0 }}>
        <Label>Texto seleccionado</Label>
        <Select
          value={textoId}
          onChange={setTextoId}
          options={[{ value: "", label: "— Seleccioná un texto —" }, ...textos.map(t => ({ value: t.id, label: t.label }))]}
        />
      </div>

      {/* Tabs */}
      <div style={{
        display: "flex", borderBottom: `1px solid ${COLORS.border}`,
        marginTop: 12, flexShrink: 0, background: COLORS.card,
      }}>
        {SECCIONES.map(s => (
          <SectionTab key={s.id} active={seccion === s.id} onClick={() => setSeccion(s.id)}>
            {s.label}
          </SectionTab>
        ))}
      </div>

      {/* Contenido */}
      <div style={{
        flex: 1, overflowY: "auto",
        padding: "4px 16px 24px",
        scrollbarWidth: "none",
      }}>
        {seccion === "trata"     && <SeccionDéQueTrata  textoId={textoId} />}
        {seccion === "preguntas" && <SeccionPreguntas   textoId={textoId} />}
        {seccion === "glosario"  && <SeccionGlosario    textoId={textoId} />}
        {seccion === "curiosos"  && <SeccionDatosCuriosos textoId={textoId} />}
      </div>
    </div>
  );
}
