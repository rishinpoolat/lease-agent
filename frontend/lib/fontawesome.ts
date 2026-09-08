import { config } from "@fortawesome/fontawesome-svg-core";
import "@fortawesome/fontawesome-svg-core/styles.css";

// Import once at the app root (see app/layout.tsx). Without this, FA's
// default runtime CSS injection happens client-side only, causing a
// flash-of-unstyled-icons on every server-rendered page load -- a
// documented gotcha for FontAwesome + Next.js SSR.
config.autoAddCss = false;
