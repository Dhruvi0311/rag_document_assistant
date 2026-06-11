import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Archival — RAG Document Intelligence",
  description: "Query your documents with precision. Hybrid retrieval, cross-encoder reranking, streaming responses.",
  robots: "noindex",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

import { ThemeProvider } from "./components/ThemeProvider";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 transition-colors duration-300 antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
