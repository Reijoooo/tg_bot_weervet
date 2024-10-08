// server/app.js

const express = require('express');
const cors = require('cors');
const app = express();
const PORT = process.env.PORT || 5000;

// Использование CORS для разрешения запросов с клиентской части
app.use(cors());

// Простая маршрутизация
app.get('/message', (req, res) => {
  res.json({ message: 'Привет из MiniApp на сервере!' });
});

// Запуск сервера
app.listen(PORT, () => {
  console.log(`Сервер запущен на http://localhost:${PORT}`);
});