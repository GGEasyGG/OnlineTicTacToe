"""A module with a game search page class, as well as a circular search indicator class and a timer class."""

import time
import tkinter as tk
import tkinter.font as tkfont
import threading
from typing import Dict
import requests
import setting_page as setp
import game_page as gp


class TimeCounter(tk.Label):
    """
       The timer class.

       :param parent: Object of the `SearchGamePage` class
       :type parent: class: `SearchGamePage`
       :param font: The font style for the timer
       :type font: class: `tkinter.font.Font`
       :param *args: Positional arguments
       :param **kwargs: Named arguments
       """

    def __init__(self, parent: 'SearchGamePage', font: tkfont.Font, *args, **kwargs) -> None:
        """Constructor method."""
        super().__init__(parent, *args, **kwargs)
        self.font: tkfont.Font = font
        self.total_seconds: int = 0
        self.update_text()

    def start(self) -> None:
        """The method that starts the timer."""
        self.total_seconds = 0
        self.update_text()
        self.run()

    def run(self) -> None:
        """A method that updates the time on the timer every second."""
        self.total_seconds += 1
        self.update_text()
        self.after(1000, self.run)

    def update_text(self) -> None:
        """A method that updates the text on a widget with a timer."""
        minutes, seconds = divmod(self.total_seconds, 60)
        self.config(text=f"{minutes:02d}:{seconds:02d}", font=self.font)


class CircularWaitingIndicator(tk.Canvas):
    """
        The class of the circular game search indicator.

        :param parent: Object of the `SearchGamePage` class
        :type parent: class: `SearchGamePage`
        :param width: Width of the circular game search indicator, defaults to 80
        :type width: class: `int`
        :param height: Height of the circular game search indicator, defaults to 80
        :type height: class: `int`
        :param color: Color of the circular game search indicator, defaults to "blue"
        :type color: class: `str`
        :param thickness: Thickness of the circular game search indicator, defaults to 5
        :type thickness: class: `int`
        :param speed: Speed of the circular game search indicator, defaults to 5
        :type speed: class: `int`
        """

    def __init__(self, parent: 'SearchGamePage', width: int = 80, height: int = 80, color: str = 'blue',
                 thickness: int = 5, speed: int = 5) -> None:
        """Constructor method."""
        super().__init__(parent, width=90, height=90)
        self.color: str = color
        self.thickness: int = thickness
        self.speed: int = speed

        self.create_oval(10, 10, width, height, outline=color, width=thickness)
        self.arc: int = self.create_arc(10, 10, width, height, start=90, extent=0, outline=color, width=thickness)

        self.update_animation()

    def update_animation(self) -> None:
        """The method that makes the circular game search indicator spin."""
        extent = (float(self.itemcget(self.arc, 'extent')) - self.speed) % 360
        self.itemconfigure(self.arc, extent=extent)
        self.after(50, self.update_animation)


class SearchGamePage(tk.Frame):
    """
       The class of the game search page.

       :param master: An instance of the main class of the game application
       :type master: class: `tictactoe.App`
       """

    def __init__(self, master) -> None:
        """Constructor method."""
        super().__init__(master)

        self.master.cur_page = 'Search'

        self.reset: bool = False

        self.configure(height=320, width=450)
        self.pack_propagate(False)

        self.warning_message: tk.Label = tk.Label()
        self.button: tk.Button = tk.Button()

        self.label1: tk.Label = tk.Label()

        self._create_widgets()

        self.thread: threading.Thread = threading.Thread(target=self.is_searched, daemon=True)
        self.thread.start()

    def is_searched(self) -> None:
        """A method that, in a separate thread, asks the server every 5 seconds if the game has been found."""
        flag = True

        while flag:
            if self.reset:
                break

            url = 'http://localhost:5000/is_game_searched'
            response = requests.get(url, cookies=self.master.token)

            if response.json()['message'] == 'Game is not searched yet':
                time.sleep(5)
                continue

            if response.json()['message'] == 'Success':
                flag = False
                self.after(0, lambda: self.game_ready({'message': 'Success', 'opponent': response.json()['opponent'],
                                                       'game_id': response.json()['game_id']}))

    def game_ready(self, data: Dict[str, str]) -> None:
        """
                A method that triggers when a game is found and switches the interface to the game page.

                :param data: Dictionary with game data
                :type data: class: `dict[str, str]`
                """
        if not self.master.mute_flag:
            self.master.background_music.set_volume(0)
        self.master.find_music.play()
        self.warning_message.config(text='The game is ready')
        self.button.config(state="disabled")

        self.master.game_id = data['game_id']

        self.after(2600, lambda: self.master.switch_frame(gp.FriendGame))

    def reset_search(self) -> None:
        """Method with action for the "Reset search" button."""
        url = 'http://localhost:5000/reset_search'
        requests.get(url, cookies=self.master.token)
        self.reset = True
        self.master.switch_frame(setp.FriendStartPage)

    def _create_widgets(self) -> None:
        """The method of rendering widgets of the game search page."""
        self.label1 = tk.Label(self, font=self.master.font, text='The game is being searched for')
        self.label1.pack(side="top", pady=(15, 30))

        indicator = CircularWaitingIndicator(self)
        indicator.pack(side="top", pady=(0, 30))

        counter = TimeCounter(self, self.master.font)
        counter.pack(side="top", pady=(0, 20))
        counter.start()

        frame = tk.Frame(self)
        frame.pack(side="top", pady=(0, 20))

        self.warning_message = tk.Label(frame, font=self.master.font, text='', fg='green')
        self.warning_message.pack()

        self.button = tk.Button(self, bg="white", font=self.master.btn_font, text="Reset search", width=30,
                                command=self.reset_search)
        self.button.pack(side='top')
