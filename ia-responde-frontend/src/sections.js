/**
 * Registro central de secciones de la app.
 * Para agregar una sección nueva: solo agregá un objeto acá.
 *
 * Campos:
 *   view      - string único que identifica la sección (usado en App state)
 *   label     - nombre que aparece en el menú y en el header
 *   icon      - emoji o string para el menú lateral
 *   component - import lazy o nombre del componente (se resuelve en App.jsx)
 */
const SECTIONS = [
  { view: "rincon", label: "Rincón del Profe", icon: "📚" },
  { view: "casa",   label: "Para Casa",        icon: "🏠" },
  { view: "browse", label: "Chat",             icon: "💬" },
];

export default SECTIONS;
