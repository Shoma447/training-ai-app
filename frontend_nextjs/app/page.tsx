import Link from "next/link";

export default function Home() {
  return (
    <main className="flex flex-col items-center justify-center h-screen bg-gradient-to-br from-blue-100 to-blue-300">
      <h1 className="text-4xl font-bold mb-6">AIパーソナルトレーナー</h1>
      <p className="text-lg mb-10 text-gray-700">
        トレーニングや食事についてAIがアドバイスします
      </p>
      <Link
        href="/chat"
        className="bg-blue-600 text-white px-6 py-3 rounded-2xl hover:bg-blue-700"
      >
        はじめる
      </Link>
    </main>
  );
}
