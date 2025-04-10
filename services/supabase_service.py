from supabase import create_client
import os

url = "https://hagfxtawcqlejisrlato.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhhZ2Z4dGF3Y3FsZWp"

supabase = create_client(url, key)

def upload_file_to_supabase(file, filename):
    bucket_name = "enrollment-upload"
    response = supabase.storage.from_(bucket_name).upload(filename, file, {"content-type": file.content_type})
    if response.get("error"):
        raise Exception(response["error"]["message"])
    return supabase.storage.from_(bucket_name).get_public_url(filename)
