import { useState } from 'react'

interface Tab {
  id: string
  label: string
}

interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onTabChange: (tabId: string) => void
  variant?: 'primary' | 'secondary'
}

function Tabs({ tabs, activeTab, onTabChange, variant = 'primary' }: TabsProps) {
  const isPrimary = variant === 'primary'

  return (
    <div className={`border-b ${isPrimary ? 'border-gray-300' : 'border-gray-200'}`}>
      <div className="flex gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === tab.id
                ? isPrimary
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'bg-gray-100 text-primary-700 rounded-t-md'
                : isPrimary
                ? 'text-gray-600 hover:text-gray-800'
                : 'text-gray-500 hover:bg-gray-50 rounded-t-md'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default Tabs
