import AppKit
import objc
import logging
from Foundation import NSObject

logging.basicConfig(level=logging.DEBUG)

#D001
class PopupButtonAction(NSObject): 

#D002
    def initWithCallback_(self, callback):
        self.callback = callback
        return self

#D003
    def buttonClicked_(self, sender):
        logging.debug("PopupButtonAction.buttonClicked_ called")
        self.callback(sender)
        sender.window().orderOut_(sender)
    buttonClicked_ = objc.selector(buttonClicked_, signature=b"v@:@")

#E001
class PopupMessage(object):

#E002
    def __init__(self, message, x, y, callback, width=200, height=120):
        logging.debug("Initializing PopupMessage")

        frame = ((x, y), (width, height))
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(frame, AppKit.NSWindowStyleMaskBorderless, AppKit.NSBackingStoreBuffered, False)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self.window.setLevel_(1001)

        popup_view = AppKit.NSView.alloc().initWithFrame_(frame)
        popup_view.setWantsLayer_(True)
        popup_view.layer().setBackgroundColor_(AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(252/255, 248/255, 203/255, 1.0).CGColor())
        popup_view.layer().setBorderColor_(AppKit.NSColor.blackColor().CGColor())
        popup_view.layer().setBorderWidth_(2.0)
        popup_view.layer().setCornerRadius_(10.0)

        text_frame = ((10, (height - 40) / 2), (width - 20, 20))
        text_view = AppKit.NSTextView.alloc().initWithFrame_(text_frame)
        text_view.setString_(message)
        text_view.setEditable_(False)
        text_view.setSelectable_(False)
        text_view.setBackgroundColor_(AppKit.NSColor.clearColor())
        text_view.setAlignment_(AppKit.NSCenterTextAlignment)
        text_view.setFont_(AppKit.NSFont.systemFontOfSize_(14))
        popup_view.addSubview_(text_view)

        button_frame = ((width - 35, height - 35), (20, 20))
        button = AppKit.NSButton.alloc().initWithFrame_(button_frame)
        button.setTitle_("X")
        button.setBordered_(False)
        button.setButtonType_(AppKit.NSButtonTypeMomentaryChange)
        button.setBezelStyle_(AppKit.NSBezelStyleCircular)
        self.buttonAction = PopupButtonAction.alloc().initWithCallback_(callback)
        button.setTarget_(self.buttonAction)
        button.setAction_("buttonClicked:")
        popup_view.addSubview_(button)

        self.window.setContentView_(popup_view) 
        self.window.orderFrontRegardless()
        logging.debug("Ordered popup window to front")

#E003
    def buttonClicked_(self, sender):
        logging.debug("PopupMessage.buttonClicked_ called")
        self.window.orderOut_(sender)
        self.window.close()