import os
from django.core.exceptions import ValidationError
from PIL import Image

def validate_image_file(file_obj):
    """
    Validates that the uploaded file is a valid image of allowed types.
    Checks both file extension and actual content using Pillow.
    Allowed: JPEG, PNG, WebP, AVIF (no GIF)
    """
    if not file_obj:
        return

    # 1. Check File Extension
    ext = os.path.splitext(file_obj.name)[1].lower()
    allowed_extensions = [
        '.jpg', '.jpeg', '.jpe', '.jfif', 
        '.png', 
        '.webp', 
        '.avif', '.avifs'
    ]
    
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Unsupported file extension: {ext}."
        )

    # 2. Check Actual File Content
    try:
        file_obj.seek(0)
        img = Image.open(file_obj)
        img.verify()
        
        # Reject GIF files even if renamed
        if img.format == 'GIF':
            raise ValidationError(
                "GIF files are not allowed, even if renamed ^^"
            )
        
        # Only allow specific formats
        allowed_formats = ['JPEG', 'PNG', 'WEBP', 'AVIF']
        if img.format not in allowed_formats:
            raise ValidationError(
                f"Invalid image format detected: {img.format}. Only JPEG, PNG, WebP, and AVIF are allowed."
            )
            
    except ValidationError:
        # Re-raise our custom validation errors
        raise
    except Exception as e:
        raise ValidationError(
            "Invalid or corrupted image file. Please upload a valid image."
        )
    finally:
        file_obj.seek(0)