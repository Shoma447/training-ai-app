import "./globals.css"; // Tailwind CSS 読み込み

export const metadata = {
  title: "AIパーソナルトレーナー",
  description: "AIがトレーニングと食事をサポートします",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="bg-gray-100">{children}</body>
    </html>
  );
}
