import requests





FACEPP_API_KEY = "kqCUSnE5vTeyhkaIzdL8xhS7W_izaLwR"
FACEPP_API_SECRET = "pmaqqyKpURdqHljXcOpWUuW10M1iN8HV"


url = "https://api-us.faceplusplus.com/facepp/v3/detect"
data = {
    "api_key": FACEPP_API_KEY,
    "api_secret": FACEPP_API_SECRET,
    "image_url": "https://static.djangoproject.com/img/logos/django-logo-negative.1d528e2cb5fb.png"
}
response = requests.post(url, data=data)
print(response.json())