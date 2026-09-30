import { ScreeningFunnelView } from '@/components/research/ScreeningFunnelView'

export const metadata = {
  title: 'Screening Funnel | Research Studio',
}

export default function ScreeningPage() {
  return (
    <main className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Fundamental Analysis Screening</h1>
          <p className="text-sm text-muted mt-1">
            5-stage screening funnel to identify highest-quality investment candidates
          </p>
        </div>

        <ScreeningFunnelView />
      </div>
    </main>
  )
}
