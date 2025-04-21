import qrcode
from PIL import Image
import io
import base64
from colorama import Fore, Style, init
from pyzbar.pyzbar import decode

# Initialize colorama
init(autoreset=True)

class QRCode:
    """
    QRCode is a utility class for generating QR codes with optional embedded logos and for scanning barcodes from images.
    It supports saving the QR code either as an image file or as a base64-encoded string in a text file, 
    and can also decode QR codes and barcodes from images.
    
    Usage:
        qrcode = QRCode()
        
        # Generate QR code and save as PNG
        result = qrcode.generate_qrcode(
            filename="output.png", 
            logo_path="logo.png", 
            data="https://www.example.com", 
            save_as_png=True
        )
        print(result)  # Output: QR code has been saved as output.png
        
        # Generate QR code and save as base64 string in a text file
        result = qrcode.generate_qrcode(
            filename="output.png", 
            logo_path="logo.png", 
            data="https://www.example.com", 
            save_as_png=False
        )
        print(result)  # Output: QR code string has been saved as output.txt

        # Scan QR code or barcode from an image
        result = qrcode.scan_image("barcode_or_qrcode.png")
        print(result)  # Output: Decoded data from the image
    """

    def generate_qrcode(self, filename=None, logo_path=None, data=None, save_as_png=True):
        if data is None:
            data = ''
        if filename is None and save_as_png is True:
            filename = "qrcode.png"

        # Check if logo_path is provided and is a PNG file
        if logo_path and not logo_path.endswith('.png'):
            raise ValueError(Fore.RED + Style.BRIGHT + 'logo_path must end with .png!')

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Create an image from the QR code instance
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        if logo_path:
            # Load the logo image
            logo = Image.open(logo_path)

            # Ensure the logo has a white background (in case of transparency)
            logo = logo.convert("RGBA")
            white_background = Image.new("RGBA", logo.size, "WHITE")
            logo = Image.alpha_composite(white_background, logo).convert("RGBA")

            # Calculate the logo size relative to the QR code
            logo_size = int(min(img.size) / 4)

            # Resize the logo
            logo = logo.resize((logo_size, logo_size))

            # Calculate the position to place the logo at the center
            logo_position = (
                (img.size[0] - logo_size) // 2,
                (img.size[1] - logo_size) // 2
            )

            # Paste the logo image onto the QR code, with a mask to handle transparency
            img.paste(logo, logo_position, mask=logo)

        if save_as_png:
            # Save the final QR code image
            img.save(filename)
            return filename
        else:
            # Convert the image to a byte stream
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")

            # Encode the byte stream to base64
            image_string = base64.b64encode(buffered.getvalue()).decode("utf-8")


            return image_string

    def scan_qrcode(self, image_path):
        """
        Scans a barcode or QR code from an image and returns the decoded data.
        
        Args:
            image_path (str): Path to the image file containing the barcode or QR code.
        
        Returns:
            str: The decoded data from the image.
        """
        try:
            # Open the image file
            img = Image.open(image_path)
            
            # Decode the QR code
            decoded_objects = decode(img)
            
            if not decoded_objects:
                return "No QR code detected."
            
            # Return the decoded data
            results = [obj.data.decode('utf-8') for obj in decoded_objects]
            return "\n".join(results)
        
        except Exception as e:
            return f"Error scanning image: {e}"