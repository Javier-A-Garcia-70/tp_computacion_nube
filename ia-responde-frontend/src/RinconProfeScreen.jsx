import { useState, useEffect } from "react";
import AppHeader from "./AppHeader";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

import T from "./theme";
const COLORS = T;

// ── helpers UI ────────────────────────────────────────────────────────────────

function SectionBtn({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        padding: "10px 8px",
        fontSize: 12,
        fontWeight: active ? 700 : 400,
        color: active ? COLORS.accent : COLORS.textMuted,
        background: active ? COLORS.accentSoft : "transparent",
        border: "none",
        borderBottom: active ? `2px solid ${COLORS.accent}` : "2px solid transparent",
        cursor: "pointer",
        transition: "all .2s",
      }}
    >
      {children}
    </button>
  );
}

function ActionBtn({ onClick, loading, children }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        width: "100%",
        padding: "12px",
        background: loading ? COLORS.border : COLORS.accent,
        color: "#fff",
        border: "none",
        borderRadius: 10,
        fontSize: 14,
        fontWeight: 600,
        cursor: loading ? "not-allowed" : "pointer",
        marginTop: 12,
        opacity: loading ? 0.7 : 1,
      }}
    >
      {loading ? "Generando..." : children}
    </button>
  );
}

function Card({ children }) {
  return (
    <div style={{
      background: COLORS.card,
      borderRadius: 12,
      padding: 16,
      marginTop: 14,
      border: `1px solid ${COLORS.border}`,
    }}>
      {children}
    </div>
  );
}

function Label({ children }) {
  return (
    <div style={{
      fontSize: 11,
      fontWeight: 700,
      color: COLORS.textMuted,
      textTransform: "uppercase",
      letterSpacing: ".05em",
      marginBottom: 4,
      marginTop: 12,
    }}>
      {children}
    </div>
  );
}

function Tag({ children }) {
  return (
    <span style={{
      display: "inline-block",
      background: COLORS.accentSoft,
      color: COLORS.accent,
      borderRadius: 6,
      padding: "3px 10px",
      fontSize: 12,
      marginRight: 6,
      marginBottom: 6,
    }}>
      {children}
    </span>
  );
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      style={{
        width: "100%",
        padding: "10px 12px",
        borderRadius: 8,
        border: `1px solid ${COLORS.border}`,
        background: COLORS.card,
        color: COLORS.text,
        fontSize: 13,
        marginTop: 4,
      }}
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

// ── Sección Resumen ───────────────────────────────────────────────────────────

function SeccionResumen({ textoId }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/rincon-profe/resumen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_id: textoId, nivel: "aula" }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ fontSize: 13, color: COLORS.textMuted, marginTop: 8 }}>
        Análisis estructurado del texto para usar como base de clase: tipo de texto, época, temas, personajes, recursos literarios, valores y ejes de debate.
      </div>
      <ActionBtn onClick={generar} loading={loading}>Generar resumen</ActionBtn>
      {error && <div style={{ color: COLORS.danger, fontSize: 12, marginTop: 8 }}>{error}</div>}

      {result && (
        <Card>
          <Label>Tipo de texto</Label>
          <div style={{ fontSize: 13, color: COLORS.text }}>{result.tipo_texto}</div>

          <Label>Época y contexto</Label>
          <div style={{ fontSize: 13, color: COLORS.text }}>{result.epoca_contexto}</div>

          <Label>Temas centrales</Label>
          <div>{result.temas_centrales?.map((t, i) => <Tag key={i}>{t}</Tag>)}</div>

          <Label>Personajes</Label>
          {result.personajes?.map((p, i) => (
            <div key={i} style={{ fontSize: 13, color: COLORS.text, marginBottom: 4 }}>
              <strong>{p.nombre}:</strong> {p.descripcion}
            </div>
          ))}

          <Label>Recursos literarios</Label>
          <div>{result.recursos_literarios?.map((r, i) => <Tag key={i}>{r}</Tag>)}</div>

          <Label>Valores</Label>
          <div>{result.valores?.map((v, i) => <Tag key={i}>{v}</Tag>)}</div>

          <Label>Ejes de debate</Label>
          {result.ejes_debate?.map((e, i) => (
            <div key={i} style={{ fontSize: 13, color: COLORS.text, marginBottom: 4 }}>• {e}</div>
          ))}

          <Label>Nivel sugerido</Label>
          <div style={{ fontSize: 13, color: COLORS.text }}>{result.nivel_sugerido}</div>
        </Card>
      )}
    </div>
  );
}

// ── Sección Actividades ───────────────────────────────────────────────────────

