import './globals.css';
import type { Metadata } from 'next';
import { Analytics } from '@vercel/analytics/next';
import { Inter_Tight, Roboto_Mono } from 'next/font/google';

// D-07/D-08/D-09 — default body + mono type stack via next/font.
// If Sergey opts into Suisse Int'l before merge, swap this block per
// RESEARCH.md §"Alternate snippet" and drop the -0.32px letter-spacing.
const interTight = Inter_Tight({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-body',
});

const robotoMono = Roboto_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
  weight: ['400', '500'],
});

export const metadata: Metadata = {
  title: 'FC Benchmark — Feature Matrix',
  description: 'UX benchmark of 26 sports website homepages',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${interTight.variable} ${robotoMono.variable}`}>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
