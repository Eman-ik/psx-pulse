import { AppLayout } from '@/components/layout/AppLayout'
import { ScreeningFunnelView } from '@/components/research/ScreeningFunnelView'

export const metadata = {
  title: 'Fundamental Screening | PSX Pulse',
}

export default function ScreeningPage() {
  return (
    <AppLayout>
      <div className="px-6 py-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <h1 className="text-2xl font-bold">Fundamental Analysis Screening</h1>
            <p className="text-sm text-muted mt-1">
              5-stage screening funnel to identify highest-quality investment candidates
            </p>
          </div>

          <ScreeningFunnelView />
        </div>
      </div>
    </AppLayout>
  )
}
