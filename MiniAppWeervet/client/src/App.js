import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import FooterButtons from './FooterButtons';
import Shedule from './pages/shedule.js';
import Add_pet from './pages/add_pet.js';
import My_pets from './pages/my_pets.js';
import Profile from './pages/profile.js';
import NotFound from './pages/NotFound.js';

function App() {
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const [viewportWidth, setViewportWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResizeFallback = () => {
      setViewportHeight(window.innerHeight);
      setViewportWidth(window.innerWidth);
    };

    if (window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp;

      // Устанавливаем начальные размеры
      setViewportHeight(tg.viewportHeight);
      setViewportWidth(tg.ViewportWidth);

      // Включаем автоматическое масштабирование
      tg.expand();

      // Обработчик изменения размеров от Telegram SDK
      const handleViewportChange = () => {
        setViewportHeight(tg.viewportHeight);
        setViewportWidth(tg.ViewportWidth); 
      };

      tg.onEvent('viewportChanged', handleViewportChange);

      // Инициализация пользователя при запуске
      const user = tg.initDataUnsafe?.user;
      if (user) registerUser(user);

      // Очистка событий при размонтировании
      return () => tg.offEvent('viewportChanged', handleViewportChange);
    } else {
      // Если Telegram SDK недоступен, слушаем изменения окна в браузере
      window.addEventListener('resize', handleResizeFallback);
      return () => window.removeEventListener('resize', handleResizeFallback);
    }
  }, []);
  
  // Функция для регистрации пользователя
  const registerUser = async (user) => {
    try {
      const response = await fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          telegram_id: user.id,
          username: user.username,
        }),
      });

      if (response.ok) {
        console.log('Пользователь успешно зарегистрирован!');
      } else {
        console.error('Ошибка регистрации пользователя');
      }
    } catch (error) {
      console.error('Ошибка при подключении к серверу:', error);
    }
  };

  return (
    <div id="app" style={{
      height: `${viewportHeight}px`,
      width: `${viewportWidth}px`,
      overflow: 'hidden', // предотвращает скролл при изменениях размера
    }}>
      <div id="work">
      <Router basename="/">
        <Routes>
          <Route path="/shedule" element={<Shedule />} />
          <Route path="/add_pet" element={<Add_pet />} />
          <Route path="/my_pets" element={<My_pets />} />
          <Route path="/" element={<Profile />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
      </div>
      <FooterButtons />
    </div>
  );
}

export default App;
