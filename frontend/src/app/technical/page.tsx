import Sidebar from '@/components/dashboard/Sidebar'
import Topbar from '@/components/dashboard/Topbar'
import TechnicalScreenerView from '@/components/screeners/TechnicalScreenerView'

export default function TechnicalPage() {
  return (
    <div className="flex min-h-screen w-full bg-bg">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 px-6 py-6 lg:px-8">
          <TechnicalScreenerView />
        </main>
      </div>
    </div>
  )
}
