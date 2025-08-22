import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { HelmetProvider } from 'react-helmet-async';

// Global console log suppression based on environment
(() => {
  const NOOP = () => {};
  const level = process.env.REACT_APP_LOG_LEVEL || (process.env.NODE_ENV === 'production' ? 'warn' : 'debug');
  const levelRank = { silent: 5, error: 4, warn: 3, info: 2, log: 1, debug: 0 };
  const methodRank = { debug: 0, log: 1, info: 2, warn: 3, error: 4 };
  const threshold = levelRank[level] ?? 0;

  Object.keys(methodRank).forEach((method) => {
    if (methodRank[method] < threshold && typeof console[method] === 'function') {
      // Suppress lower-priority methods
      console[method] = NOOP;
    }
  });
})();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <HelmetProvider>
      <App />
    </HelmetProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
