import React from 'react'

const Home: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to Pafar</h2>
            <p className="text-gray-600">Your ride booking platform</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home