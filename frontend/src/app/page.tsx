'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import ThemeToggle from '@/components/ui/ThemeToggle'
import ImageUploader from '@/components/ui/ImageUploader'

interface PredictionItem {
  class_name: string
  confidence: number
}

interface PredictResponse {
  predicted_class: string
  confidence: number
  top_predictions: PredictionItem[]
  gemini_info: string | null
  gemini_available: boolean
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<PredictResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile)
    setPreviewUrl(URL.createObjectURL(selectedFile))
    setResult(null)
    setError(null)
    setIsLoading(true)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/predict`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Gagal menganalisis gambar. Pastikan backend Anda aktif.')
      }

      const data: PredictResponse = await response.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Terjadi kesalahan sistem.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen px-4 py-8 md:px-12 lg:px-24 max-w-7xl mx-auto flex flex-col justify-between">
      {/* Header Editorial */}
      <header className="flex justify-between items-baseline border-b pb-6" style={{ borderColor: 'var(--border-color)' }}>
        <div className="space-y-1">
          <h1 className="font-serif text-3xl md:text-4xl font-bold tracking-tight text-gradient">
            The AI Field Guide
          </h1>
          <p className="font-mono text-xs uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            Vol. I — Smart Insect Identifier
          </p>
        </div>
        <ThemeToggle />
      </header>

      {/* Grid Asimetris Utama */}
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-8 my-10 items-start">
        {/* Kolom Kiri: Input & Probabilitas (Slot: 5/12) */}
        <section className="lg:col-span-5 space-y-6 lg:sticky lg:top-8 animate-fade-up">
          <div className="card rounded-2xl p-4 glass">
            <ImageUploader 
              onFileSelect={handleFileSelect} 
              isLoading={isLoading} 
              previewUrl={previewUrl} 
            />
          </div>

          {error && (
            <div className="p-4 rounded-xl font-mono text-xs border border-red-200 bg-red-50 text-red-700 dark:bg-red-950/20 dark:border-red-900 dark:text-red-400">
              [⚠️ SYSTEM ERROR]: {error}
            </div>
          )}

          {/* Metrics Probabilitas */}
          {result && (
            <div className="card rounded-2xl p-6 space-y-4 animate-fade-in">
              <h3 className="font-mono text-xs uppercase tracking-widest font-semibold" style={{ color: 'var(--accent-amber)' }}>
                Model Classification Metrics
              </h3>
              <div className="space-y-3">
                {result.top_predictions.map((pred, index) => (
                  <div key={index} className="space-y-1">
                    <div className="flex justify-between font-mono text-xs">
                      <span className="capitalize text-slate-700 dark:text-slate-300 font-medium">
                        {pred.class_name}
                      </span>
                      <span style={{ color: index === 0 ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                        {(pred.confidence * 100).toFixed(2)}%
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <div 
                        className="h-full rounded-full animate-bar-fill"
                        style={{
                          background: index === 0 
                            ? 'linear-gradient(90deg, var(--accent-green), var(--accent-amber))' 
                            : 'var(--text-muted)',
                          '--bar-width': `${pred.confidence * 100}%`
                        } as React.CSSProperties}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Kolom Kanan: Ensiklopedia Gemini (Slot: 7/12) */}
        <section className="lg:col-span-7 card rounded-2xl p-8 glass min-h-[450px] flex flex-col justify-between">
          {result?.gemini_info ? (
            <article className="prose-insect animate-fade-in">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.gemini_info}</ReactMarkdown>
            </article>
          ) : isLoading ? (
            /* Skeleton Loading */
            <div className="space-y-6 py-4 w-full">
              <div className="h-8 w-2/3 rounded shimmer" />
              <div className="h-[1px] w-full bg-slate-200 dark:bg-slate-800" />
              <div className="space-y-3">
                <div className="h-4 w-full rounded shimmer" />
                <div className="h-4 w-5/6 rounded shimmer" />
                <div className="h-4 w-full rounded shimmer" />
              </div>
            </div>
          ) : (
            /* State Awal / Kosong */
            <div className="h-full flex flex-col items-center justify-center text-center p-8 my-auto space-y-2 opacity-60">
              <span className="text-3xl">📜</span>
              <p className="font-serif text-lg italic" style={{ color: 'var(--text-secondary)' }}>
                "Menanti lembaran spesimen diunggah..."
              </p>
              <p className="text-xs max-w-sm" style={{ color: 'var(--text-muted)' }}>
                Unggah gambar spesimen serangga atau makhluk hidup di sisi kiri untuk membuka catatan ensiklopedia digital otomatis.
              </p>
            </div>
          )}

          {result && (
            <div className="mt-8 pt-4 border-t border-dashed font-mono text-[10px] flex justify-between" style={{ borderColor: 'var(--border-color)', color: 'var(--text-muted)' }}>
              <span>ENGINE: EFFICIENTNET-B3 + PYTORCH</span>
              <span>GEMINI INTEGRATION: {result.gemini_available ? 'ACTIVE' : 'FALLBACK'}</span>
            </div>
          )}
        </section>
      </main>

      <footer className="text-center font-mono text-[10px] opacity-50 py-4 border-t" style={{ borderColor: 'var(--border-color)' }}>
        © {new Date().getFullYear()} — Naturalist Digital Codex & AI Systems.
      </footer>
    </div>
  )
}