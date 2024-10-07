// client/src/App.js

import React, { useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('');

  // useEffect(() => {
  //   // Получение данных с сервера
  //   fetch('http://localhost:5000/api/message')
  //     .then(response => response.json())
  //     .then(data => setMessage(data.message))
  //     .catch(error => console.error('Ошибка:', error));
  // }, []);
  useEffect(() => {
    fetch('/api/message')
      .then(response => response.json())
      .then(data => setMessage(data.message))
      .catch(error => console.error('Ошибка:', error));
  }, []);
  

  return (
    <div className="App">
      <h1>MiniApp на React и Node.js</h1>
      <p>{message}</p>
    </div>
  );
}

export default App;