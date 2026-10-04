import { AppLayout } from '@/components/layout/AppLayout'
import { ScreeningFunnelView } from '@/components/research/ScreeningFunnelView'
import { SectionHeader } from '@/components/glass'

export const metadata = {
  title: 'Fundamental Screening | PSX Pulse',
}

export default function ScreeningPage() {
  return (
    <AppLayout>
      <div className="px-6 py-12 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <SectionHeader
            title="Fundamental Analysis Screening"
            subtitle="5-stage screening funnel to identify highest-quality investment candidates"
          />

          <ScreeningFunnelView />
        </div>
      </div>
    </AppLayout>
  )
}
