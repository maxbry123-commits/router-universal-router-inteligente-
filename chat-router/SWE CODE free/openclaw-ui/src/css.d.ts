// El scaffold oficial (`openclaw plugins init --type feature`, TypeScript 7.0.2) importa ./control-ui.css y tsc lo rechaza (TS2882) sin esta declaracion.
declare module "*.css";
