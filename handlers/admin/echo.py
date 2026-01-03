from aiogram import types
from loader import dp


@dp.message_handler(content_types=['document'])
async def get_file_id(message: types.Message):
    file_id = message.document.file_id
    file_name = message.document.file_name
    await message.reply(
        f"Fayl nomi: {file_name}\n\nID: <code>{file_id}</code>",
        parse_mode="HTML"
    )