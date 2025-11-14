import storage
from buttons import button_down_depressed, button_up_depressed


# xxx doc
# xxx add doc in readme about needing to hold down the up or down button during boot to be able to program
disable_logging = button_up_depressed() or button_down_depressed()
storage.remount("/", readonly=disable_logging)