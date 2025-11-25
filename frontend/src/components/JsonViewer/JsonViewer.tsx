interface JsonViewerProps {
  data: any
  title?: string
}

function JsonViewer({ data, title = 'Backend JSON' }: JsonViewerProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">{title}</h3>
      <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto text-xs max-h-96 overflow-y-auto">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}

export default JsonViewer
