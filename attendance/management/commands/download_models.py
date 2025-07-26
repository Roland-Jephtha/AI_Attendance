from django.core.management.base import BaseCommand
import os
import requests
from pathlib import Path


class Command(BaseCommand):
    help = 'Download DeepFace models manually to avoid timeout issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            default='VGG-Face',
            help='Model to download (VGG-Face, Facenet, OpenFace, DeepFace)',
        )

    def handle(self, *args, **options):
        model_name = options['model']
        self.stdout.write(f'Downloading and initializing {model_name} model...')

        try:
            # Import DeepFace and preload model
            from deepface import DeepFace
            from deepface.basemodels import VGGFace
            import numpy as np

            self.stdout.write('Ensuring weights directory exists...')

            # Ensure weights directory exists
            from pathlib import Path
            weights_dir = Path.home() / '.deepface' / 'weights'
            weights_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(f'Weights directory: {weights_dir}')

            # Create a dummy image to force model loading
            dummy_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

            self.stdout.write('Preloading VGG-Face model...')

            # Preload the model
            try:
                preloaded_model = VGGFace.loadModel()
                self.stdout.write(
                    self.style.SUCCESS('✅ VGG-Face model preloaded successfully!')
                )

                # Test with dummy image using preloaded model
                embedding = DeepFace.represent(
                    img_path=dummy_image,
                    model_name=model_name,
                    detector_backend='opencv',
                    enforce_detection=False
                )
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {model_name} model tested successfully with preloaded model!')
                )

            except Exception as model_error:
                self.stdout.write(
                    self.style.WARNING(f'Model preloading failed: {str(model_error)}')
                )
                self.stdout.write('Trying standard initialization...')

                # Fallback to standard initialization
                try:
                    embedding = DeepFace.represent(
                        img_path=dummy_image,
                        model_name=model_name,
                        detector_backend='opencv',
                        enforce_detection=False
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {model_name} model initialized successfully!')
                    )
                except Exception as fallback_error:
                    self.stdout.write(
                        self.style.WARNING(f'Standard initialization failed: {str(fallback_error)}')
                    )
                    self.stdout.write('Trying manual download...')
                    self.download_models_manually()
                
        except ImportError:
            self.stdout.write(
                self.style.ERROR('DeepFace not installed. Run: pip install deepface')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error downloading models: {str(e)}')
            )
            self.stdout.write('\nTrying manual download...')
            self.download_models_manually()

    def download_models_manually(self):
        """Manually download model files"""
        self.stdout.write('Attempting manual model download...')
        
        # Get the home directory for DeepFace models
        home_dir = Path.home()
        deepface_dir = home_dir / '.deepface' / 'weights'
        deepface_dir.mkdir(parents=True, exist_ok=True)
        
        # Model URLs (these might change, check DeepFace GitHub for updates)
        models = {
            'vgg_face_weights.h5': 'https://github.com/serengil/deepface_models/releases/download/v1.0/vgg_face_weights.h5',
            'facenet_weights.h5': 'https://github.com/serengil/deepface_models/releases/download/v1.0/facenet_weights.h5',
            'openface_weights.h5': 'https://github.com/serengil/deepface_models/releases/download/v1.0/openface_weights.h5',
        }
        
        for filename, url in models.items():
            file_path = deepface_dir / filename
            
            if file_path.exists():
                self.stdout.write(f'✅ {filename} already exists')
                continue
                
            try:
                self.stdout.write(f'Downloading {filename}...')
                
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.stdout.write(f'✅ Downloaded {filename}')
                
            except requests.exceptions.Timeout:
                self.stdout.write(f'❌ Timeout downloading {filename}')
            except Exception as e:
                self.stdout.write(f'❌ Error downloading {filename}: {str(e)}')
        
        self.stdout.write('\nManual download completed. Try running the face enrollment again.')
        self.stdout.write('\nIf issues persist, you can:')
        self.stdout.write('1. Use a different internet connection')
        self.stdout.write('2. Download models manually from: https://github.com/serengil/deepface_models/releases')
        self.stdout.write('3. Use a simpler face recognition model')
