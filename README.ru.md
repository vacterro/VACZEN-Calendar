# VACZEN Calendar

> Минималистичный, однопроходный календарь + менеджер задач на Tk.
> Тёмная Win95-тема по умолчанию. Один файл на Python, ноль зависимостей.

<p align="center">
  <img alt="Лицензия" src="https://img.shields.io/github/license/vacterro/VACZEN-Calendar?style=for-the-badge&color=9DD9F9">
  <img alt="Версия" src="https://img.shields.io/badge/version-0.0.1-9DD9F9?style=for-the-badge">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-9DD9F9?style=for-the-badge&logo=python&logoColor=black">
  <img alt="Один файл" src="https://img.shields.io/badge/%D0%BE%D0%B4%D0%B8%D0%BD%20%D1%84%D0%B0%D0%B9%D0%BB-%D0%B4%D0%B0-9DD9F9?style=for-the-badge">
  <img alt="Зависимости" src="https://img.shields.io/badge/%D0%B7%D0%B0%D0%B2%D0%B8%D1%81%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D0%B8-stdlib%20only-9DD9F9?style=for-the-badge">
</p>

<p align="center">
  <img alt="Размер репо" src="https://img.shields.io/github/repo-size/vacterro/VACZEN-Calendar?style=flat-square">
  <img alt="Размер кода" src="https://img.shields.io/github/languages/code-size/vacterro/VACZEN-Calendar/ZEN_CALENDAR.py?style=flat-square&label=ZEN_CALENDAR.py">
  <img alt="Последний коммит" src="https://img.shields.io/github/last-commit/vacterro/VACZEN-Calendar?style=flat-square">
  <img alt="Issues" src="https://img.shields.io/github/issues/vacterro/VACZEN-Calendar?style=flat-square">
</p>

<p align="center">
  <a href="https://buymeacoffee.com/vacuum34"><img alt="Поддержать" src="https://img.shields.io/badge/%E2%9D%A4%EF%B8%8F%20%D0%9F%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B0%D1%82%D1%8C-9DD9F9?style=for-the-badge"></a>
  <a href="docs/overview.md"><img alt="Доки" src="https://img.shields.io/badge/%F0%9F%93%9D%20%D0%94%D0%BE%D0%BA%D0%B8-9DD9F9?style=for-the-badge"></a>
  <a href="#-%D0%B3%D0%BE%D1%80%D1%8F%D1%87%D0%B8%D0%B5-%D0%BA%D0%BB%D0%B0%D0%B2%D0%B8%D1%88%D0%B8"><img alt="Клавиши" src="https://img.shields.io/badge/%E2%9C%A8%20%D0%93%D0%BE%D1%80%D1%8F%D1%87%D0%B8%D0%B5%20%D0%BA%D0%BB%D0%B0%D0%B2%D0%B8%D1%88%D0%B8-9DD9F9?style=for-the-badge"></a>
</p>

---

## 📸 Скриншот

```
┌──────────────────────────────────────────────────────────────┐
│  Вт 01 сен 2026  14:23:07   ◀ ▶   Сентябрь 2026   ⌂ Сегодня  │
├──────────────────────────────────────────────────────────────┤
│  Пн  Вт  Ср  Чт  Пт  Сб  Вс                                 │
│       [ 1] [ 2] [ 3] [ 4] [ 5] [ 6]                          │
│   [ 7] [ 8] [ 9][10] [11] [12] [13]                          │
│  [14] [15] [16] [17] [18] [19] [20]                          │
│  [21] [22] [23] [24] [25] [26] [27]                          │
│  [28] [29] [30] [ 1] [ 2] [ 3] [ 4]                          │
│                                                              │
│            ┌─ Выбрано: Ср 16 сен ───────────────┐            │
│            │ • 09:00  Стендап команды  [готово] │            │
│            │ • 14:00  Ревью PR #142            │            │
│            │ • 19:30  🏃 Пробежка, ленивая жопа│            │
│            └────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
   Ctrl+K  настройки   f   фокус   s   сохранить   Esc   выход
```

> ASCII-набросок — настоящая штука тёмная, золото-на-чёрном, пиксель-чистая.
> Когда появится настоящий скриншот, положи его в `docs/screenshot.png` и
> раскомментируй строку ниже.

<!-- ![VACZEN Calendar под Windows](docs/screenshot.png) -->

---

## ✨ Возможности

