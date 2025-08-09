import requests
import base64

FACEPP_API_KEY = "kqCUSnE5vTeyhkaIzdL8xhS7W_izaLwR"
FACEPP_API_SECRET = "pmaqqyKpURdqHljXcOpWUuW10M1iN8HV"

FACEPP_DETECT_URL = "https://api-us.faceplusplus.com/facepp/v3/detect"
FACEPP_COMPARE_URL = "https://api-us.faceplusplus.com/facepp/v3/compare"
FACEPP_FACESET_CREATE_URL = "https://api-us.faceplusplus.com/facepp/v3/faceset/create"
FACEPP_FACESET_ADD_URL = "https://api-us.faceplusplus.com/facepp/v3/faceset/addface"
FACEPP_FACESET_REMOVE_URL = "https://api-us.faceplusplus.com/facepp/v3/faceset/removeface"
FACEPP_FACESET_GETDETAIL_URL = "https://api-us.faceplusplus.com/facepp/v3/faceset/getdetail"
FACEPP_FACESET_SEARCH_URL = "https://api-us.faceplusplus.com/facepp/v3/search"

# Dummy FaceSet token for demo, replace with your own after creating a FaceSet
FACEPP_FACESET_TOKEN = "YOUR_FACEPP_FACESET_TOKEN"


def detect_face_token_from_url(image_url):
    """Detect face and return face_token from an image URL."""
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET,
        'image_url': image_url
    }
    response = requests.post(FACEPP_DETECT_URL, data=data)
    result = response.json()
    if 'faces' in result and len(result['faces']) > 0:
        return result['faces'][0]['face_token']
    return None

def detect_face_token_from_base64(image_base64):
    """Detect face and return face_token from a base64 image string."""
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET,
        'image_base64': image_base64
    }
    response = requests.post(FACEPP_DETECT_URL, data=data)
    result = response.json()
    if 'faces' in result and len(result['faces']) > 0:
        return result['faces'][0]['face_token']
    return None


def detect_face_token_from_file(image_path):
    """Detect face and return face_token from an image file."""
    files = {'image_file': open(image_path, 'rb')}
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET
    }
    response = requests.post(FACEPP_DETECT_URL, files=files, data=data)
    result = response.json()
    if 'faces' in result and len(result['faces']) > 0:
        return result['faces'][0]['face_token']
    return None


def compare_face_tokens(face_token1, face_token2):
    """Compare two face_tokens and return the confidence score."""
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET,
        'face_token1': face_token1,
        'face_token2': face_token2
    }
    response = requests.post(FACEPP_COMPARE_URL, data=data)
    return response.json()


def create_faceset(outer_id=None):
    """Create a new FaceSet and return its token."""
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET,
    }
    if outer_id:
        data['outer_id'] = outer_id
    response = requests.post(FACEPP_FACESET_CREATE_URL, data=data)
    return response.json()


def add_face_to_faceset(face_token, faceset_token=FACEPP_FACESET_TOKEN):
    """Add a detected face to the FaceSet."""
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET,
        'faceset_token': faceset_token,
        'face_tokens': face_token
    }
    response = requests.post(FACEPP_FACESET_ADD_URL, data=data)
    return response.json()


def remove_face_from_faceset(face_token, faceset_token=FACEPP_FACESET_TOKEN):
    """Remove a face from the FaceSet."""
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET,
        'faceset_token': faceset_token,
        'face_tokens': face_token
    }
    response = requests.post(FACEPP_FACESET_REMOVE_URL, data=data)
    return response.json()


def get_faceset_detail(faceset_token=FACEPP_FACESET_TOKEN):
    """Get details of the FaceSet."""
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET,
        'faceset_token': faceset_token
    }
    response = requests.post(FACEPP_FACESET_GETDETAIL_URL, data=data)
    return response.json()


def search_face(image_base64, faceset_token=FACEPP_FACESET_TOKEN):
    """Search for a face in the FaceSet using Face++ API."""
    data = {
        'api_key': FACEPP_API_KEY,
        'api_secret': FACEPP_API_SECRET,
        'image_base64': image_base64,
        'faceset_token': faceset_token
    }
    response = requests.post(FACEPP_FACESET_SEARCH_URL, data=data)
    return response.json()
