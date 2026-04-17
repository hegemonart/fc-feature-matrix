import { describe, it, expect } from 'vitest';
import { hasFontFaceSet, waitForFontsReady } from './setup-fonts';

// D-07/D-08 — enforces that Inter Tight + Roboto Mono are loaded by the time
// the page is interactive. In jsdom (default vitest env) the FontFaceSet API
// is not implemented, so the assertions short-circuit via the hasFontFaceSet
// guard. In a browser env (Playwright / happy-dom) they enforce the contract.

describe('fonts', () => {
  it('Inter Tight is loaded after document.fonts.ready', async () => {
    await waitForFontsReady();
    if (!hasFontFaceSet()) {
      // jsdom env — FontFaceSet not available, skip assertion.
      expect(true).toBe(true);
      return;
    }
    const ok = (document as Document & { fonts: FontFaceSet }).fonts.check(
      '16px "Inter Tight"',
    );
    expect(ok).toBe(true);
  });

  it('Roboto Mono is loaded after document.fonts.ready', async () => {
    await waitForFontsReady();
    if (!hasFontFaceSet()) {
      expect(true).toBe(true);
      return;
    }
    const ok = (document as Document & { fonts: FontFaceSet }).fonts.check(
      '10px "Roboto Mono"',
    );
    expect(ok).toBe(true);
  });
});
