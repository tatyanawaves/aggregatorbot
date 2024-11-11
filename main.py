import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_TOKEN
from openai_client import ask_chatgpt, generate_image
from database import init_db,get_user_history, save_user_history # Предполагается, что они в файле database_setup.py


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Инициализация базы данных и заполнение данными (однократно при запуске)
init_db()
# populate_database_with_sql()

# Определение состояний
class Form(StatesGroup):
    main_menu = State()
    neural_categories = State()
    neural_list = State()
    neural_info = State()
    ask_question = State()
    generate_image = State()

# Функции для создания клавиатур
def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Нейросети', callback_data='menu_neural')],
        [InlineKeyboardButton(text='Задать вопрос', callback_data='menu_ask')],
        [InlineKeyboardButton(text='Генерация картинки', callback_data='menu_image')],
        [InlineKeyboardButton(text='Моя история', callback_data='menu_history')]
    ])
    return keyboard

def categories_keyboard():
    categories = ['Фото', 'Видео', 'Текст', 'Аудио']
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=category, callback_data=f'neural_category_{category}')] for category in categories
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text='Назад', callback_data='back_to_main_menu')])
    return keyboard

def networks_keyboard(networks):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=network['name'], callback_data=f'neural_network_{idx}')] for idx, network in enumerate(networks)
    ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text='Назад', callback_data='back_to_neural_categories')])
    return keyboard

def back_to_networks_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back_to_neural_list')],
        [InlineKeyboardButton(text='В главное меню', callback_data='back_to_main_menu')]
    ])
    return keyboard

# Обработчики команд и состояний
@router.message(Command(commands=['start']))
async def start_handler(message: types.Message, state: FSMContext):
    await message.reply(
        "Привет! Я бот, который поможет вам узнать о различных нейросетях и получить инструкции для их использования.\n\n"
        "Пожалуйста, выберите опцию:",
        reply_markup=main_menu_keyboard()
    )
    await state.set_state(Form.main_menu)

@router.message(Command(commands=['help']))
async def help_handler(message: types.Message):
    help_text = (
        "/start - Запустить бота и показать главное меню.\n"
        "/help - Показать эту справку.\n"
        "/history - Показать вашу историю запросов.\n"
        "\n"
        "Опции меню:\n"
        "- **Нейросети**: Получить информацию и ссылку на различные нейросети.\n"
        "- **Задать вопрос**: Задать вопрос по теме нейросетей и получить ответ от ChatGPT.\n"
        "- **Генерация картинки**: Сгенерировать изображение с помощью нейросети на основе вашего текста.\n"
        "- **Моя история**: Просмотреть вашу историю запросов и ответов."
    )
    await message.reply(help_text)

@router.message(Command(commands=['history']))
async def history_handler(message: types.Message):
    user_id = message.from_user.id
    history = get_user_history(user_id)

    if history:
        for idx, (request_type, request_content, response_content, image_url, timestamp) in enumerate(history, 1):
            response_lines = (
                f"{idx}. [{timestamp}]\n"
                f"Тип запроса: {request_type}\n"
                f"Ваш запрос: {request_content}\n"
                f"Ответ: {response_content}\n"
            )
            await message.reply(response_lines)

            # Если есть изображение, отправляем его как фото
            if image_url:
                await message.reply_photo(photo=image_url)
    else:
        await message.reply("У вас пока нет сохраненной истории запросов.")

# Обработчик для "Генерация картинки"

@router.message(Form.generate_image)
async def handle_image_generation(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    image_description = message.text
    await message.answer("Генерирую изображение, пожалуйста, подождите...")

    image_url = generate_image(image_description)

    if image_url:
        await message.answer_photo(photo=image_url)

        # Сохраняем запрос, ответ и ссылку на изображение в базу данных
        save_user_history(
            user_id=user_id,
            request_type='image_generation',
            request_content=image_description,
            response_content="Изображение успешно сгенерировано.",
            image_url=image_url
        )
    else:
        error_message = "К сожалению, не удалось сгенерировать изображение. Пожалуйста, попробуйте снова позже."
        await message.answer(error_message)

        # Сохраняем неудачный запрос без ссылки на изображение
        save_user_history(
            user_id=user_id,
            request_type='image_generation',
            request_content=image_description,
            response_content=error_message
        )

    await state.set_state(Form.main_menu)


@router.callback_query(F.data.in_(['menu_neural', 'menu_ask', 'menu_image']), Form.main_menu)
async def process_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == 'menu_neural':
        await callback_query.message.edit_text(
            "Выберите категорию нейросетей:",
            reply_markup=categories_keyboard()
        )
        await state.set_state(Form.neural_categories)
    elif callback_query.data == 'menu_ask':
        await callback_query.message.edit_text("Введите ваш вопрос, и я передам его модели ChatGPT для ответа.")
        await state.set_state(Form.ask_question)
    elif callback_query.data == 'menu_image':
        await callback_query.message.edit_text("Введите описание изображения, которое вы хотите сгенерировать.")
        await state.set_state(Form.generate_image)
    await callback_query.answer()


@router.callback_query(F.data == 'back_to_main_menu')
async def back_to_main_menu_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        "Возвращение в главное меню. Пожалуйста, выберите опцию:",
        reply_markup=main_menu_keyboard()
    )
    await state.set_state(Form.main_menu)
    await callback_query.answer()

