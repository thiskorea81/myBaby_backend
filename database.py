from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 환경 변수 로드

# MongoDB 연결 설정
mongo_client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))
db = mongo_client.baby_growth
users_collection = db.users
records_collection = db.records
