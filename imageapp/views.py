from rest_framework import viewsets
from .models import Images
from .serializer import ImageSerializer, RegisterSerializer, LoginSerializer
from rest_framework.response import Response
from rest_framework import status
import requests
import os
import hashlib
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from requests.exceptions import RequestException
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.exceptions import APIException
from django.db import models

class LoginAPI(APIView):

    def post(self, request):
        data = request.data
        serializer = LoginSerializer(data=data)
        if not serializer.is_valid():
            return Response({
                'status': False,
                'message' : serializer.errors
            }, status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username = serializer.data['username'], password = serializer.data['password'])
        if not user:
            return Response({
                'status': False,
                'message': 'invalid credentials'
            }, status.HTTP_400_BAD_REQUEST)

        token,_ = Token.objects.get_or_create(user=user)

        return Response({'status': True, 'message': 'user login', 'token': str(token)}, status.HTTP_201_CREATED)

class RegisterAPI(APIView):
    def post(self, request):
        data = request.data
        serializer = RegisterSerializer(data = data)

        if not serializer.is_valid():
            return Response({
                'status': False,
                'message' : serializer.errors
            }, status.HTTP_400_BAD_REQUEST)
        
        serializer.save()

        return Response({'status': True, 'message': 'user created'}, status.HTTP_201_CREATED)

class ImageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = Images.objects.all()
    serializer_class = ImageSerializer
    lookup_field = 'url'

    def create(self, request, *args, **kwargs):
        image_urls = request.data.get('image_urls', [])

        # Ensure the media directory exists
        media_directory = os.path.join("media")
        os.makedirs(media_directory, exist_ok=True)
        for url in image_urls:
            # Check if the URL is already in the database
            if not Images.objects.filter(url=url).exists():
                try:
                    response = requests.get(url)
                    response.raise_for_status()

                    image_hash = hashlib.sha256(url.encode()).hexdigest()
                    imagename = f"image-{image_hash}.jpeg"
                    image_path = os.path.join(media_directory, imagename)

                    with open(image_path, 'wb') as f:
                        f.write(response.content)

                    # Create Image instance and save the URL to the database
                    Images.objects.create(url=url, imagename=imagename)

                except RequestException as e:
                    # Handle HTTP request errors
                    raise APIException(detail=f"Failed to download image from {url}")

                except IntegrityError as e:
                    # Handle database integrity error (ex: duplicate key violation)
                    raise APIException(detail="IntegrityError: Duplicate key or database integrity violation")

                except ValidationError as e:
                    # Handle URL validation error
                    raise APIException(detail="ValidationError: Invalid URL")

                except Exception as e:
                    # Handle other errors (e.g: file write errors)
                    raise APIException(detail="Error processing image")

        return Response(status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            url = request.query_params.get('url', None)
            if not url:
                return Response({'error': 'Missing URL parameter'}, status=400)
            if Images.objects.filter(url=url).exists():
                instance = get_object_or_404(Images, url=url)
                imagename = instance.imagename

                media_directory = os.path.join("media")
                image_path = os.path.join(media_directory, imagename)

                if not os.path.exists(image_path):
                    return Response({'error': 'Image not found in the media folder'}, status=404)

                with open(image_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='image/jpeg')
                    response['Content-Disposition'] = f'attachment; filename="{imagename}"'
                    return response
            else:
                return Response({'error': 'Image not downloaded and stored'}, status=404)
        
        except ValidationError as e:
            # Handle validation error (ex: invalid URL)
            return Response({'Validation error': str(e)}, status=400)

        except FileNotFoundError:
            # Handle file not found error
            return Response({'error': 'Image file not found in the media folder'}, status=404)

        except Exception as e:
            # Handle unexpected errors
            return Response({'error': 'An unexpected error occurred'}, status=500)
        
    def destroy(self, request, *args, **kwargs):
        url = request.query_params.get('url', None)
        if not url:
            return Response({'error': 'Missing URL parameter'}, status=400)
        try:
            if Images.objects.filter(url=url).exists():
                instance = get_object_or_404(Images, url=url)
                imagename = instance.imagename

                media_directory = os.path.join("media")
                image_path = os.path.join(media_directory, imagename)

                if not os.path.exists(image_path):
                    return Response({'error': 'Image not found in the media folder'}, status=404)

                # Delete the instance from the database
                self.perform_destroy(instance)

                # Delete the image file from the media folder
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                return Response({'error': 'Image not downloaded and stored'}, status=404)
        
        except models.ProtectedError:
            # Handle protected error (ex: if there are related objects that prevent deletion)
            return Response({'error': 'Cannot delete image due to related objects'}, status=400)

        except FileNotFoundError:
            # Handle file not found error
            return Response({'error': 'Image file not found in the media folder'}, status=404)

        except PermissionError:
            # Handle permission error (ex: if the process has no permission to delete the file)
            return Response({'error': 'Permission error during deletion'}, status=500)

        except OSError as e:
            # Handle OS error (ex: if the file cannot be removed)
            return Response({'error': f'OS error during deletion: {str(e)}'}, status=500)

        except Exception as e:
            # Handle unexpected errors
            return Response({'error': 'An unexpected error occurred during deletion'}, status=500)

        return Response(status=204)
