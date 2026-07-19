import time
import board
import busio
import displayio
import terminalio
import usb_hid

from adafruit_display_text import label
import adafruit_displayio_ssd1306

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.matrix import DiodeOrientation
from kmk.modules import Module
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.rgb import RGB

keyboard = KMKKeyboard()

# ---- matrix: pin confermati dal netlist ----
# righe = D0,D1,D2 -- colonne = D3,D7,D8
keyboard.row_pins = (board.D0, board.D1, board.D2)
keyboard.col_pins = (board.D3, board.D7, board.D8)
keyboard.diode_orientation = DiodeOrientation.ROW2COL

# il pulsante dell'encoder e' scollegato (D13 rimosso, S1/S2 unconnected
# nel netlist), quindi la matrice e' solo i 9 switch reali.
# ordine fisico reale sul PCB (riga per riga, sinistra->destra):
#   riga D0: SW11(col D3), SW12(col D7), SW13(col D8)
#   riga D1: SW14(col D7), SW15(col D8), SW16(col D3)  -- occhio, non in ordine elettrico!
#   riga D2: SW17(col D3), SW18(col D7), SW19(col D8)
keyboard.keymap = [
    [
        KC.N1,  KC.N2,  KC.N3,    # riga D0: col D3, D7, D8 = SW11, SW12, SW13
        KC.N6,  KC.N4,  KC.N5,    # riga D1: col D3, D7, D8 = SW16, SW14, SW15
        KC.N7,  KC.N8,  KC.N9,    # riga D2: col D3, D7, D8 = SW17, SW18, SW19
    ]
]

# ---- encoder: ruotandolo avanti/indietro cerca nel brano ----
# nessun pulsante gestito
encoder_handler = EncoderHandler()
encoder_handler.pins = ((board.D9, board.D10, None),)  # (A, B, pulsante=None)
encoder_handler.map = [((KC.MRWD, KC.MFFD),)]
keyboard.modules.append(encoder_handler)

# ---- retroilluminazione, 9 SK6812 in catena ----
rgb = RGB(pixel_pin=board.D10, num_pixels=9, val_limit=100)
keyboard.extensions.append(rgb)

# ---- OLED ----
# SDA = D4 = PA08, SCL = D5 = PA09 -- confermati dalle etichette sullo schematic
displayio.release_displays()
i2c = busio.I2C(board.D5, board.D4)  # SCL, SDA
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)

splash = displayio.Group()
display.root_group = splash

title_label = label.Label(terminalio.FONT, text="No player", x=0, y=6)
bar_label = label.Label(terminalio.FONT, text="", x=0, y=20)
splash.append(title_label)
splash.append(bar_label)


def draw_bar(percent, width=16):
    filled = int(max(0, min(100, percent)) / 100 * width)
    return "#" * filled + "-" * (width - filled)


# ---- raw HID: deve essere dichiarato in boot.py, qui lo recuperiamo ----
raw_hid = None
for device in usb_hid.devices:
    if getattr(device, "usage_page", None) == 0xFF60 and getattr(device, "usage", None) == 0x61:
        raw_hid = device
        break

media_state = {"playing": False, "track_percent": 0, "volume_percent": 0, "title": ""}


class MediaDisplay(Module):
    """Legge i pacchetti raw HID dal companion script e aggiorna l'OLED.
    Gestisce anche la finestra 'mostra il volume' dopo il click dell'encoder."""

    def __init__(self):
        self.volume_view_until = 0
        self.last_hid_packet = 0
        self.hid_timeout_ms = 3000
        self.volume_view_ms = 2000
        self.last_update = 0

    def during_bootup(self, keyboard):
        return

    def before_matrix_scan(self, keyboard):
        now = time.monotonic() * 1000

        # click sull'encoder -> mostra il volume per un po'
        for key in keyboard.keys_pressed:
            if key == KC.MUTE:
                self.volume_view_until = now + self.volume_view_ms

        self._read_hid(now)

        # aggiorna l'OLED al massimo 10 volte al secondo, non ad ogni scan
        if now - self.last_update > 100:
            self._update_oled(now)
            self.last_update = now

        return

    def after_matrix_scan(self, keyboard):
        return

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return

    def _read_hid(self, now):
        global raw_hid
        if raw_hid is None:
            return
        report = raw_hid.get_last_received_report()
        if not report:
            return
        media_state["playing"] = bool(report[0])
        media_state["track_percent"] = report[1]
        media_state["volume_percent"] = report[2]
        raw_title = bytes(report[3:19]).split(b"\x00")[0]
        media_state["title"] = raw_title.decode("utf-8", "ignore")
        self.last_hid_packet = now

    def _update_oled(self, now):
        hid_alive = (now - self.last_hid_packet) < self.hid_timeout_ms
        show_volume = now < self.volume_view_until

        if show_volume:
            title_label.text = "Volume"
            bar_label.text = draw_bar(media_state["volume_percent"])
        elif not hid_alive:
            title_label.text = "No player"
            bar_label.text = ""
        else:
            title_label.text = (media_state["title"] or "Playing")[:16]
            if media_state["playing"]:
                bar_label.text = draw_bar(media_state["track_percent"])
            else:
                bar_label.text = "paused"


keyboard.modules.append(MediaDisplay())

if __name__ == "__main__":
    keyboard.go()
