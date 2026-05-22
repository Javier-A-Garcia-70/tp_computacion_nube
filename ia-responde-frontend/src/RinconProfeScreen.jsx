import { useState, useEffect } from "react";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

const COLORS = {
  bg:        "#EDE5D0",
  header:    "#DDD3B8",
  text:      "#1a140a",
  textMuted: "#8a7a60",
  card:      "#FDFAF4",
  accent:    "#5a3a1a",
  accentSoft:"#e8dcc8",
  border:    "#d4c9b0",
  danger:    "#8B2020",
};

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
  const [nivel, setNivel]     = useState("aula");
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  async function generar() {
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await fetch(`${API}/rincon-profe/resumen`, {
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

  return (
    <div>
      <Label>Nivel</Label>
      <Select
        value={nivel}
        onChange={setNivel}
        options={[
          { value: "aula",  label: "Para el aula" },
          { value: "casa",  label: "Para explicar en casa" },
        ]}
      />
      <ActionBtn onClick={generar} loading={loading}>Generar resumen</ActionBtn>
      {error && <div style={{ color: COLORS.danger, fontSize: 12, marginTop: 8 }}>{error}</div>}

      {result && nivel === "aula" && (
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

      {result && nivel === "casa" && (
        <Card>
          <Label>De qué trata</Label>
          <div style={{ fontSize: 13, color: COLORS.text, lineHeight: 1.6 }}>{result.resumen}</div>

          <Label>Preguntas para hacerle a tu hijo</Label>
          {result.preguntas?.map((p, i) => (
            <div key={i} style={{ fontSize: 13, color: COLORS.text, marginBottom: 6 }}>
              {i + 1}. {p}
            </div>
          ))}

          <Label>Datos curiosos</Label>
          {result.datos_curiosos?.map((d, i) => (
            <div key={i} style={{ fontSize: 13, color: COLORS.text, marginBottom: 4 }}>• {d}</div>
          ))}
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

export default function RinconProfeScreen({ onBack }) {
  const [seccion,  setSeccion]  = useState("resumen");
  const [textos, setTextos] = useState([{ id: "todos", label: "Todos los textos" }]);
  const [textoId,  setTextoId]  = useState("todos");

  useEffect(() => {
    fetch(`${API}/textos`)
      .then(r => r.json())
      .then(data => setTextos([{ id: "todos", label: "Todos los textos" }, ...data.textos]))
      .catch(() => {});
  }, []);

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "100%", background: COLORS.bg,
      fontFamily: "'Inter', sans-serif",
    }}>
      {/* Header */}
      <div style={{
        background: COLORS.header,
        padding: "14px 16px 10px",
        display: "flex", alignItems: "center", gap: 12,
        flexShrink: 0,
      }}>
        <button
          onClick={onBack}
          style={{
            background: "none", border: "none",
            cursor: "pointer", padding: 4,
            fontSize: 18, color: COLORS.text,
          }}
        >
          ←
        </button>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.text }}>
            Rincón del Profe
          </div>
          <div style={{ fontSize: 11, color: COLORS.textMuted }}>
            Herramientas para docentes y familias
          </div>
        </div>
      </div>

      {/* Selector de texto */}
      <div style={{ padding: "12px 16px 0", flexShrink: 0 }}>
        <Label>Texto seleccionado</Label>
        <Select
          value={textoId}
          onChange={setTextoId}
          options={textos.map(t => ({ value: t.id, label: t.label }))}
        />
      </div>

      {/* Tabs de sección */}
      <div style={{
        display: "flex",
        borderBottom: `1px solid ${COLORS.border}`,
        marginTop: 12,
        flexShrink: 0,
        background: COLORS.card,
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
