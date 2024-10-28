import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import FooterButtons from './FooterButtons';
// import Back_button from './BackButton.js';
import Shedule from './pages/shedule.js';
import Add_pet from './pages/add_pet.js';
import My_pets from './pages/my_pets.js';
import Profile from './pages/profile.js';
import NotFound from './pages/NotFound.js';

function App() {
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);

  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      const tg = window.Telegram.WebApp;

      // Вызов expand() для автоматического масштабирования
      tg.expand();

      const handleViewportChange = () => {
        setViewportHeight(tg.viewportHeight); // Устанавливаем высоту вьюпорта от Telegram SDK
        console.log("Изменение вьюпорта. Высота: " + tg.viewportHeight);
      };

      tg.onEvent('viewportChanged', handleViewportChange);

      return () => {
        tg.offEvent('viewportChanged', handleViewportChange);
      };
    }
  }, []);

  return (
    <div id="app" style={{ height: `${viewportHeight}px` }}>
      
      {/* <Back_button /> */}
      
      <div id="work">
      <Router>
        <Routes>
            <Route path="/" element={<Shedule />}/>
            <Route path="/add_pet" element={<Add_pet/>}/>
            <Route path="/my_pets" element={<My_pets />}/>
            <Route path="/profile" element={<Profile />}/>
            <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
      </div>
      <FooterButtons />
    </div>
  );
}

export default App;
