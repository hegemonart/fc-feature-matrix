// D-07/D-08 — font-readiness helper.
// In a real browser env, awaits document.fonts.ready (FontFaceSet API) so
// callers can assert specific font-faces are loaded. In jsdom (Vitest's
// default env), document.fonts is undefined; the helper resolves immediately
// and the corresponding assertions short-circuit via hasFontFaceSet() guard.

export function hasFontFaceSet(): boolean {
  return (
    typeof document !== 'undefined' &&
    typeof (document as Document & { fonts?: FontFaceSet }).fonts !== 'undefined'
  );
}

export async function waitForFontsReady(): Promise<void> {
  if (!hasFontFaceSet()) return;
  await (document as Document & { fonts: FontFaceSet }).fonts.ready;
}