function SeccionActividades({ textoId }) {
  const [nivel, setNivel]     = useState("primaria");
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/rincon-profe/actividades`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_id: textoId, nivel }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function ActividadCard({ act, tipo }) {
    return (
      <div style={{
        background: COLORS.accentSoft,
        borderRadius: 10,
        padding: 12,
        marginBottom: 10,
      }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: COLORS.accent, marginBottom: 4 }}>
          {act.nombre}
          <span style={{ fontWeight: 400, color: COLORS.textMuted, marginLeft: 8, fontSize: 11 }}>
            {act.tiempo_estimado}
          </span>
        </div>
        <div style={{ fontSize: 13, color: COLORS.text, lineHeight: 1.5 }}>{act.consigna}</div>
      </div>
    );
  }

  return (
    <div>
      <Label>Nivel escolar</Label>
      <Select
        value={nivel}
        onChange={setNivel}
        options={[
          { value: "primaria",   label: "Primaria" },
          { value: "secundaria", label: "Secundaria" },
        ]}
      />
      <ActionBtn onClick={generar} loading={loading}>Generar actividades</ActionBtn>
      {error && <div style={{ color: COLORS.danger, fontSize: 12, marginTop: 8 }}>{error}</div>}

      {result && (
        <Card>
          <Label>Actividades grupales</Label>
          {result.grupales?.map((a, i) => <ActividadCard key={i} act={a} />)}
          <Label>Actividades individuales de escritura</Label>
          {result.individuales?.map((a, i) => <ActividadCard key={i} act={a} />)}
        </Card>
      )}
    </div>
  );
}

// ── Sección Valores ───────────────────────────────────────────────────────────

function SeccionValores({ textoId }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/rincon-profe/valores`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_id: textoId }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ fontSize: 13, color: COLORS.textMuted, marginTop: 8 }}>
        Detecta valores y temas transversales presentes en el corpus.
      </div>
      <ActionBtn onClick={generar} loading={loading}>Analizar valores</ActionBtn>
      {error && <div style={{ color: COLORS.danger, fontSize: 12, marginTop: 8 }}>{error}</div>}

      {result && (
        <Card>
          <Label>Valores</Label>
          {result.valores?.map((v, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: COLORS.accent }}>{v.valor}</div>
              <div style={{ fontSize: 12, color: COLORS.textMuted, lineHeight: 1.5 }}>{v.contexto}</div>
            </div>
          ))}

          <Label>Temas transversales</Label>
          {result.temas_transversales?.map((t, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: COLORS.accent }}>{t.tema}</div>
              <div style={{ fontSize: 12, color: COLORS.textMuted, lineHeight: 1.5 }}>{t.descripcion}</div>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

// ── Sección Personajes ────────────────────────────────────────────────────────

function SeccionPersonajes({ textoId }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/rincon-profe/personajes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto_id: textoId }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div style={{ fontSize: 13, color: COLORS.textMuted, marginTop: 8 }}>
        Genera una ficha completa de cada personaje principal.
      </div>
      <ActionBtn onClick={generar} loading={loading}>Generar fichas</ActionBtn>
      {error && <div style={{ color: COLORS.danger, fontSize: 12, marginTop: 8 }}>{error}</div>}

      {result && result.personajes?.map((p, i) => (
        <Card key={i}>
          <div style={{ fontSize: 15, fontWeight: 700, color: COLORS.accent, marginBottom: 8 }}>
            {p.nombre}
          </div>
          <Label>Características físicas</Label>
          <div style={{ fontSize: 13, color: COLORS.text }}>{p.caracteristicas_fisicas}</div>
          <Label>Características psicológicas</Label>
          <div style={{ fontSize: 13, color: COLORS.text }}>{p.caracteristicas_psicologicas}</div>
          <Label>Rol en la historia</Label>
          <div style={{ fontSize: 13, color: COLORS.text }}>{p.rol_en_historia}</div>
          <Label>Frase / momento representativo</Label>
          <div style={{ fontSize: 13, color: COLORS.text, fontStyle: "italic" }}>
            "{p.frase_o_momento_representativo}"
          </div>
        </Card>
      ))}
    </div>
  );
}

// ── Pantalla principal ────────────────────────────────────────────────────────

const SECCIONES = [
  { id: "resumen",    label: "Resumen" },
  { id: "actividades",label: "Actividades" },
  { id: "valores",    label: "Valores" },
  { id: "personajes", label: "Personajes" },
];

export default function RinconProfeScreen({ user, onOpenMenu }) {
  const [seccion,  setSeccion]  = useState("resumen");
  const [textos, setTextos] = useState([]);
  const [textoId,  setTextoId]  = useState("");

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
      <AppHeader title="Rincón del Profe" user={user} onOpenMenu={onOpenMenu} />

      {/* Descripción */}
      <div style={{ padding: "14px 16px 0", flexShrink: 0 }}>
        <p style={{ margin: 0, fontSize: 13, color: COLORS.textMuted, lineHeight: 1.6 }}>
          Herramientas pensadas para el aula: analizá un texto, generá actividades, detectá valores o consultá las fichas de personajes. Seleccioná el texto que querés trabajar en el campo de abajo, o si querés sumar un libro nuevo,{" "}
          <span style={{ color: COLORS.accent, fontWeight: 600 }}>agregalo acá</span>.
        </p>
      </div>

      {/* Selector de texto */}
      <div style={{ padding: "12px 16px 0", flexShrink: 0 }}>
        <Label>Texto seleccionado</Label>
        <Select
          value={textoId}
          onChange={setTextoId}
          options={[{ value: "", label: "— Seleccioná un texto —" }, ...textos.map(t => ({ value: t.id, label: t.label }))]}
        />
      </div>

      {/* Tabs de sección */}
      <div style={{
        display: "flex",
        borderBottom: `1px solid ${COLORS.border}`,
        flexShrink: 0,
        background: COLORS.card,
        margin: "12px 16px 0",
        borderRadius: 8,
      }}>
        {SECCIONES.map(s => (
          <SectionBtn
            key={s.id}
            active={seccion === s.id}
            onClick={() => setSeccion(s.id)}
          >
            {s.label}
          </SectionBtn>
        ))}
      </div>

      {/* Contenido scrolleable */}
      <div style={{
        flex: 1, overflowY: "auto",
        padding: "4px 16px 24px",
        scrollbarWidth: "none",
      }}>
        {seccion === "resumen"     && <SeccionResumen     textoId={textoId} />}
        {seccion === "actividades" && <SeccionActividades textoId={textoId} />}
        {seccion === "valores"     && <SeccionValores     textoId={textoId} />}
        {seccion === "personajes"  && <SeccionPersonajes  textoId={textoId} />}
      </div>
    </div>
  );
}
