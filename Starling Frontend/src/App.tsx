import { useState } from 'react'
import './App.css'
import ChatInterface from './pages/ChatInterface'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <ChatInterface />
    </div>
  )
}

export default App
