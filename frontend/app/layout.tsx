import "./globals.css";

export const metadata = {
  title: "Talent Matcher",
  description: "Find perfect matches between candidates and jobs",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
