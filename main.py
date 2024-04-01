import random
import time
import glob
import objc
import logging
from Quartz import CGShieldingWindowLevel

from AppKit import NSNormalWindowLevel

from PyObjCTools import AppHelper
from messages import messages
from AppKit import (NSApplication, NSColor, NSFullSizeContentViewWindowMask,
                    NSImage, NSImageView, NSWindow, NSBorderlessWindowMask,
                    NSWindowCollectionBehaviorCanJoinAllSpaces, NSWindowCollectionBehaviorFullScreenAuxiliary)
from Quartz import CGDisplayPixelsWide, CGDisplayPixelsHigh, CGMainDisplayID
from Foundation import NSObject, NSTimer
from popup import PopupMessage

# Configure logging to display messages in the console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

#A001
def calculate_velocity(previous_location, current_location, previous_time, current_time):
    # Calculate the x and y velocities and return them as a tuple
    # Catch any ZeroDivisionError that might occur if the times are the same
    try:
        x_velocity = (current_location.x - previous_location.x) / (current_time - previous_time)
        y_velocity = (current_location.y - previous_location.y) / (current_time - previous_time)
        return -x_velocity, -y_velocity
    except ZeroDivisionError:
        logging.error("Caught ZeroDivisionError in calculate_velocity")
        return 0, 0

