# conda activate twitter_env
# pip freeze > requirements.txt
# flask run

from dotenv import load_dotenv
load_dotenv()

from app import app

if __name__=='__main__':
    app.run(host='0.0.0.0', port=3000)
