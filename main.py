
import os
import random
import sys

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import logging

import strings as st


# получение токена из переменной
def getToken() -> str:
    """Gets the Telegram bot token from the environment variable.

    If the environment variable is not set, a default token is used,
    which is not recommended for production use.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "7889987670:AAElMxjkMNhDUk-nXObnf1I-oqLU1Np1L-Y")
    if token == "7889987670:AAElMxjkMNhDUk-nXObnf1I-oqLU1Np1L-Y" and "TELEGRAM_BOT_TOKEN" not in os.environ:
        print("Warning: Using default token. It's recommended to set TELEGRAM_BOT_TOKEN environment variable for security.", file=sys.stderr)
    print("Token from getToken():", token)
    return token


# проверка на выигрыш
# проверяет нет ли победной комбинации в строчках, столбцах или по диагонали
# arr - массив
# who - кого надо проверить: нужно передать значение 'х' или '0'
def isWin(arr: str, who: str) -> bool:
    """Checks if the given player has won the Tic-Tac-Toe game.

    Args:
        arr (str): The current state of the game board (a string).
        who (str): The player to check ('x' or 'o').

    Returns:
        bool: True if the player has won, False otherwise.
    """

    if ((arr[0] == who and arr[1] == who and arr[2] == who)
        or (arr[3] == who and arr[4] == who and arr[5] == who)
        or (arr[6] == who and arr[7] == who and arr[8] == who)):
        return True

    if ((arr[0] == who and arr[3] == who and arr[6] == who)
            or (arr[1] == who and arr[4] == who and arr[7] == who)
            or (arr[2] == who and arr[5] == who and arr[8] == who)):
        return True

    if ((arr[0] == who and arr[4] == who and arr[8] == who)
            or (arr[2] == who and arr[4] == who and arr[6] == who)):
        return True

    return False


def countUndefinedCells(cellArray: str) -> int:
    """Counts the number of undefined cells on the board.

    Args:
        cellArray (str): The current state of the game board.

    Returns:
        int: The number of undefined cells.
    """
    counter = 0
    for i in cellArray:
        if i == st.SYMBOL_UNDEF:
            counter += 1
    return counter


game_states = {}
waiting_users = []


def game(users: tuple[int, int], buttonNumber: int) -> tuple[str, str | None, str | None]:
    """Implements the game logic for Tic-Tac-Toe for two players.

    Args:
        users: tuple containing the user ids
        buttonNumber: The callback data from the button click.

    Returns:
        tuple: A tuple containing (message, updated callback data, alert message (if any)).
    """
    message = None
    alert = None

    game_key = tuple(sorted(users))

    if game_key not in game_states:
        return "Ошибка: Состояние игры не найдено", None, None
    game_data = game_states.get(game_key)


    cellArray = list(game_data['board'])  
    currentPlayer = game_data['current_player']
    opponentPlayer = st.SYMBOL_O if currentPlayer == st.SYMBOL_X else st.SYMBOL_X

    if cellArray[buttonNumber] == st.SYMBOL_UNDEF:
        cellArray[buttonNumber] = currentPlayer

        
        if isWin("".join(cellArray), currentPlayer):  
            message = f"{st.ANSW_PLAYER_WIN.format(currentPlayer)}\n"
            message += '\n'
            for i in range(0, 3):
                message += '\n | '
                for j in range(0, 3):
                     message += cellArray[j + i * 3] + ' | '
            del game_states[game_key]  
        elif countUndefinedCells("".join(cellArray)) == 0:
            message = f"{st.ANSW_DRAW}\n"
            message += '\n'
            for i in range(0, 3):
                message += '\n | '
                for j in range(0, 3):
                     message += cellArray[j + i * 3] + ' | '
            del game_states[game_key]  
        else:
            
            currentPlayer = st.SYMBOL_O if currentPlayer == st.SYMBOL_X else st.SYMBOL_X
            message = st.ANSW_PLAYER_TURN.format(currentPlayer)
        
        if game_key in game_states:
            game_states[game_key]['board'] = "".join(cellArray)  
            game_states[game_key]['current_player'] = currentPlayer
    else:
        alert = st.ALERT_CANNOT_MOVE_TO_THIS_CELL

    return message, None, alert


# возвращает клавиатуру для бота
# на вход получает callBackData - данные с callBack-кнопки
def getKeyboard(board: str) -> list[list[InlineKeyboardButton]]:
    """Creates the keyboard for the Tic-Tac-Toe game.

    Args:
        board (str): The current state of the game board.

    Returns:
        list: A list of lists representing the keyboard buttons.
    """
    keyboard = [[], [], []]  # заготовка объекта клавиатуры, которая вернется

    # формирование объекта клавиатуры
    for i in range(0, 3):
        for j in range(0, 3):
            keyboard[i].append(
                InlineKeyboardButton(board[j + i * 3], callback_data=str(j + i * 3)))

    return keyboard


def newGame(update: telegram.update.Update, context: CallbackContext):
    """Starts a new game of Tic-Tac-Toe."""
    user_id = update.effective_user.id

    if user_id in waiting_users:
        update.message.reply_text(st.ANSW_ALREADY_IN_QUEUE)
        return

    waiting_users.append(user_id)
    update.message.reply_text(st.ANSW_WAITING_FOR_PARTNER)
    logging.info(f"User {user_id} added to queue.")


    if len(waiting_users) >= 2:
        try:
            user1 = waiting_users.pop(0)
            user2 = waiting_users.pop(0)
            logging.info(f"Users {user1}, {user2} matched.")

            startGame(user1, user2, context)
        except Exception as e:
             logging.error(f"Ошибка при поиске соперника: {e}")
             update.message.reply_text("Произошла ошибка при запуске игры. Пожалуйста, попробуйте снова.")



def startGame(user1: int, user2: int, context: CallbackContext):
    """Starts the game between two players"""
    board = ''
    for i in range(0, 9):
        board += st.SYMBOL_UNDEF
    currentPlayer = st.SYMBOL_X

    game_key = tuple(sorted((user1, user2)))
    game_states[game_key] = {"board": board, "current_player": currentPlayer}

    try:
        for user in (user1, user2):
            message = st.ANSW_PLAYER_TURN.format(currentPlayer) if user == user1 else st.ANSW_PLAYER_TURN.format(
                st.SYMBOL_O)
            context.bot.send_message(user, message, reply_markup=InlineKeyboardMarkup(getKeyboard(board)))
            logging.info(f"Игра начата для игроков {user1}, {user2}")
    except Exception as e:
        logging.error(f"Ошибка при запуске игры для игроков {user1}, {user2}: {e}")
        context.bot.send_message(user1, "Произошла ошибка при запуске игры. Пожалуйста, попробуйте снова.")
        context.bot.send_message(user2, "Произошла ошибка при запуске игры. Пожалуйста, попробуйте снова.")


def button(update: telegram.update.Update, context: CallbackContext):
    """Handles the button clicks during the game."""
    query = update.callback_query
    user_id = query.from_user.id

    buttonNumber = int(query.data)  
    game_users = None
    for key in game_states:  
        if user_id in key:
            game_users = key
            break

    if game_users:
        if game_users not in game_states:  
            query.answer(text="Игра закончилась. Пожалуйста, начните новую игру.", show_alert=True)
            try:
                for user in game_users:
                  context.bot.send_message(user, "Игра закончилась. Пожалуйста, начните новую игру с `/new_game`, если хотите сыграть ещё раз.")
            except Exception as e:
               logging.error(f"Ошибка при отправке сообщения о завершении игры: {e}")
            return  
        try:
            message, _, alert = game(game_users, buttonNumber)  # игра
            if alert is None:  # если не получен сигнал тревоги (alert==None), то редактируем сообщение и меняем клавиатуру
                query.answer()  # обязательно нужно что-то отправить в ответ, иначе могут возникнуть проблемы с ботом
                board = game_states.get(game_users).get('board', None) if game_states.get(game_users) else None

                if "выиграл" in message or "Ничья" in message:
                    for user in game_users:
                        context.bot.send_message(user, message)
                elif board:
                    for user in game_users:
                        context.bot.send_message(user, message, reply_markup=InlineKeyboardMarkup(getKeyboard(board)))
                else:
                    logging.error(f"Состояние доски не найдено. Сообщение: {message}")

            else:  # если получен сигнал тревоги (alert!=None), то отобразить сообщение о тревоге
                query.answer(text=alert, show_alert=True)
        except Exception as e:
             logging.error(f"Ошибка при обработке хода для игроков {game_users}: {e}", exc_info=True)
             query.answer(text="Произошла ошибка при обработке хода. Пожалуйста, попробуйте начать новую игру.", show_alert=True)
             try:
                  for user in game_users:
                       context.bot.send_message(user, f"Произошла ошибка при обработке хода, пожалуйста, попробуйте начать новую игру с `/new_game`, если хотите сыграть ещё раз.")
             except Exception as e:
                 logging.error(f"Ошибка при отправке сообщения игрокам {game_users}: {e}")
    else:
        query.answer(text="Игра не начата, используйте /new_game", show_alert=True)


def help_command(update, _):
    """Handles the /help command."""
    update.message.reply_text(st.ANSW_HELP)
    logging.info(f"User {update.effective_user.id} used the /help command")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    updater = Updater(getToken())  # получение токена из переменной и инициализация updater

    # добавление обработчиков
    updater.dispatcher.add_handler(CommandHandler('start', newGame))
    updater.dispatcher.add_handler(CommandHandler('new_game', newGame))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, help_command))  # обработчик на любое текстовое сообщение
    updater.dispatcher.add_handler(CallbackQueryHandler(button))  # добавление обработчика на CallBack кнопки

    # Запуск бота
    updater.start_polling()
    updater.idle()
