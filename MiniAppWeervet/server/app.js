// app.js

const express = require('express');
const db = require('./db'); // Импортируем наш файл с подключением к БД

const app = express();
const PORT = 5000;

// Middleware для работы с JSON
app.use(express.json());

// Маршрут для проверки подключения к базе данных
app.get('/add_pets', async (req, res) => {
  try {
    const result = await db.query('SELECT * FROM users'); // пример запроса к таблице "users"
    res.json(result.rows);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Ошибка сервера');
  }
});

// Запуск сервера
app.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`);
});
