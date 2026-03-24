import os
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.advideo import AdVideo

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

token      = os.getenv("META_ACCESS_TOKEN")
account_id = os.getenv("META_ACCOUNT_ID")

FacebookAdsApi.init(access_token=token)

filepath  = "/Users/alexrangelalves/Downloads/11-_teste_SBC.mp4"
videoname = "11-_teste_SBC"

print(f"Iniciando upload: {filepath}")
print(f"Conta: act_{account_id}")

video = AdVideo(parent_id=f"act_{account_id}")
video[AdVideo.Field.filepath] = filepath
video[AdVideo.Field.name]     = videoname

video.remote_create()

video_id = video[AdVideo.Field.id]
print(f"\n✅ Upload concluído com sucesso!")
print(f"   Nome:     {videoname}")
print(f"   Video ID: {video_id}")
print(f"\nUse esse ID para criar criativos: {video_id}")
