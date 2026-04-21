import type { Metadata } from "next";
import { Source_Sans_3 } from "next/font/google";

import "./globals.css";

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-source-sans",
});

export const metadata: Metadata = {
  title: "UFC Matchmaking",
  description: "Search UFC fighters and inspect simple matchup suggestions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${sourceSans.variable} font-body antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
