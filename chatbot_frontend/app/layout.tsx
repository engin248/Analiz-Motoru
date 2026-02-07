// app/layout.tsx
import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { LightboxProvider } from "@/components/ui/lightbox-provider";
import { ThemeProvider } from "@/components/ThemeContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "LUMORA AI",
    description: "Tekstil odaklı yapay zeka asistanı",
    manifest: "/manifest.json",
    appleWebApp: {
        capable: true,
        statusBarStyle: "default",
        title: "LUMORA AI",
    },
};

export const viewport: Viewport = {
    themeColor: "#1B5E20",
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="tr" suppressHydrationWarning>
            <body className={`${inter.className} bg-brand-bg`} suppressHydrationWarning>
                <ThemeProvider>
                    <LightboxProvider>
                        {children}
                    </LightboxProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}