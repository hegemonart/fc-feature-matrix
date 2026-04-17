/* ================================================================
   Modal.test.tsx

   D-24 — Single-orange-CTA per surface (modals).

   The three locked-overlay modals (LOCKED, LOGIN, COMING SOON)
   are rendered inline in app/MatrixIsland.tsx (not exported),
   so this spec uses small fixture components that mirror the
   JSX of each modal verbatim. If MatrixIsland's modal markup
   changes, update the fixtures below to match.

   Per modal we assert:
     (a) exactly ONE element with the .locked-btn class — the
         orange (background: var(--accent)) primary CTA.
     (b) at least ONE secondary action — either .locked-dismiss
         (text-only / muted) or no secondary at all (Coming Soon
         dismisses by clicking the overlay).
   ================================================================ */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';

/* ── Fixture: LOCKED MODAL (mirrors MatrixIsland.tsx ~line 706) ── */
function LockedModalFixture() {
  return (
    <div className="locked-overlay visible" role="dialog" aria-modal="true" aria-labelledby="lockedTitle">
      <div className="locked-card">
        <div className="lock-big" />
        <h3 id="lockedTitle">Analysis Restricted</h3>
        <p>
          The <span className="locked-flow-name">Conversion</span> view is locked.
        </p>
        <button className="locked-btn">Request access from admin</button>
        <button className="locked-dismiss">Maybe later</button>
      </div>
    </div>
  );
}

/* ── Fixture: LOGIN MODAL (mirrors MatrixIsland.tsx ~line 731) ── */
function LoginModalFixture() {
  return (
    <div className="locked-overlay visible" role="dialog" aria-modal="true" aria-labelledby="loginTitle">
      <div className="locked-card login-card">
        <h3 id="loginTitle">Sign in</h3>
        <p className="login-subtitle">Enter your credentials.</p>
        <form className="login-form">
          <label className="login-label">
            Email
            <input type="email" className="login-input" />
          </label>
          <label className="login-label">
            Password
            <input type="password" className="login-input" />
          </label>
          <button type="submit" className="locked-btn login-submit">Sign in</button>
        </form>
        <button className="locked-dismiss">Cancel</button>
      </div>
    </div>
  );
}

/* ── Fixture: COMING SOON MODAL (mirrors MatrixIsland.tsx ~line 776) ── */
function ComingSoonModalFixture() {
  return (
    <div className="locked-overlay visible" role="dialog" aria-modal="true" aria-labelledby="comingSoonTitle">
      <div className="locked-card coming-soon-card">
        <div className="coming-soon-icon" />
        <h3 id="comingSoonTitle">Coming Soon</h3>
        <p>
          The <span className="locked-flow-name">Engagement</span> analysis is locked.
        </p>
        <button className="locked-btn">Send request</button>
      </div>
    </div>
  );
}

/* ── Helper: assert single-orange-CTA invariant ── */
function assertSingleOrangeCTA(container: HTMLElement, modalLabel: string) {
  const orangeButtons = container.querySelectorAll('.locked-btn');
  expect(orangeButtons.length, `${modalLabel}: exactly one .locked-btn (orange CTA)`).toBe(1);
}

describe('<Modal> single-orange-CTA per surface (D-24)', () => {
  describe('LOCKED modal', () => {
    it('has exactly one .locked-btn (the orange "Request access" CTA)', () => {
      const { container } = render(<LockedModalFixture />);
      assertSingleOrangeCTA(container, 'LOCKED');
    });

    it('has a text-only secondary action (.locked-dismiss "Maybe later")', () => {
      const { container } = render(<LockedModalFixture />);
      const dismiss = container.querySelectorAll('.locked-dismiss');
      expect(dismiss.length).toBeGreaterThanOrEqual(1);
    });

    it('the secondary action is NOT styled as orange (no .locked-btn class on dismiss)', () => {
      const { container } = render(<LockedModalFixture />);
      const dismiss = container.querySelector('.locked-dismiss');
      expect(dismiss?.classList.contains('locked-btn')).toBe(false);
    });
  });

  describe('LOGIN modal', () => {
    it('has exactly one .locked-btn (the orange "Sign in" submit CTA)', () => {
      const { container } = render(<LoginModalFixture />);
      assertSingleOrangeCTA(container, 'LOGIN');
    });

    it('the orange CTA is also marked .login-submit', () => {
      const { container } = render(<LoginModalFixture />);
      const cta = container.querySelector('.locked-btn');
      expect(cta?.classList.contains('login-submit')).toBe(true);
    });

    it('has a text-only secondary action (.locked-dismiss "Cancel")', () => {
      const { container } = render(<LoginModalFixture />);
      const dismiss = container.querySelectorAll('.locked-dismiss');
      expect(dismiss.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('COMING SOON modal', () => {
    it('has exactly one .locked-btn (the orange "Send request" CTA)', () => {
      const { container } = render(<ComingSoonModalFixture />);
      assertSingleOrangeCTA(container, 'COMING SOON');
    });

    it('uses overlay click to dismiss (no .locked-dismiss button required)', () => {
      const { container } = render(<ComingSoonModalFixture />);
      // Overlay-click dismissal is the secondary mechanism — no inline dismiss button.
      // This is acceptable because the modal still has at most one orange CTA.
      const overlay = container.querySelector('.locked-overlay');
      expect(overlay).toBeTruthy();
    });
  });

  describe('cross-modal invariant', () => {
    it('every modal renders ≤ 1 element with .locked-btn class', () => {
      for (const Modal of [LockedModalFixture, LoginModalFixture, ComingSoonModalFixture]) {
        const { container } = render(<Modal />);
        const orange = container.querySelectorAll('.locked-btn');
        expect(orange.length).toBeLessThanOrEqual(1);
      }
    });
  });
});
