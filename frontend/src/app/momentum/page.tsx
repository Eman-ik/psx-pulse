import { AppLayout } from '@/components/layout/AppLayout'
import MomentumScreenerView from '@/components/screeners/MomentumScreenerView'

export const metadata = {
  title: 'Momentum Analysis | PSX Pulse',
}

export default function MomentumPage() {
  return (
    <AppLayout>
      <div className="flex-1 px-6 py-12 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <MomentumScreenerView />
        </div>
      </div>
    </AppLayout>
  )
}
