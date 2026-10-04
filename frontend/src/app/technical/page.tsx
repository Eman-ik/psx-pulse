import { AppLayout } from '@/components/layout/AppLayout'
import TechnicalScreenerView from '@/components/screeners/TechnicalScreenerView'

export const metadata = {
  title: 'Technical Analysis | PSX Pulse',
}

export default function TechnicalPage() {
  return (
    <AppLayout>
      <div className="flex-1 px-6 py-6 lg:px-8">
        <TechnicalScreenerView />
      </div>
    </AppLayout>
  )
}
