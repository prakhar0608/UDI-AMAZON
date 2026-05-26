from supabase_client import supabase

response = supabase.table("profiles").select("*").execute()

print(response.data)