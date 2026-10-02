import Sidebar from '@/components/dashboard/Sidebar'
import MomentumScreenerView from '@/components/screeners/MomentumScreenerView'

export default function MomentumPage() {
  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="flex-1 px-6 py-6 lg:px-8">
          <MomentumScreenerView />
        </main>
      </div>
    </div>
  )
}