#B001
class ClickAndDragWindow(NSWindow):
    current_image_index = objc.ivar()
    popup_active = objc.ivar()
    popup = objc.ivar()

    #B002
    def initWithImages_(self, image_sequence):
        logging.debug("Initializing ClickAndDragWindow with image sequence")

        # Validate the image_sequence argument
        if not isinstance(image_sequence, list) or not all(isinstance(image, NSImage) for image in image_sequence):
            logging.error("Invalid image sequence")
            return None

        self.image_sequence = image_sequence
        self.current_image_index = 0
        self.popup_active = False
        return self

    #B003
    def next_image(self):
        # Increment current_image_index and wrap around to 0 if it reaches the length of the image sequence
        self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)

        # Try to set the image and log an error if it fails
        try:
            self.contentView().setImage_(self.image_sequence[self.current_image_index])
        except Exception as e:
            logging.error(f"Failed to set image: {e}")
    next_image = objc.selector(next_image)

    #B004
    def mouseDownCanMoveWindow(self):
        return False

    #B005
    def mouseDown_(self, event):
        logging.debug("ClickAndDragWindow.mouseDown_ called")
        logging.debug(f"popup_active is {self.popup_active}")

        if self.popup_active:
            return

        # Record the initial location of the mouse and the current time
        self.initial_location = event.locationInWindow()
        self.previous_time = time.time()
        self.previous_location = event.locationInWindow()
        self.dragged = False

    #B006
    def mouseDragged_(self, event):
        logging.debug("ClickAndDragWindow.mouseDragged_ called")
        logging.debug(f"popup_active is {self.popup_active}")

        if self.popup_active:
            return

        self.dragged = True

        # Calculate the new location of the window and move it there
        screen_location = self.frame().origin
        current_location = event.locationInWindow()
        new_location = (screen_location.x + (current_location.x - self.initial_location.x),
                        screen_location.y + (current_location.y - self.initial_location.y))
        self.setFrameOrigin_(new_location)

        # Calculate the velocity of the mouse movement
        current_time = time.time() # Fetch current time here
        self.velocity = calculate_velocity(self.previous_location, current_location, self.previous_time, current_time)
        self.previous_location = current_location
        self.previous_time = current_time
        self.updateEyePositions()

        if hasattr(self, 'myWindow'):
            self.myWindow.updateEyePositions()

    #B007
    def create_new_window(self):
        try:
            app = NSApplication.sharedApplication()

            # Get the current location of the pet window
            current_location = self.frame().origin
            x, y = current_location.x, current_location.y

            # Set the frame to the current location of the pet window
            frame = ((x, y), (200.0, 200.0))  # Adjust the frame size here

            window = MyWindow.alloc().initWithContentRect_styleMask_backing_defer_(frame, NSBorderlessWindowMask, 0, False)
            window.setLevel_(CGShieldingWindowLevel())  # Set window level here
            window.makeKeyAndOrderFront_(None)
            window.acceptsMouseMovedEvents = True
            timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.1, window, window.mouseDidMove_, None, True)
            AppHelper.runEventLoop()
            return window  # Return the window instance
        except Exception as e:
            logging.error("Exception occurred in create_new_window: {}".format(str(e)))



    #B009
    def remove_popup(self, sender):
        logging.debug("ClickAndDragWindow.remove_popup called")

        # Remove the popup and set popup_active to False
        try:
            sender.window().orderOut_(sender)
            self.popup_active = False
            self.popup = None
        except Exception as e:
            logging.error(f"Failed to remove popup: {e}")
        logging.debug(f"popup_active is now {self.popup_active}")

    #B010
    @objc.typedSelector(b'v@:@')
    def showPopupMessage_(self, timer):
        logging.debug("ClickAndDragWindow.showPopupMessage_ called")

        if not self.popup_active:
            # Set popup_active to True immediately
            self.popup_active = True
            logging.debug(f"popup_active is now {self.popup_active}")

            # Create a new popup message with the current location of the window
            try:
                x, y = self.frame().origin.x, self.frame().origin.y - 50  # Decrease y value to spawn the popup lower
                message = random.choice(messages)  # Select a random message
                self.popup = PopupMessage(message, x, y, callback=self.remove_popup)
            except Exception as e:
                logging.error(f"Failed to create popup: {e}")
                self.popup_active = False

    def throw_window(self):
        logging.debug("ClickAndDragWindow.throw_window called")

        # Calculate the distance to throw the window and the size of the screen and the window
        throw_distance = 5
        screen_width = CGDisplayPixelsWide(CGMainDisplayID())
        screen_height = CGDisplayPixelsHigh(CGMainDisplayID())
        image_width = self.contentView().frame().size.width
        image_height = self.contentView().frame().size.height
        current_location = self.frame().origin

        # Calculate the target location for the window
        target_x = min(max(current_location.x + self.velocity[0] * throw_distance, 0), screen_width - image_width)
        target_y = min(max(current_location.y + self.velocity[1] * throw_distance, 0), screen_height - image_height)

        # Set up the timer info for the animation
        steps = 30
        self.timer_info = {
            "step": 0,
            "steps": steps,
            "current_location": current_location,
            "target": (target_x, target_y),
        }

        # Create and start a timer to animate the throw
        try:
            self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.01,  # time interval between timer fires
                self,  # target
                objc.selector(b"animate:", signature="v@:@"),  # selector
                None,  # user info
                True,  # repeats
            )
        except Exception as e:
            logging.error(f"Failed to create timer: {e}")

def animate_(self, timer):
    logging.debug("ClickAndDragWindow.animate_ called")

    # Calculate the new location for the window and move it there
    new_x = self.timer_info["current_location"].x + (self.timer_info["target"][0] - self.timer_info["current_location"].x) * self.timer_info["step"] / self.timer_info["steps"]
    new_y = self.timer_info["current_location"].y + (self.timer_info["target"][1] - self.timer_info["current_location"].y) * self.timer_info["step"] / self.timer_info["steps"]
    self.setFrameOrigin_((new_x, new_y))

    # If the animation is complete, invalidate the timer and set it to None
    if self.timer_info["step"] == self.timer_info["steps"]:
        self.timer.invalidate()
        self.timer = None
    else:
        # Otherwise, increment the step count
        self.timer_info["step"] += 1

