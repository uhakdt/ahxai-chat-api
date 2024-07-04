def determine_content_type(filename):
    content_type = "application/octet-stream"

    if filename.endswith('.json'):
        content_type = 'application/json'
    elif filename.endswith('.pdf'):
        content_type = 'application/pdf'
    elif filename.endswith('.png'):
        content_type = 'image/png'
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif filename.endswith('.gif'):
        content_type = 'image/gif'
    elif filename.endswith('.bmp'):
        content_type = 'image/bmp'
    elif filename.endswith('.tiff') or filename.endswith('.tif'):
        content_type = 'image/tiff'
    elif filename.endswith('.webp'):
        content_type = 'image/webp'
    elif filename.endswith('.csv'):
        content_type = 'text/csv'
    
    return content_type
