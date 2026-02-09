import { SectionOutput } from '../../types/models'

interface OutputSectionProps {
  section: SectionOutput
  showJson: boolean
}

function OutputSection({ section, showJson }: OutputSectionProps) {
  const content = section.analysis || section.summary

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-primary-900 mb-4">{section.title}</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Content */}
        <div className="space-y-4">
          {content && (
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{content}</p>
            </div>
          )}
          
          {section.points && section.points.length > 0 && (
            <ul className="list-disc list-inside space-y-2 text-gray-700">
              {section.points.map((point, idx) => (
                <li key={idx}>{point}</li>
              ))}
            </ul>
          )}
        </div>

        {/* Right: Image */}
        {section.image && (
          <div className="flex items-start justify-center">
            <img
              src={section.image.src}
              alt={section.image.alt}
              className="max-w-full h-auto rounded-lg shadow-sm"
            />
          </div>
        )}
      </div>

      {/* JSON Viewer */}
      {showJson && section.rawJson && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Raw JSON Data</h3>
          <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto text-xs">
            {JSON.stringify(section.rawJson, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default OutputSection
