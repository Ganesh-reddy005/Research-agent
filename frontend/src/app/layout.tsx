import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["300", "400", "500", "600", "700"],
});

const ibmPlexMono = IBM_Plex_Mono({ 
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600", "700"],
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Research Agent | Retro Engine",
  description: "High-performance research synthesis with a retro touch.",
};

export default function RootLayout(props: LayoutProps) {
  return (
    <html lang="en">
      <body className={`${spaceGrotesk.variable} ${ibmPlexMono.variable} font-sans antialiased text-mistral-black`}>
        {props.children}
      </body>
    </html>
  );
}
