import argparse
from random import choice
import re
import sys

import chess
import openai

MODEL = "gpt-3.5-turbo"
SAN_PATTERN = r"([Oo0](-[Oo0]){1,2}|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](\=[QRBN])?[+#]?(\s(1-0|0-1|1\/2-1\/2))?)"
SYMBOLS = {
    "K": "♔",
    "Q": "♕",
    "R": "♖",
    "B": "♗",
    "N": "♘",
    "P": "♙",
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
    ".": " ",
}


def render(board: chess.Board) -> str:
    board_lines = str(board).split("\n")
    n_lines = len(board_lines)
    board_chars = [list(line.replace(" ", "")) for line in board_lines]
    lines: list[str] = []
    for i, row in enumerate(board_chars):
        line = f"{n_lines - i}│ "
        line += " │ ".join([SYMBOLS.get(char, char) for char in row])
        line += " │"
        lines.append(line)
        if i < n_lines - 1:
            lines.append(" ├───┼───┼───┼───┼───┼───┼───┼───┤")
    if board.turn == chess.BLACK:
        lines.reverse()
    lines.insert(0, " ┌───┬───┬───┬───┬───┬───┬───┬───┐")
    lines.append(" └───┴───┴───┴───┴───┴───┴───┴───┘")
    lines.append("   a   b   c   d   e   f   g   h")
    return "\n".join(lines)


def get_user_move(board: chess.Board) -> chess.Move:
    san = input("\nYour next move: ")
    while True:
        if san == "quit":
            sys.exit()
        try:
            move = board.parse_san(san)
            return move
        except chess.InvalidMoveError:
            san = input("Not valid standard algebraic chess notation. Try again: ")
        except chess.IllegalMoveError:
            san = input("This move is illegal. Try again: ")
        except chess.AmbiguousMoveError:
            san = input("This move is ambiguous. Also state piece to move: ")


def get_ai_prompt(color: str, board_str: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": f"You are a chess bot playing as {color}. You reply with the optimal next move in standard algebraic chess notation on the first line and nothing else and on the second line an explanation of the move but without reprinting the board. The user will give you a chess board configuration, where each piece is represented by a single character. The uppercase letters represent the white pieces (K for king, Q for queen, R for rook, B for bishop, N for knight and P for pawn), while the corresponding lowercase letters represent the black pieces. The dots represent empty squares on the board. The ranks are numbered from 1 to 8, and the files are labeled from a to h.",
        },
        {"role": "assistant", "content": "Ok."},
        {
            "role": "user",
            "content": board_str,
        },
    ]


def send_ai_prompt(prompt: list[dict[str, str]]) -> str:
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=prompt,
    )
    return response["choices"][0]["message"]["content"]


def get_ai_move(board: chess.Board, max_tries: int) -> chess.Move:
    color = "white" if board.turn == chess.WHITE else "black"
    prompt = get_ai_prompt(color, str(board))
    for _ in range(max_tries):
        reply = send_ai_prompt(prompt)
        try:
            san = next(re.finditer(SAN_PATTERN, reply)).group()
            move = board.parse_san(san)
            print("\n".join([line for line in reply.splitlines()[1:] if line != ""]))
            return move
        except StopIteration:
            continue
        except ValueError:
            continue
    print("AI did not make a valid move.")
    return chess.Move.null()


def authenticate() -> None:
    if openai.api_key is None:
        print("OpenAI API key not found in environment variable 'OPENAI_API_KEY'.")
        openai.api_key = input("Enter your OpenAI key manually: ")
    try:
        openai.Model.retrieve(MODEL)
    except openai.error.AuthenticationError as err:
        print(err)
        sys.exit()


def main() -> None:
    # read api key
    authenticate()

    print("\n")
    # argument parsing
    parser = argparse.ArgumentParser(
        prog="chessGPT", description="Play chess against GPT in the terminal."
    )
    parser.add_argument(
        "-w",
        "--white",
        action="store_true",
        help="start as white otherwise determines sides randomly",
    )
    parser.add_argument(
        "-t",
        "--tries",
        default=1,
        help="maximum number of tries for AI to generate a valid move, makes no move otherwise",
    )
    args = parser.parse_args()

    # setup board
    board = chess.Board()
    user_side = chess.WHITE if args.white else choice((chess.WHITE, chess.BLACK))

    # starting user move
    if user_side == chess.WHITE:
        print(render(board))
        board.push(get_user_move(board))

    # game loop
    while not board.is_game_over():
        board.push(get_ai_move(board, args.tries))
        print(render(board))
        board.push(get_user_move(board))

    # print outcome
    winner = board.outcome().winner
    if winner is None:
        print("It's a draw.")
    elif winner == user_side:
        print("You won!")
    else:
        print("You lost.")


if __name__ == "__main__":
    main()
