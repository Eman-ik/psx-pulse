import { AppLayout } from '@/components/layout/AppLayout'
import TechnicalScreenerView from '@/components/screeners/TechnicalScreenerView'

export const metadata = {
  title: 'Technical Analysis | PSX Pulse',
}

export default function TechnicalPage() {
  return (
    <AppLayout>
      <div className="flex-1 px-6 py-12 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <TechnicalScreenerView />
        </div>
      </div>
    </AppLayout>
  )
}
