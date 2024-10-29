// app.js

const express = require('express');
const db = require('./db'); // Импортируем наш файл с подключением к БД
const bodyParser = require('body-parser');
const app = express();
const PORT = 5000;

// Middleware для работы с JSON
app.use(express.json());

// Middleware для обработки JSON
// app.use(bodyParser.json());

app.post('/register', async (req, res) => {
  const { telegram_id, name } = req.body;

  try {
    // Проверяем, есть ли уже пользователь с таким telegram_id
    const userCheck = await db.query('SELECT * FROM users WHERE telegram_id = $1', [telegram_id]);

    if (userCheck.rows.length > 0) {
      return res.status(200).json({ message: 'Пользователь уже существует' });
    }

    // Если пользователя нет, добавляем его в базу данных
    const newUser = await db.query(
      'INSERT INTO users (telegram_id, name) VALUES ($1, $2) RETURNING *',
      [telegram_id, name]
    );

    res.status(201).json({ message: 'Пользователь зарегистрирован', user: newUser.rows[0] });
  } catch (error) {
    console.error('Ошибка при регистрации пользователя:', error);
    res.status(500).json({ message: 'Ошибка сервера' });
  }
});

// Роут для обработки добавления питомца
app.post('/add_pet', async (req, res) => {
  const {name, type, date_birth, age, sex, breed, color, weight, sterilized, chip_number, chip_place, town, keeping, special_signs, photo} = req.body;

  try {
    const result = await pool.query(
      `INSERT INTO pets (name, type, date_birth, age, sex, breed, color, weight, sterilized, chip_number, chip_place, town, keeping, special_signs, photo)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
       RETURNING *`,
      [name, type, date_birth, age, sex, breed, color, weight, sterilized, chip_number, chip_place, town, keeping, special_signs, photo]
    );

    res.status(201).json({ message: 'Питомец добавлен!', pet: result.rows[0] });
  } catch (error) {
    console.error('Ошибка при добавлении питомца:', error);
    res.status(500).json({ message: 'Ошибка сервера при добавлении питомца' });
  }
});

// Запуск сервера
app.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`);
});
