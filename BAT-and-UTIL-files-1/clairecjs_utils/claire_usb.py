import hid


import usb.core
import usb.backend.libusb1



import logging as logging
for handler in logging.root.handlers[:]: logging.root.removeHandler(handler)
logging.basicConfig(
    level=logging.WARNING,
    format='\t\t[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)
#logger.setLevel(logging.WARNING)
logger.debug("clairecjs_usb started")




def display_all_devices():
    # Find all devices
    devices = usb.core.find(find_all=True)

    #backend = usb.backend.libusb1.get_backend(find_library=lambda x: "libusb-1.0.dll")
    #devices = usb.core.find(find_all=True, backend=backend)
    #for device in devices:
    #    print(f"Device: {device}")
    #    print(f"  Vendor ID: {hex(device.idVendor)}")
    #    print(f"  Product ID: {hex(device.idProduct)}")
    #    print(f"  Serial Number: {usb.util.get_string(device, 256, device.iSerialNumber)}\n")

def list_usb_devices():
    import pywinusb.hid as hid
    all_devices = hid.find_all_hid_devices()
    for device in all_devices:
        print(f"Device: {          device.product_name}")
        print(f"       Vendor ID: {device.vendor_id   }")
        print(f"     P roduct ID: {device.product_id  }")
        print(f"    Manufacturer: {device.product_name}")

list_usb_devices()


if __name__ == "__main__":
    # List all devices
    for device in hid.enumerate(): print(device)


    #display_all_devices()
