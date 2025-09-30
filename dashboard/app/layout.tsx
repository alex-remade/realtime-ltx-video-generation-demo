import type { Metadata } from 'next'
import { JetBrains_Mono } from 'next/font/google'
import './globals.css'

const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'FAL Realtime AI Dashboard',
  description: 'Real-time monitoring dashboard for AI video generation pipeline',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`font-focal ${jetbrainsMono.variable}`}>
        <div className="min-h-screen bg-fal-gray-50">
          {/* FAL Header */}
          <header className="bg-white border-b border-fal-gray-200">
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
              <div className="flex justify-between items-center py-6">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-3">
                    <div className="h-8 flex items-center">
                      <img 
                        src="https://github.com/fal-ai/fal-assets/blob/main/C1/Logo%20%26%20Text%20Padding%20Transparent%20C1.png?raw=true"
                        alt="FAL Logo"
                        className="h-8 w-auto"
                      />
                    </div>
                    <div>
                      <h1 className="text-xl font-bold text-fal-gray-900">
                        Realtime Video Streamer (Demo App)
                      </h1>
   
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </header>
          
          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
            <div className="fade-in">
              {children}
            </div>
          </main>
          
          {/* Footer */}
          <footer className="border-t border-fal-gray-200 mt-16">
            <div className="max-w-7xl mx-auto px-6 lg:px-8 py-6">
              <div className="flex justify-between items-center text-sm text-fal-gray-600">
                <div>FAL Realtime AI Dashboard v1.0</div>
                <div className="flex items-center space-x-4">
                  <span>Powered by FAL</span>
                  <div className="w-1 h-1 bg-fal-gray-400 rounded-full"></div>
                  <span className="font-mono">{new Date().getFullYear()}</span>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
