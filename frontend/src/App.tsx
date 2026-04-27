import { Routes, Route } from 'react-router-dom'
import Studio from './pages/Studio'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Studio />} />
    </Routes>
  )
}