def throw_window(self):
    logging.debug("ClickAndDragWindow.throw_window called")

    # Calculate the distance to throw the window and the size of the screen and the window
    throw_distance = 5
    screen_width = CGDisplayPixelsWide(CGMainDisplayID())
    screen_height = CGDisplayPixelsHigh(CGMainDisplayID())
    image_width = self.contentView().frame().size.width
    image_height = self.contentView().frame().size.height
    current_location = self.frame().origin

    # Calculate the target location for the window
    target_x = min(max(current_location.x + self.velocity[0] * throw_distance, 0), screen_width - image_width)
    target_y = min(max(current_location.y + self.velocity[1] * throw_distance, 0), screen_height - image_height)

    # Set up the timer info for the animation
    steps = 30
    self.timer_info = {
        "step": 0,
        "steps": steps,
        "current_location": current_location,
        "target": (target_x, target_y),
    }

    # Create and start a timer to animate the throw
    try:
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.01,  # time interval between timer fires
            self,  # target
            objc.selector(b"animate:", signature="v@:@"),  # selector
            None,  # user info
            True,  # repeats
        )
    except Exception as e:
        logging.error(f"Failed to create timer: {e}")

#B013
def create_hovering_window():
    logging.debug("Creating hovering window")

    # Load the image sequence
    try:
        image_files = sorted(glob.glob("images/idle_ani/*.png"))
        image_sequence = [NSImage.alloc().initWithContentsOfFile_(image_file) for image_file in image_files]
    except Exception as e:
        logging.error(f"Failed to load images: {e}")
        return None
    logging.debug(f"Image sequence length: {len(image_sequence)}")

    logging.debug("Allocating ClickAndDragWindow")
    rect = ((500, 500), (200, 200))

    # Create and initialize the ClickAndDragWindow
    try:
        window = ClickAndDragWindow.alloc().initWithContentRect_styleMask_backing_defer_(rect, 0, 2, False)
        window = window.initWithImages_(image_sequence)
        window.setLevel_(CGShieldingWindowLevel())  # Set window level here
        window.orderFrontRegardless()
        window.makeKeyAndOrderFront_(None)

    except Exception as e:
        logging.error(f"Failed to create window: {e}")
        return None

    # Set up the window and its content view
    try:
        window.setBackgroundColor_(NSColor.clearColor())
        window.setOpaque_(False)
        window.setLevel_(1000)
        window.makeKeyAndOrderFront_(None)

        image_view = NSImageView.alloc().initWithFrame_(((0, 0), (200, 200)))
        image_view.setImage_(image_sequence[0])
        image_view.setAnimates_(True)
        window.setContentView_(image_view)

        # Position the window in the top-right corner of the screen
        screen_width = CGDisplayPixelsWide(CGMainDisplayID())
        screen_height = CGDisplayPixelsHigh(CGMainDisplayID())
        window_width = window.contentView().frame().size.width
        window_height = window.contentView().frame().size.height
        new_x = screen_width - window_width
        new_y = screen_height - window_height
        window.setFrameOrigin_((new_x, new_y))
    except Exception as e:
        logging.error(f"Failed to set up window: {e}")
        return None

    logging.debug("Hovering window creation successful")
    return window

#C001
def main():
    try:
        logging.debug("Initializing application")
        app = NSApplication.sharedApplication()
        window = create_hovering_window()

        # Check if the window was created successfully
        if window is None:
            logging.error("Failed to create window")
            return

        # Create and start the timers for the animation and popup messages
        try:
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.05, window, "next_image", None, True)
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(10.0, window, "showPopupMessage:", None, True)
        except Exception as e:
            logging.error(f"Failed to create timers: {e}")
            return

        # Spawn eye following code
        #try:
        #    eye_window = window.create_new_window()  # This should return the instance of MyWindow
        #    eye_follower = EyeFollow(eye_window)
        #    eye_window.makeKeyAndOrderFront_(None)
        #    eye_window.orderFrontRegardless()
        #except Exception as e:
        #   logging.error(f"Failed to run eye_follow: {e}")

        # Start the application event loop
        app.run()
    except Exception as e:
        logging.error(f"Exception occurred during application initialization: {e}")

if __name__ == "__main__":
    main()
