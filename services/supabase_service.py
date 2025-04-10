from supabase import create_client
import os

url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWp"

supabase = create_client(url, key)

def upload_file_to_supabase(file_obj, path: str) -> str:
    """
    Uploads a file object to Supabase storage and returns the public URL.
    """
    file_bytes = file_obj.read()

    # Upload to the 'student-documents' bucket
    result = supabase.storage.from_('enrollment-uploads').upload(path, file_bytes, {"content-type": "application/pdf"})

    if 'error' in result:
        raise Exception(result['error'])

    # Return public URL
    public_url = supabase.storage.from_('enrollment-uploads').get_public_url(path)
    return public_url