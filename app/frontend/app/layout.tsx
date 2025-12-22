import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Nav from "./components/Nav";
import { HealthScanProvider } from "./context/HealthScanContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HealthScan - AI Healthcare Assistant",
  description: "Scan medical forms, prescriptions, and healthcare documents. Get instant help with healthcare paperwork.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <HealthScanProvider>
          {/* Skip Navigation Link for Accessibility */}
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>
          <Nav />
          <main id="main-content" tabIndex={-1} className="flex-1 flex flex-col min-h-0">
            {children}
          </main>
        </HealthScanProvider>
      </body>
    </html>
  );
}
