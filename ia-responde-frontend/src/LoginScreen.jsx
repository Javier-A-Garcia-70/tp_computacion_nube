import { GoogleLogin } from "@react-oauth/google";
import { jwtDecode } from "jwt-decode";

const COLORS = {
  bg:      "#D2E4F0",
  card:    "#FDFCFB",
  subtitle:"#98B6C8",
  divider: "#C8D8E8",
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
        display:        "flex",
        flexDirection:  "column",
        alignItems:     "center",
        justifyContent: "center",
        height:         "100%",
        background:     COLORS.bg,
        fontFamily:     "'Inter', sans-serif",
        gap:            40,
        padding:        "0 32px",
      }}
    >
      {/* Logo suelto, sin card */}
      <img
        src="/logo_rincon_libro.png"
        alt="El Rincón del Libro"
        style={{
          width:     220,
          maxWidth:  "70%",
          objectFit: "contain",
        }}
      />

      {/* Card de login */}
      <div
        style={{
          background:    COLORS.card,
          borderRadius:  20,
          padding:       "36px 32px",
          display:       "flex",
          flexDirection: "column",
          alignItems:    "center",
          gap:           16,
          boxShadow:     "0 8px 32px rgba(0,0,0,.12)",
          width:         "100%",
          maxWidth:      320,
        }}
      >
        <div
          style={{
            fontSize:      11,
            fontWeight:    600,
            letterSpacing: "0.08em",
            color:         COLORS.subtitle,
            textTransform: "uppercase",
            marginBottom:  4,
          }}
        >
          Acceso a la plataforma
        </div>

        <div
          style={{
            width:     "100%",
            borderTop: `1px solid ${COLORS.divider}`,
          }}
        />

        <GoogleLogin
          onSuccess={handleSuccess}
          onError={() => console.error("Google login fallido")}
          text="signin_with"
          locale="es"
          shape="rectangular"
          size="large"
          width="256"
          theme="outline"
        />

        <div
          style={{
            fontSize:   10,
            color:      COLORS.subtitle,
            textAlign:  "center",
            lineHeight: 1.5,
          }}
        >
          Al continuar aceptás los términos de uso del servicio.
        </div>
      </div>
    </div>
  );
}