| | |
|---|---|
| 🎯 **Один файл, одна цель** | Всё приложение — это `ZEN_CALENDAR.py`. Никакого фреймворка, пакета, вендорных копий. |
| 📦 **Ноль зависимостей** | Только стандартная библиотека Python. `tkinter`, `json`, `datetime`, `pathlib`. Без `pip install`. |
| 🌑 **Тёмная Win95 по умолчанию** | Чёрные панели, золотые акценты, никаких анимаций и сглаживаний. Дружит с батареей. |
| ⚡ **Клавиатура — главная** | Каждое действие — одна клавиша. Мышь — по желанию. |
| 💾 **Атомарное сохранение** | Запись с межпроцессной блокировкой и проверкой поколения. Два экземпляра не перетрут друг друга. |
| 🛡️ **Самовосстанавливающаяся загрузка** | Битый JSON → карантин, единственная копия никогда не затирается. Невалидные даты изолируются, а не молча теряются. |
| 🪟 **Режим фокуса** | Одна клавиша (`f`) прячет всё кроме календаря. Защита от расфокуса. |
| ⚙️ **15-цветная тема** | Фон, панели, текст, шапка, выходные, сегодня, выбрано, акцент — всё крутится на лету. |
| 🌍 **i18n** | `lang: ru / en / uk`. Ключ настроек, все строки UI его слушаются. |
| 🔢 **Номера недель ISO** | Опциональная колонка. |
| 🕐 **Живые часы** | Снизу-справа, самопланирующиеся, никогда не отстают. |
| 📐 **Геометрия, которая помнит** | Размер, позиция, полный экран, always-on-top. Ходит по кругу через файл данных. |

---

## 🚀 Установка

```bash
# 1. Клонировать
git clone https://github.com/vacterro/VACZEN-Calendar.git
cd VACZEN-Calendar

# 2. Запустить (шага установки нет)
python ZEN_CALENDAR.py
```

Всё. Python 3.11 или новее. Виртуальное окружение не нужно — ставить
нечего. Под Windows можно также переименовать в `.pyw` или запускать
через `pythonw.exe` — без консоли.

---

## ⌨️ Горячие клавиши

Все привязки ниже глушатся, пока ты печатаешь в редакторе или пока
открыта панель Настроек — черновик не теряется от случайного нажатия.

| Клавиша | Действие |
|---|---|
| `←` / `→` | Предыдущий / следующий месяц |
| `↑` / `↓` | Предыдущий / следующий год |
| `f` | Переключить **режим фокуса** |
| `a` | Добавить задачу к выбранному дню |
| `e` | Редактировать выбранную задачу |
| `d` | Удалить выбранную задачу |
| `s` | Сохранить сейчас |
| `Пробел` | Отметить выбранную задачу выполненной / обратно |
| `Enter` | В редакторе → принять; иначе → обновить панель деталей |
| `Esc` | Настройки открыты → закрыть; редактируешь → отменить; иначе → выход |
| `Ctrl+K` | Переключить панель настроек |

---

## 📂 Структура проекта

```
VACZEN-Calendar/
├── ZEN_CALENDAR.py          ← всё приложение
├── CalendarTask_data.json   ← твои задачи (создаётся автоматически, в .gitignore)
├── ZenCalendar_data.json    ← (legacy) альтернативное имя того же файла
├── docs/                    ← архитектура и справки
│   ├── overview.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── ui-and-rendering.md
│   ├── settings.md
│   ├── keyboard.md
│   └── canonical-ids.md
├── README.md                ← ты здесь
├── README.et.md             ← eesti
├── README.ru.md             ← русский
├── CONTRIBUTING.md
└── LICENSE                  ← MIT
```

---

## 📚 Документация

| Док | Что покрывает |
|---|---|
| [Обзор](docs/overview.md) | Что это за приложение, а что — нет. |
| [Архитектура](docs/architecture.md) | Метод-за-методом карта `ZEN_CALENDAR.py`. Без воды. |
| [Модель данных](docs/data-model.md) | Форма JSON, атомарное сохранение, карантин, восстановление. |
| [UI & рендеринг](docs/ui-and-rendering.md) | Тема, шрифты, геометрия, режим фокуса. |
| [Настройки](docs/settings.md) | `DEFAULT_SETTINGS`, контракт валидации, пайплайн применения. |
| [Клавиатура](docs/keyboard.md) | Полная таблица клавиша → обработчик. |
| [Канонические ID](docs/canonical-ids.md) | Имена, которые рефакторинг не должен ломать. |

---

## 🤝 Участие

Issues и PR приветствуются. Баг-репорты: добавь ОС, версию Python
(`python --version`) и содержимое файла данных (или отредактированный
кусок — пути и заметки можно санитизировать).

Для крупных изменений сначала открой issue, чтобы договориться о форме
до того, как потратишь на это выходные. Смотри [CONTRIBUTING.md](CONTRIBUTING.md).

---

## ❤️ Поддержать

Если это держит тебя подальше от телефона и перед настоящим расписанием:

<a href="https://buymeacoffee.com/vacuum34"><img alt="Купи мне кофе" src="https://img.shields.io/badge/%D0%BA%D1%83%D0%BF%D0%B8%20%D0%BC%D0%BD%D0%B5%20%D0%BA%D0%BE%D1%84%D0%B5-vacuum34-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black"></a>

---

## 📜 Лицензия

[MIT](LICENSE) — делай что хочешь, только сохрани строку копирайта.

---

<p align="center">
  <sub>VACZEN Calendar · v0.0.1 · один файл · ноль зависимостей · клавиатура — главная</sub>
</p>
