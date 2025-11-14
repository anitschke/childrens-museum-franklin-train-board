import board
from digitalio import DigitalInOut, Pull

# Configure buttons to pull up. This means that by default they will have a
# value of True and when pressed will get a value of False. I tried configuring
# them the other way around so we get a value of true when pressed but they must
# be normally closed or something, because it didn't work, I don't really
# understand.
# 
# To work around this we will just setup a lambda that tells us if it is
# currently depressed.
# 
# Ideally we would use hardware interrupts or something to keep track of if it
# has been pressed but it seems like that isn't possible. It seems like the
# right way to do this would be to use async to allow monitoring the button
# while we are still scrolling the text. But this adds a lot of complexity to
# the code. So we will just make it so you need to be holding down the button
# when we happen to check.
button_down = DigitalInOut(board.BUTTON_DOWN)
button_down.switch_to_input(pull=Pull.UP)
button_down_depressed = lambda : not button_down.value
button_up = DigitalInOut(board.BUTTON_UP)
button_up.switch_to_input(pull=Pull.UP)
button_up_depressed = lambda : not button_up.value