import type { Metadata } from "next";
import { ThemeProvider } from "next-themes";
// @ts-ignore
import "./globals.css";

export const metadata: Metadata = {
  title: "Insect Identifier — AI Field Guide",
  description:
    "Identifikasi serangga menggunakan deep learning & Google Gemini",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange={false}
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
