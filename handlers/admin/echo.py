from aiogram import types
from loader import dp


@dp.message_handler(content_types=['video'])
async def get_video_id(message: types.Message):
    file_id = message.video.file_id

    # Logga chiqarish
    print(f"\n{'=' * 50}")
    print(f"VIDEO FILE_ID:")
    print(f"{file_id}")
    print(f"{'=' * 50}\n")

    # Userga ham yuborish
    await message.answer(f"✅ Video qabul qilindi!\n\nFile ID:\n<code>{file_id}</code>")


@dp.message_handler(content_types=['document'])
async def get_file_id(message: types.Message):
    file_id = message.document.file_id
    file_name = message.document.file_name
    await message.reply(
        f"Fayl nomi: {file_name}\n\nID: <code>{file_id}</code>",
        parse_mode="HTML"
    )