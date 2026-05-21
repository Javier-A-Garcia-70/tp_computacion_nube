import { GoogleLogin } from "@react-oauth/google";
import { jwtDecode } from "jwt-decode";

const COLORS = {
  bg:       "#BFB090",   // beige oscuro (más profundo que el header #DDD3B8)
  card:     "#FDFAF4",
  title:    "#1a140a",
  subtitle: "#8a7a60",
  divider:  "#E0D8C8",
};

export default function LoginScreen({ onLogin }) {
  function handleSuccess(credentialResponse) {
    try {
      const decoded = jwtDecode(credentialResponse.credential);
      onLogin({
        name:       decoded.name,
        email:      decoded.email,
        picture:    decoded.picture,
        credential: credentialResponse.credential,
      });
    } catch {
      console.error("Error decodificando credencial Google");
    }
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        background: COLORS.bg,
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <div
        style={{
          background:    COLORS.card,
          borderRadius:  24,
          padding:       "48px 40px",
          display:       "flex",
          flexDirection: "column",
          alignItems:    "center",
          gap:           20,
          boxShadow:     "0 12px 40px rgba(0,0,0,.18)",
          width:         300,
        }}
      >
        {/* Icono */}
        <div style={{ fontSize: 48, lineHeight: 1 }}>🔍</div>

        {/* Título */}
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              fontSize:   22,
              fontWeight: 700,
              color:      COLORS.title,
              letterSpacing: "-0.3px",
            }}
          >
            LoreChat
          </div>
          <div
            style={{
              fontSize:   12,
              color:      COLORS.subtitle,
              marginTop:  5,
              lineHeight: 1.4,
            }}
          >
            Conversaciones con personajes de la literatura
          </div>
        </div>

        {/* Separador */}
        <div
          style={{
            width:      "100%",
            borderTop:  `1px solid ${COLORS.divider}`,
            margin:     "4px 0",
          }}
        />

        {/* Botón Google */}
        <GoogleLogin
          onSuccess={handleSuccess}
          onError={() => console.error("Google login fallido")}
          text="signin_with"
          locale="es"
          shape="rectangular"
          size="large"
          width="240"
          theme="outline"
        />

        <div
          style={{
            fontSize:  10,
            color:     COLORS.subtitle,
            textAlign: "center",
            lineHeight: 1.5,
          }}
        >
          Al continuar aceptás los términos de uso del servicio.
        </div>
      </div>
    </div>
  );
}
