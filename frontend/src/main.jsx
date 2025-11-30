
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx' 
// import './index.css' is usually here, but we rely on Tailwind CDN.

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)