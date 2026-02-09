import { ReactNode } from 'react'
import Header from '../Header/Header'

interface LayoutProps {
  children: ReactNode
}

function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen" style={{ backgroundColor: '#CADCFC' }}>
      <Header />
      <main className="w-full">
        {children}
      </main>
    </div>
  )
}

export default Layout
