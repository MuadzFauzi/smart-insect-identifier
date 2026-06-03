'use client'
 
import { useCallback, useRef, useState } from 'react'
 
interface Props {
  onFileSelect: (file: File) => void
  isLoading: boolean
  previewUrl: string | null
}
 
export default function ImageUploader({ onFileSelect, isLoading, previewUrl }: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
 
  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return
    onFileSelect(file)
  }, [onFileSelect])
 
  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [handleFile])
 
  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true) }
  const onDragLeave = () => setIsDragging(false)
  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }
 
  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onClick={() => !isLoading && inputRef.current?.click()}
      className={`relative w-full rounded-2xl overflow-hidden cursor-pointer transition-all duration-300 ${isDragging ? 'drop-zone-active' : ''}`}
      style={{
        border: `2px dashed ${isDragging ? 'var(--accent-green)' : 'var(--border-color)'}`,
        background: 'var(--bg-secondary)',
        minHeight: '320px',
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={onInputChange}
        disabled={isLoading}
      />
 
      {previewUrl ? (
        <div className="relative w-full h-full" style={{ minHeight: '320px' }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="Preview"
            className="w-full h-full object-contain transition-all duration-500"
            style={{ minHeight: '320px', maxHeight: '480px' }}
          />
 
          {isLoading && (
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.35)' }} />
 
              <div
                className="absolute left-0 right-0 h-[2px]"
                style={{
                  background: 'linear-gradient(90deg, transparent, var(--accent-green), transparent)',
                  boxShadow: '0 0 12px 4px var(--accent-glow)',
                  animation: 'scanLine 1.8s ease-in-out infinite',
                }}
              />
 
              {[
                'top-4 left-4 border-t-2 border-l-2',
                'top-4 right-4 border-t-2 border-r-2',
                'bottom-4 left-4 border-b-2 border-l-2',
                'bottom-4 right-4 border-b-2 border-r-2',
              ].map((cls, i) => (
                <div
                  key={i}
                  className={`absolute w-6 h-6 ${cls}`}
                  style={{ borderColor: 'var(--accent-green)' }}
                />
              ))}
 
              <div className="absolute bottom-0 left-0 right-0 p-3 flex items-center justify-center gap-2">
                <span
                  className="text-xs font-mono tracking-widest uppercase animate-pulse"
                  style={{ color: 'var(--accent-green)' }}
                >
                  Menganalisis Spesimen...
                </span>
              </div>
            </div>
          )}
 
          {!isLoading && (
            <div
              className="absolute bottom-0 left-0 right-0 p-2 text-center text-xs opacity-0 hover:opacity-100 transition-opacity duration-200"
              style={{
                background: 'linear-gradient(to top, rgba(0,0,0,0.6), transparent)',
                color: '#fff',
              }}
            >
              Klik untuk ganti gambar
            </div>
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center gap-4 p-10" style={{ minHeight: '320px' }}>
          <div
            className="w-20 h-20 rounded-full flex items-center justify-center float"
            style={{ background: 'var(--accent-glow)', border: '1px solid var(--border-color)' }}
          >
            <span className="text-4xl select-none">🦋</span>
          </div>
 
          <div className="text-center space-y-1">
            <p className="font-serif text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
              {isDragging ? 'Lepaskan di sini' : 'Unggah Gambar Serangga'}
            </p>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Seret & lepas, atau klik untuk memilih
            </p>
            <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
              JPG · PNG · WebP · maks 10 MB
            </p>
          </div>
 
          <div
            className="mt-2 px-5 py-2 rounded-full text-sm font-medium transition-all duration-200 hover:scale-105"
            style={{
              background: 'var(--accent-green)',
              color: '#fff',
              boxShadow: '0 4px 12px var(--accent-glow)',
            }}
          >
            Pilih File
          </div>
        </div>
      )}
    </div>
  )
}