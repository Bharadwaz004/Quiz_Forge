import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#2a2924',
            color: '#f0efe8',
            border: '1px solid rgba(204, 201, 184, 0.1)',
            fontFamily: '"DM Sans", sans-serif',
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
);