@router.callback_query(F.data == 'back_to_neural_categories', Form.neural_list)
async def back_to_neural_categories_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        "Выберите категорию нейросетей:",
        reply_markup=categories_keyboard()
    )
    await state.set_state(Form.neural_categories)
    await callback_query.answer()
@router.callback_query(F.data == 'back_to_neural_list', Form.neural_info)
async def back_to_neural_list_handler(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем сохраненную категорию из состояния
    user_data = await state.get_data()
    category = user_data.get('selected_category')

    # Проверяем, что категория существует, и загружаем соответствующие нейросети
    if category:
        networks = get_networks_by_category(category)  # Загрузка нейросетей из базы данных по категории
        
        # Создаем клавиатуру для выбора нейросетей в этой категории
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f'neural_network_{network_id}')] for network_id, name in networks
        ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text='Назад', callback_data='back_to_neural_categories')])
        
        await callback_query.message.edit_text(
            f"Доступные нейросети в категории '{category}':",
            reply_markup=keyboard
        )
        await state.set_state(Form.neural_list)  # Устанавливаем состояние обратно на список нейросетей
    else:
        await callback_query.message.edit_text("Не удалось загрузить список нейросетей.")
    
    await callback_query.answer()

def get_networks_by_category(category):
    """Извлекает нейросети из базы данных по категории."""
    conn = sqlite3.connect('ai_tools.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM tools WHERE category = ?", (category,))
    networks = cursor.fetchall()
    conn.close()
    return networks

@router.callback_query(F.data.startswith('neural_category_'), Form.neural_categories)
async def process_neural_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data.split('_')[-1]
    await state.update_data(selected_category=category)
    
    # Загружаем нейросети из базы данных для выбранной категории
    networks = get_networks_by_category(category)
    
    if networks:
        # Создаем клавиатуру с полученными нейросетями
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f'neural_network_{network_id}')] for network_id, name in networks
        ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text='Назад', callback_data='back_to_neural_categories')])
        
        await callback_query.message.edit_text(
            f"Доступные нейросети в категории '{category}':",
            reply_markup=keyboard
        )
        await state.set_state(Form.neural_list)
    else:
        await callback_query.message.edit_text(f"В категории '{category}' пока нет нейросетей.")
    await callback_query.answer()

def get_network_details(network_id):
    """Извлекает подробную информацию о нейросети по её ID."""
    conn = sqlite3.connect('ai_tools.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, instructions, link FROM tools WHERE id = ?", (network_id,))
    network = cursor.fetchone()
    conn.close()
    return network

@router.callback_query(F.data.startswith('neural_network_'), Form.neural_list)
async def process_neural_network(callback_query: types.CallbackQuery, state: FSMContext):
    network_id = int(callback_query.data.split('_')[-1])
    
    # Получаем данные нейросети из базы данных
    network = get_network_details(network_id)
    
    if network:
        name, description, instructions, link = network
        await callback_query.message.edit_text(
            f"<b>Название:</b> {name}\n"
            f"<b>Описание:</b> {description}\n"
            f"<b>Инструкции:</b> {instructions}\n"
            f"<b>Ссылка:</b> {link}",
            parse_mode='HTML',
            reply_markup=back_to_networks_keyboard()
        )
        await state.set_state(Form.neural_info)
    else:
        await callback_query.message.edit_text("Неверный выбор.")
    await callback_query.answer()

@router.callback_query(F.data == 'menu_history', Form.main_menu)
async def menu_history_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    history = get_user_history(user_id)

    if history:
        for idx, (request_type, request_content, response_content, image_url, timestamp) in enumerate(history, 1):
            response_lines = (
                f"{idx}. [{timestamp}]\n"
                f"Тип запроса: {request_type}\n"
                f"Ваш запрос: {request_content}\n"
                f"Ответ: {response_content}\n"
            )
            await callback_query.message.answer(response_lines)

            if image_url:
                await callback_query.message.answer_photo(photo=image_url)
    else:
        await callback_query.message.answer("У вас пока нет сохраненной истории запросов.")
    
    await callback_query.answer()


@router.message(Form.ask_question)
async def handle_user_question(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_question = message.text
    answer = ask_chatgpt(user_question)
    await message.answer(f"Ответ на ваш вопрос:\n{answer}")

    # Сохраняем вопрос и ответ в базу данных
    save_user_history(
        user_id=user_id,
        request_type='question',
        request_content=user_question,
        response_content=answer
    )

    # Сбрасываем состояние после ответа
    await state.set_state(Form.main_menu)

# Завершение всех async функций в соответствии с новой версией
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
