"""
boot.py gira PRIMA di code.py, una volta sola all'accensione/reset.
Serve a dichiarare un device USB HID "raw" in piu' rispetto a quello
standard della tastiera, cosi' il companion script sul PC puo' mandare
dati (stato musica, volume) senza interferire con la tastiera normale.

Dopo aver modificato boot.py serve un reset della scheda (non basta
salvare code.py) perche' i device USB si configurano solo all'avvio.
"""

import usb_hid

RAW_HID_REPORT_DESCRIPTOR = bytes((
    0x06, 0x60, 0xFF,  # Usage Page (Vendor Defined 0xFF60)
    0x09, 0x61,        # Usage (0x61)
    0xA1, 0x01,        # Collection (Application)
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x00,  #   Logical Maximum (255)
    0x75, 0x08,        #   Report Size (8)
    0x95, 0x20,        #   Report Count (32) -- deve combaciare col companion script
    0x09, 0x62,        #   Usage (0x62)
    0x81, 0x02,        #   Input (Data,Var,Abs)
    0x95, 0x20,        #   Report Count (32)
    0x09, 0x63,        #   Usage (0x63)
    0x91, 0x02,        #   Output (Data,Var,Abs)
    0xC0,              # End Collection
))

raw_hid_device = usb_hid.Device(
    report_descriptor=RAW_HID_REPORT_DESCRIPTOR,
    usage_page=0xFF60,
    usage=0x61,
    report_ids=(0,),
    in_report_lengths=(32,),
    out_report_lengths=(32,),
)

usb_hid.enable(
    (usb_hid.Device.KEYBOARD, usb_hid.Device.CONSUMER_CONTROL, raw_hid_device)
)
