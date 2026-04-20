import './globals.css';
import type { Metadata } from 'next';
import { Analytics } from '@vercel/analytics/next';
import localFont from 'next/font/local';
import { Roboto_Mono } from 'next/font/google';

// Suisse Int'l — licensed font supplied by humbleteam (public/fonts/suisse/).
// Replaces Inter Tight per Figma spec (body: SuisseIntl Regular 14px / -0.3px).
const suisseIntl = localFont({
  src: [
    { path: '../public/fonts/suisse/SuisseIntl-Regular.otf',  weight: '400', style: 'normal' },
    { path: '../public/fonts/suisse/SuisseIntl-Medium.otf',   weight: '500', style: 'normal' },
    { path: '../public/fonts/suisse/SuisseIntl-SemiBold.otf', weight: '600', style: 'normal' },
    { path: '../public/fonts/suisse/SuisseIntl-Bold.otf',     weight: '700', style: 'normal' },
  ],
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
    <html lang="en" className={`${suisseIntl.variable} ${robotoMono.variable}`}>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
