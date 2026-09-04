import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PulseCheck — Live Audience Insights",
  description:
    "Live audience-response and insights-capture platform for Botswana's advertising, PR, and research industry.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-sans min-h-screen">{children}</body>
    </html>
  );
}
