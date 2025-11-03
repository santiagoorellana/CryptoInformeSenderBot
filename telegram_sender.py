

# Consultado: https://docs.python-telegram-bot.org/en/stable/index.html
# Consultado: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API

import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from typing import Literal, Optional
import os
import time


MsgType = Literal["text", "photo", "photoUrl", "voice", "audio", "video", "document"]
TIMEOUT = 60
INSISTENCE_COUNT_MAX = 10
INSISTENCE_PAUSE_SECONDS = 6

RESULT_OK = 0
RESULT_ERROR_GENERIC = -1
RESULT_UNKNOWN_MESSAGE = 2
RESULT_FILE_NOT_FOUND = 3



async def _send(msgType:MsgType, botToken:str, receiver:str, text:Optional[str]=None, filename:Optional[str]=None, 
                title:Optional[str]=None, thumbFilename:Optional[str]=None,  #parseMode:str='HTML'
                protectContent:bool=True, timeout:int=60):
    try:
        bot = Bot(botToken)
        async with bot:
            if msgType == "text":
                await bot.send_message(
                    chat_id = receiver, 
                    text = text, 
                    #parse_mode = parseMode, 
                    protect_content = protectContent,
                    parse_mode=ParseMode.HTML
                )
                return RESULT_OK
            elif msgType == "photoUrl":
                await bot.send_photo(
                    chat_id = receiver, 
                    caption = text, 
                    photo = filename, 
                    #parse_mode = parseMode, 
                    protect_content = protectContent
                )
                return RESULT_OK
            else:
                if os.path.exists(filename):
                    thumb = open(thumbFilename,'rb') if thumbFilename is not None and os.path.exists(thumbFilename) else None
                    if msgType == "document":
                        await bot.send_document(
                            chat_id = receiver, 
                            caption = text, 
                            #parse_mode = parseMode, 
                            document = open(filename,'rb'), 
                            thumb = thumb, 
                            filename = title,
                            protect_content = protectContent,
                            read_timeout = timeout,
                            write_timeout = timeout,
                            connect_timeout = timeout,
                            pool_timeout = timeout
                        )
                        return RESULT_OK
                    elif msgType == "video":
                        await bot.send_video(
                            chat_id = receiver, 
                            caption = text, 
                            #parse_mode = parseMode, 
                            video = open(filename,'rb'), 
                            protect_content = protectContent,
                            pool_timeout = timeout,
                            read_timeout = timeout,
                            write_timeout = timeout,
                            connect_timeout = timeout
                        )
                        return RESULT_OK
                    elif msgType == "audio":
                        await bot.send_audio(
                            chat_id = receiver, 
                            caption = text, 
                            #parse_mode = parseMode, 
                            audio = open(filename,'rb'), 
                            thumb = thumb, 
                            title = title, 
                            protect_content = protectContent,
                            pool_timeout = timeout,
                            read_timeout = timeout,
                            write_timeout = timeout,
                            connect_timeout = timeout
                        )
                        return RESULT_OK
                    elif msgType == "voice":
                        await bot.send_voice(
                            chat_id = receiver, 
                            caption = text, 
                            #parse_mode = parseMode, 
                            voice = open(filename,'rb'), 
                            protect_content = protectContent,
                            pool_timeout = timeout,
                            read_timeout = timeout,
                            write_timeout = timeout,
                            connect_timeout = timeout
                        )
                        return RESULT_OK
                    elif msgType == "photo":
                        await bot.send_photo(
                            chat_id = receiver, 
                            caption = text, 
                            #parse_mode = parseMode, 
                            photo = open(filename, 'rb'), 
                            protect_content = protectContent,
                            pool_timeout = timeout,
                            read_timeout = timeout,
                            write_timeout = timeout,
                            connect_timeout = timeout
                        )
                        return RESULT_OK
                    else:
                        print('ERROR: No se reconoce el tipo de mensaje que intenta enviar a Telegram.')
                        return RESULT_UNKNOWN_MESSAGE
                else:
                    print(f'ERROR: No se encuentra el fichero: "{filename}"')
                    return RESULT_FILE_NOT_FOUND
    except Exception as e:
        print(f'ATENCION: Error conectando con Telegram. Exception: {str(e)}')
        return RESULT_ERROR_GENERIC



def send(msgType:MsgType, botToken:str, receiver:str, text:Optional[str]=None, filename:Optional[str]=None, 
        title:Optional[str]=None, thumbFilename:Optional[str]=None,   #parseMode:str='HTML'
        protectContent:bool=True, timeout:int=60):
    result = RESULT_ERROR_GENERIC
    for i in range(INSISTENCE_COUNT_MAX):
        if result == RESULT_ERROR_GENERIC:
            if i > 0:
                print(f"...reintento numero {i}")
            result = asyncio.run(
                _send(msgType, botToken, receiver, text, filename, title, thumbFilename, protectContent, timeout) #parseMode
            )
            time.sleep(INSISTENCE_PAUSE_SECONDS)
    if result != RESULT_OK:
        print(f"ERROR: No se pudo enviar la informacion ({msgType}) a Telegram.\n")
    return result == RESULT_OK



# Este es el código de pruebas para este script.
if __name__ == '__main__':
    TOKEN = 'TOKEN_DEL_BOT_QUE_REALIZA_EL_ENVIO'
    CHAT = "@IDENTIFICADOR_DEL_CANAL_O_USUARIO"     
    send("text", TOKEN, CHAT, "Esto es una prueba")


